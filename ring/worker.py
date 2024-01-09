import os

from celery import Celery
import datetime
from celery.schedules import crontab

from ring.pynamo_models.email_model import ScheduleModel
from ring.email_util import email_group

celery = Celery(
    "celery",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis"),
)
# print(f"broker url {celery.conf.broker_url}")
# celery.conf.accept_content = ["pickle", "json", "msgpack", "yaml"]
# celery.conf.worker_send_task_events = True


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # sender.add_periodic_task(10.0, hello_task.s(), name="add every 10")
    sender.add_periodic_task(
        crontab(hour="*/1"), poll_schedule_task.s(), name="poll_schedule"
    )


@celery.task(name="hello")
def hello_task():
    return "Hello World! - Celery"


@celery.task(name="poll_schedule")
def poll_schedule_task():
    table_scan = ScheduleModel.scan()
    possible_groups = set()
    for schedule_item in table_scan:
        if (not schedule_item.sent) and (
            datetime.datetime.now(datetime.UTC) - schedule_item.scheduled_datetime
        ) <= datetime.timedelta(hours=1):
            possible_groups.add(schedule_item.group_id)
    for group_id in possible_groups:
        # email_group(group_id)
        pass
    return {
        "status": "success",
        "message": f"Group ids emailed: {possible_groups}",
        "task_name": "poll_schedule",
    }


# if __name__ == "__main__":
# celery.start()
