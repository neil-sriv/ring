import os

from celery import Celery

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
    sender.add_periodic_task(10.0, hello_task.s(), name="add every 10")


@celery.task(name="hello")
def hello_task():
    return "Hello World! - Celery"


# if __name__ == "__main__":
# celery.start()
