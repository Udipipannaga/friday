import os
import subprocess
import sys
from sqlalchemy import select
from friday import db


def test_real_process_crash_then_checkpoint_recovery(client):
    jid = client.post('/api/projects', json={'text':'Recover a research project','request_key':db.uid()}).json()['id']
    env = {**os.environ, 'FRIDAY_DATABASE_URL':str(db.engine.url), 'FRIDAY_API_KEY':'fixture', 'FRIDAY_MODEL':'fixture'}
    crash = '''
import os
from friday import db, execution
job_id = os.environ['TEST_JOB_ID']
token = execution.claim(job_id)
with db.Session.begin() as s:
    j = s.get(db.Job,job_id)
    j.stage = 'fetch'
    j.lease_until = 0
    j.checkpoint = {'urls':['https://example.org/research']}
    s.add(db.Source(job_id=job_id,position=1,url='https://example.org/research',title='Saved before crash',text='A durable research workflow survives restarts.'))
os._exit(23)
'''
    env['TEST_JOB_ID'] = jid
    failed = subprocess.run([sys.executable,'-c',crash],env=env,timeout=15)
    assert failed.returncode == 23
    resume = '''
import os
from friday import execution
from tests.test_workflows import TestModel
def forbidden(*a): raise AssertionError('Completed source fetched again')
execution.run_job(os.environ['TEST_JOB_ID'],provider=TestModel(),search=forbidden,fetch=forbidden)
'''
    result = subprocess.run([sys.executable,'-c',resume],env=env,timeout=15)
    assert result.returncode == 0
    with db.Session() as s:
        assert s.get(db.Job,jid).status == 'succeeded'
        assert len(list(s.scalars(select(db.Source).where(db.Source.job_id==jid)))) == 1
