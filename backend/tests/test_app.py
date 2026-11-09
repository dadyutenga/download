import socket
import time
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.core.security import normalize_url, validate_remote, DestinationGuard
from app.services import media
from app.workers.jobs import Manager, JobError
from app.main import create_app

@pytest.mark.parametrize('url',['http://x.com/a/status/123','https://x.com.evil.test/a/status/1','https://x.com@127.0.0.1/a/status/1','https://127.0.0.1/a/status/1','file:///etc/passwd','https://x.com:444/a/status/1','https://x.com/a/status/1/../../admin','https://x.com/','https://twitter.com/a/status/nope'])
def test_reject_urls(url):
    with pytest.raises(ValueError): normalize_url(url)
@pytest.mark.parametrize('host',['x.com','twitter.com','www.twitter.com','mobile.twitter.com'])
def test_normalize(host):
    assert normalize_url(f'https://{host}/NASA/status/123?s=20')=='https://x.com/i/status/123'
@pytest.mark.parametrize('ip',['127.0.0.1','10.0.0.1','169.254.169.254','::1','192.168.0.2'])
def test_private_dns(monkeypatch,ip):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443))])
    with pytest.raises(ValueError):validate_remote('https://video.twimg.com/video.mp4')
@pytest.mark.parametrize('url',['https://localhost/a','https://video.twimg.com.evil/a','file:///etc/passwd','http://video.twimg.com/a','https://video.twimg.com:444/a','https://user:pass@video.twimg.com/a'])
def test_network_allowlist(url):
    with pytest.raises(ValueError):validate_remote(url,resolve=False)
def test_redirect_guard():
    from urllib.request import Request
    with pytest.raises(ValueError):DestinationGuard().https_request(Request('https://127.0.0.1/secret'))
def test_pinned_connection_blocks_rebinding(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))])
    with pytest.raises(OSError):media.public_connection(('video.twimg.com',443))
def test_extract_filters_formats(monkeypatch):
    class Fake:
        def __init__(self,*a):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def extract_info(self,*a,**kw):
            fmt=lambda h,p:{'height':h,'url':'https://video.twimg.com/a.mp4','protocol':p,'ext':'mp4','vcodec':'h264','acodec':'aac'}
            return {'title':'Example','duration':3,'formats':[fmt(720,'https'),fmt(720,'https'),fmt(1080,'m3u8_native')]}
    monkeypatch.setattr(media,'SafeYDL',Fake);monkeypatch.setattr(media,'validate_remote',lambda *a:None)
    meta,formats=media.extract('https://x.com/a/status/1')
    assert [q['id'] for q in meta['qualities']]==['best','720'] and len(formats)==2

class FixtureManager(Manager):
    def run_process(self,target,args,job=None):
        if job:
            if 'fail' in job.title:raise JobError('Fixture download failure')
            if 'slow' in job.title:
                while not job.cancelled.wait(.01):pass
                raise JobError('Cancelled')
            (job.directory/'video.mp4').write_bytes(b'fixture-mp4')
            return
        return ({'title':'Test video','duration':2,'thumbnail':None,'qualities':[{'id':'best','label':'Best available','height':720}]},[{'url':'https://video.twimg.com/test.mp4','height':720}])
@pytest.fixture
def manager(tmp_path):
    m=FixtureManager(Settings(data_dir=tmp_path,disk_reserve=0,max_file_bytes=1024,ttl=10))
    yield m
    m.close()
def wait(job,state):
    end=time.monotonic()+3
    while job.state!=state and time.monotonic()<end:time.sleep(.01)
    assert job.state==state

def test_lifecycle_and_expiry(manager):
    a=manager.analyze('https://x.com/a/status/1');j=manager.create(a['reference'],'best');wait(j,'completed')
    assert j.file.read_bytes()==b'fixture-mp4' and j.snapshot()['percent']==100
    with pytest.raises(KeyError):manager.get(j.id,'incorrect')
    j.created-=11;manager.expire()
    assert not j.directory.exists()
    with pytest.raises(KeyError):manager.get(j.id,j.token)
