from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    database: str = "MAGMUTUAL_MFQ_APP"
    schema: str = "PORTAL"
    form_key: str = "MFQ_V1"
    default_user_id: str = "U1"


CONFIG = AppConfig()