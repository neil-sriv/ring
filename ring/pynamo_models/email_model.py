from ring.pynamo_models.base_model import BaseModel
from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute


class ScheduleModel(BaseModel):
    class Meta:
        table_name = "schedule"

    group_id = UnicodeAttribute(hash_key=True)
    scheduled_datetime = UTCDateTimeAttribute()
    sent = BooleanAttribute(default=False)
