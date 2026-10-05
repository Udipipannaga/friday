"""Explicit test-only worker. Never use with a real account database."""
import os
import time
from friday import execution, retrieval
from tests.test_workflows import TestModel

assert os.environ.get('FRIDAY_E2E_FIXTURES') == '1', 'Explicit fixture opt-in required'
assert 'e2e' in os.environ.get('FRIDAY_DATABASE_URL', ''), 'Use an isolated e2e database'
while True:
    for job_id in execution.pending_ids():
        execution.run_job(job_id, provider=TestModel(), search=lambda q:['https://example.org/research'],
            fetch=lambda u: retrieval.Page(u,'Fixture source','A durable research workflow stores evidence in the database. ' * 4))
    time.sleep(.2)
