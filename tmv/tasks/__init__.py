from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    celery = Celery(
        app.import_name,
        # backend=app.config["CELERY_RESULT_BACKEND"],
        backend="db+" + app.config["SQLALCHEMY_DATABASE_URI"],
        broker=app.config["CELERY_BROKER_URL"],
        include=["tasks.jira",],
    )

    celery.conf.beat_schedule = {
        "sync-projects-every-1-hour": {
            "task": "tasks.jira.sync_assigned_projects",
            "schedule": crontab(minute="0", hour="*"),
        }
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
