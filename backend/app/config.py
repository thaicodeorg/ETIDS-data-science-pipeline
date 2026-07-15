from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(default="postgresql+psycopg2://manufacturing:manufacturing@postgres:5432/manufacturing_dw", alias="DATABASE_URL")
    data_zip_path: Path = Field(default=Path("/app/data/seed/etids_manufacturing_synthetic_dataset_v1.zip"), alias="DATA_ZIP_PATH")
    data_extract_dir: Path = Field(default=Path("/app/data/seed"), alias="DATA_EXTRACT_DIR")
    sensor_row_limit: int = Field(default=200_000, alias="SENSOR_ROW_LIMIT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def dataset_root(self) -> Path:
        return self.data_extract_dir / "etids_manufacturing_synthetic_dataset_v1"

    model_config = {"populate_by_name": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()