def test_cancel(manager):
    a=manager.analyze('https://x.com/a/status/1');manager.analyses[a['reference']][1]['title']='slow'
    j=manager.create(a['reference'],'best');wait(j,'downloading');manager.cancel(j);manager.pool.shutdown(wait=True)
    assert j.state=='cancelled' and not j.directory.exists()
def test_failed_job(manager):
    a=manager.analyze('https://x.com/a/status/1');manager.analyses[a['reference']][1]['title']='fail'
    j=manager.create(a['reference'],'best');wait(j,'failed');assert j.error=='Fixture download failure'
def test_invalid_quality_and_reference(manager):
    with pytest.raises(KeyError):manager.create('missing','best')
    a=manager.analyze('https://x.com/a/status/1')
    with pytest.raises(ValueError):manager.create(a['reference'],'../../etc/passwd')
def test_api_workflow(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,disk_reserve=0,max_file_bytes=1024),FixtureManager)
    with TestClient(app) as c:
        assert c.get('/api/v1/health').status_code==200
        assert c.post('/api/v1/media/analyze',json={'url':'http://localhost'}).status_code==422
        a=c.post('/api/v1/media/analyze',json={'url':'https://x.com/a/status/1'}).json()
        r=c.post('/api/v1/downloads',json={'reference':a['reference'],'quality':'best'});assert r.status_code==202
        j=r.json();headers={'Authorization':f"Bearer {j['token']}"};path=f"/api/v1/downloads/{j['id']}"
        assert c.get(path).status_code==404
        wait(app.state.manager.jobs[j['id']],'completed')
        assert c.get(path,headers=headers).json()['status']=='completed'
        events=c.get(path+'/events',headers=headers);assert 'event: progress' in events.text and 'completed' in events.text
        f=c.get(path+'/file',headers=headers);assert f.content==b'fixture-mp4' and 'attachment' in f.headers['content-disposition']
        assert c.delete(path,headers=headers).status_code==204
        assert c.get(path+'/file',headers=headers).status_code==409
def test_path_escape_file_denied(tmp_path):
    app=create_app(Settings(data_dir=tmp_path/'jobs',disk_reserve=0,max_file_bytes=1024),FixtureManager)
    with TestClient(app) as c:
        a=app.state.manager.analyze('https://x.com/a/status/1');j=app.state.manager.create(a['reference'],'best');wait(j,'completed')
        outside=tmp_path/'secret';outside.write_text('secret');j.file.unlink();j.file.symlink_to(outside)
        assert c.get(f'/api/v1/downloads/{j.id}/file',headers={'Authorization':f'Bearer {j.token}'}).status_code==404
def test_rate_and_body_limit(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path,rate_limit=1),FixtureManager)) as c:
        assert c.post('/api/v1/media/analyze',content='x'*5000).status_code==413
        c.post('/api/v1/media/analyze',json={'url':'bad'})
        assert c.post('/api/v1/media/analyze',json={'url':'bad'}).status_code==429

def test_unknown_audio_codec_progressive_is_supported(monkeypatch):
    class Fake:
        def __init__(self,*a):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def extract_info(self,*a,**kw):return {'title':'X MP4','formats':[{'height':480,'url':'https://video.twimg.com/480.mp4','protocol':'https','ext':'mp4'}]}
    monkeypatch.setattr(media,'SafeYDL',Fake);monkeypatch.setattr(media,'validate_remote',lambda *a:None)
    meta,formats=media.extract('https://x.com/a/status/1')
    assert len(formats)==1 and meta['qualities'][1]['id']=='480'

def stalled_worker(channel):
    time.sleep(10)

def test_process_timeout_reaps_worker(tmp_path):
    import multiprocessing
    m=Manager(Settings(data_dir=tmp_path,timeout=1))
    try:
        with pytest.raises(JobError,match='timed out'):m.run_process(stalled_worker,())
        assert not multiprocessing.active_children()
    finally:m.close()
