"""Exercise real yt-dlp HTTP downloading with a controlled in-memory transport."""
import io
from app.services import media
from yt_dlp import YoutubeDL
from yt_dlp.networking.common import RequestHandler, Response, Features

class FixtureRH(RequestHandler):
    _SUPPORTED_URL_SCHEMES=('https',)
    _SUPPORTED_PROXY_SCHEMES=None
    _SUPPORTED_FEATURES=(Features.NO_PROXY, Features.ALL_PROXY)
    def _send(self,request):
        payload=b'\x00\x00\x00\x18ftypmp42'+b'video-fixture'*1024
        return Response(io.BytesIO(payload),url=request.url,headers={'Content-Length':str(len(payload)),'Content-Type':'video/mp4'},status=200)

class FixtureYDL(media.SafeYDL):
    def build_request_director(self,handlers,preferences=None):
        return YoutubeDL.build_request_director(self,[FixtureRH],[])

def test_real_downloader_progress_and_output(monkeypatch,tmp_path):
    monkeypatch.setattr(media,'SafeYDL',FixtureYDL)
    monkeypatch.setattr(media,'validate_remote',lambda *a:None)
    events=[]
    media.download('https://video.twimg.com/controlled-fixture.mp4',tmp_path,events.append,200000)
    path=tmp_path/'video.mp4'
    assert path.is_file() and path.read_bytes().startswith(b'\x00\x00\x00\x18ftypmp42')
    assert any(e['status']=='downloading' and e['downloaded_bytes']>0 for e in events)
    assert events[-1]['status']=='finished' and events[-1]['downloaded_bytes']==path.stat().st_size
