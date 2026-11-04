from redis import Redis
from rq import Queue

from app.config import settings

JOB_TIMEOUT_SECONDS = 300  # Above the sandbox's own limit, so a stuck run still gets recorded as a failure.


def enqueue(submission_id: int) -> None:
    queue = Queue("submissions", connection=Redis.from_url(settings.redis_url))
    queue.enqueue("app.worker.judge_submission", submission_id, job_timeout=JOB_TIMEOUT_SECONDS, result_ttl=0)
