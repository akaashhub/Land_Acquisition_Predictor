"""Preprocessing pipeline shared by training and inference."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import joblib
from pathlib import Path

from app.ml.feature_engineering import get_feature_matrix, FEATURE_COLUMNS


class Preprocessor:
    def __init__(self):
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.feature_names: list[str] = []
        self.fitted = False

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        X = get_feature_matrix(df)
        self.feature_names = list(X.columns)
        self.imputer.fit(X)
        X_imp = self.imputer.transform(X)
        self.scaler.fit(X_imp)
        self.fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("Preprocessor not fitted")
        X = get_feature_matrix(df)
        # Align columns
        for c in self.feature_names:
            if c not in X.columns:
                X[c] = 0
        X = X[self.feature_names]
        X_imp = self.imputer.transform(X)
        return self.scaler.transform(X_imp)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        return self.fit(df).transform(df)

    def save(self, path: str | Path):
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> "Preprocessor":
        return joblib.load(path)
