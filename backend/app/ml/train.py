"""Train classifier + regressor for delay prediction."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, mean_absolute_error,
    mean_squared_error, r2_score,
)
import joblib

from app.ml.generate_dataset import generate_dataset
from app.ml.preprocessing import Preprocessor
from app.ml.feature_engineering import FEATURE_COLUMNS

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def train_all(n_samples: int = 3000, seed: int = 42):
    print("=" * 60)
    print("SIH26017 — Training Pipeline (Synthetic Demonstration Data)")
    print("=" * 60)

    df = generate_dataset(n_samples, seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / "sample_dataset.csv"
    df.to_csv(csv_path, index=False)
    print(f"Dataset: {len(df)} rows → {csv_path}")
    print(f"Delayed rate: {df['delayed'].mean():.2%}")

    y_cls = df["delayed"].astype(int).values
    y_reg = df["delay_days"].astype(float).values

    preprocessor = Preprocessor()
    X = preprocessor.fit_transform(df)
    print(f"Features: {len(preprocessor.feature_names)}")

    X_train, X_test, y_cls_train, y_cls_test, y_reg_train, y_reg_test = train_test_split(
        X, y_cls, y_reg, test_size=0.2, random_state=seed, stratify=y_cls
    )

    # --- Classifiers ---
    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed),
        "RandomForest": RandomForestClassifier(
            n_estimators=150, max_depth=12, min_samples_leaf=5,
            class_weight="balanced", random_state=seed, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.08, random_state=seed
        ),
    }

    best_name, best_model, best_recall = None, None, -1
    results = {}

    for name, model in candidates.items():
        model.fit(X_train, y_cls_train)
        pred = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else pred.astype(float)
        metrics = {
            "accuracy": float(accuracy_score(y_cls_test, pred)),
            "precision": float(precision_score(y_cls_test, pred, zero_division=0)),
            "recall": float(recall_score(y_cls_test, pred, zero_division=0)),
            "f1": float(f1_score(y_cls_test, pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_cls_test, proba)) if len(np.unique(y_cls_test)) > 1 else 0.0,
            "confusion_matrix": confusion_matrix(y_cls_test, pred).tolist(),
        }
        results[name] = metrics
        print(f"\n{name}: Acc={metrics['accuracy']:.3f} Prec={metrics['precision']:.3f} "
              f"Rec={metrics['recall']:.3f} F1={metrics['f1']:.3f} AUC={metrics['roc_auc']:.3f}")
        # Prefer recall for early-warning
        score = metrics["recall"] * 0.5 + metrics["f1"] * 0.3 + metrics["roc_auc"] * 0.2
        if score > best_recall:
            best_recall = score
            best_name = name
            best_model = model

    print(f"\nSelected classifier: {best_name} (recall-focused selection)")

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        fi = dict(zip(preprocessor.feature_names, best_model.feature_importances_.tolist()))
    elif hasattr(best_model, "coef_"):
        fi = dict(zip(preprocessor.feature_names, np.abs(best_model.coef_[0]).tolist()))
    else:
        fi = {}
    fi_sorted = dict(sorted(fi.items(), key=lambda x: -x[1])[:20])

    # --- Regressor ---
    reg_candidates = {
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=120, max_depth=12, min_samples_leaf=5, random_state=seed, n_jobs=-1
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=100, max_depth=5, learning_rate=0.08, random_state=seed
        ),
    }
    best_reg_name, best_reg, best_mae = None, None, 1e9
    reg_results = {}
    for name, model in reg_candidates.items():
        model.fit(X_train, y_reg_train)
        pred = model.predict(X_test)
        mae = float(mean_absolute_error(y_reg_test, pred))
        rmse = float(np.sqrt(mean_squared_error(y_reg_test, pred)))
        r2 = float(r2_score(y_reg_test, pred))
        reg_results[name] = {"mae": mae, "rmse": rmse, "r2": r2}
        print(f"{name}: MAE={mae:.2f} RMSE={rmse:.2f} R²={r2:.3f}")
        if mae < best_mae:
            best_mae = mae
            best_reg_name = name
            best_reg = model

    print(f"Selected regressor: {best_reg_name}")

    # Save
    clf_path = MODELS_DIR / "delay_classifier.joblib"
    reg_path = MODELS_DIR / "delay_regressor.joblib"
    prep_path = MODELS_DIR / "preprocessor.joblib"
    meta_path = MODELS_DIR / "metrics.json"

    joblib.dump(best_model, clf_path)
    joblib.dump(best_reg, reg_path)
    preprocessor.save(prep_path)

    meta = {
        "classifier": best_name,
        "classifier_metrics": results[best_name],
        "all_classifier_metrics": results,
        "regressor": best_reg_name,
        "regressor_metrics": reg_results[best_reg_name],
        "all_regressor_metrics": reg_results,
        "feature_importance": fi_sorted,
        "feature_names": preprocessor.feature_names,
        "training_size": len(df),
        "n_features": len(preprocessor.feature_names),
        "test_size": len(y_cls_test),
        "disclaimer": (
            "Model metrics are based on the synthetic demonstration dataset "
            "and should not be interpreted as production validation."
        ),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nSaved models → {MODELS_DIR}")
    return meta


if __name__ == "__main__":
    train_all()
