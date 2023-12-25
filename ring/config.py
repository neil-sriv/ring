import os
from dotenv import load_dotenv


class RingConfig:
    def __init__(self) -> None:
        self.dynamo_db_host = f"http://{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}"
        self.envrionment = os.getenv("ENVIRONMENT")


def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()
