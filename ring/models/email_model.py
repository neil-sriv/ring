from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
)
from ring.fast import ring_config


class ScheduleModel(Model):
    class Meta:  # type: ignore
        host = ring_config.dynamo_db_host
        table_name = "schedule"
        region = "us-west-2"

    group_id = UnicodeAttribute(hash_key=True)
    scheduled_datetime = UnicodeAttribute()
