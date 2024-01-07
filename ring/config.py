import os
from dotenv import load_dotenv


class RingConfig:
    def __init__(self) -> None:
        self.environment = os.getenv("ENVIRONMENT")
        self.dynamo_db_host = f"http://{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}"


def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()
