"""
Application settings.

Phase 1 runs locally by default. The same settings object supports cloud
deployment by switching environment variables instead of changing business code.
"""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration for the Financial Intelligence Engine."""

    environment: str
    project_root: Path
    data_root: Path
    raw_data_dir: Path
    processed_data_dir: Path
    feature_store_dir: Path
    vector_store_dir: Path
    model_dir: Path
    reports_dir: Path
    database_url: str
    genai_provider: str
    genai_model: str
    openai_api_key: str
    sec_user_agent: str
    market_universe: str

    @property
    def is_cloud(self) -> bool:
        return self.environment.lower() in {"cloud", "prod", "production"}


def get_settings(project_root: Path | None = None) -> AppSettings:
    root = project_root or Path(__file__).resolve().parents[1]
    try:
        from dotenv import load_dotenv

        load_dotenv(root / ".env", override=False)
    except ImportError:
        pass

    data_root = Path(os.getenv("FIE_DATA_ROOT", root / "data"))

    return AppSettings(
        environment=os.getenv("FIE_ENV", "local"),
        project_root=root,
        data_root=data_root,
        raw_data_dir=Path(os.getenv("FIE_RAW_DATA_DIR", data_root / "raw")),
        processed_data_dir=Path(os.getenv("FIE_PROCESSED_DATA_DIR", data_root / "processed")),
        feature_store_dir=Path(os.getenv("FIE_FEATURE_STORE_DIR", data_root / "features")),
        vector_store_dir=Path(os.getenv("FIE_VECTOR_STORE_DIR", data_root / "vectors")),
        model_dir=Path(os.getenv("FIE_MODEL_DIR", root / "models")),
        reports_dir=Path(os.getenv("FIE_REPORTS_DIR", root / "reports")),
        database_url=os.getenv("FIE_DATABASE_URL", f"sqlite:///{data_root / 'phase1.sqlite'}"),
        genai_provider=os.getenv("FIE_GENAI_PROVIDER", "local"),
        genai_model=os.getenv("FIE_GENAI_MODEL", "gpt-5.4-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        sec_user_agent=os.getenv("FIE_SEC_USER_AGENT", ""),
        market_universe=os.getenv("FIE_MARKET_UNIVERSE", "us_equities"),
    )
