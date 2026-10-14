from celery import Celery
from .config import settings
from .execution import pending_ids, run_job
from .operating import run_due_weekly_notes

app = Celery('friday', broker=settings.redis_url)
app.conf.update(task_acks_late=True, task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1, task_ignore_result=True,
    task_soft_time_limit=650, task_time_limit=700,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        'recover-and-dispatch': {'task': 'friday.dispatch', 'schedule': 5.0},
        'owner-weekly-notes': {'task': 'friday.weekly-notes', 'schedule': 60.0},
    })


@app.task(name='friday.dispatch')
def dispatch():
    for job_id in pending_ids():
        execute.delay(job_id)


@app.task(name='friday.execute')
def execute(job_id):
    run_job(job_id)


@app.task(name='friday.weekly-notes')
def weekly_notes():
    model_ready = bool(settings.model and settings.provider in ('ollama', 'openai') and
        (settings.provider != 'openai' or settings.api_key))
    return run_due_weekly_notes(model_ready=model_ready)

