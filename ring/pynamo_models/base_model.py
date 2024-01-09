from pynamodb.models import Model
from ring.config import get_config


class BaseModel(Model):
    class Meta:  # type: ignore
        host = get_config().dynamo_db_host
        region = "us-west-2"
