from celery.signals import after_task_publish
from app import create_app
from tasks import make_celery


app = create_app()
celery = make_celery(app)


@after_task_publish.connect
def update_sent_state(sender=None, headers=None, **kwargs):
    # the task may not exist if sent using `send_task` which
    # sends tasks by name, so fall back to the default result backend
    # if that is the case.
    task = celery.tasks.get(sender)
    backend = task.backend if task else celery.backend

    backend.store_result(headers["id"], None, "SENT")
