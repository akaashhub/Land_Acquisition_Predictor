from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:////tmp/sih26017_land.db"
    SECRET_KEY: str = "sih26017-demo-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    MODEL_PATH: str = "app/ml/models/delay_classifier.joblib"
    REGRESSOR_PATH: str = "app/ml/models/delay_regressor.joblib"
    PREPROCESSOR_PATH: str = "app/ml/models/preprocessor.joblib"
    DEMO_MODE: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
