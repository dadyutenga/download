import http.client
import ipaddress
import socket
from urllib.request import ProxyHandler
from yt_dlp import YoutubeDL
from yt_dlp.networking._urllib import UrllibRH, HTTPHandler
from app.core.security import DestinationGuard, normalize_url, validate_remote

class QuietLogger:
    def debug(self, *_): pass
    def info(self, *_): pass
    def warning(self, *_): pass
    def error(self, *_): pass

def public_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, **kwargs):
    # Resolve once, reject private answers, and connect to that exact numeric IP.
    infos = socket.getaddrinfo(address[0], address[1], type=socket.SOCK_STREAM)
    if not infos or any(not ipaddress.ip_address(a[4][0]).is_global for a in infos):
        raise OSError('Non-public connection blocked')
    last = None
    for family, socktype, proto, _, target in infos:
        sock = socket.socket(family, socktype, proto)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT: sock.settimeout(timeout)
            if source_address: sock.bind(source_address)
            sock.connect(target)
            return sock
        except OSError as exc:
            last = exc
            sock.close()
    raise last or OSError('Connection failed')

class PinnedHTTPHandler(HTTPHandler):
    @staticmethod
    def _make_conn_class(base, req):
        # An administrator-supplied HTTPS proxy resolves remote destinations itself.
        # DestinationGuard still validates every destination and redirect locally.
        if req.has_proxy() or getattr(req, "_tunnel_host", None):
            return base
        class Connection(base):
            def connect(self):
                self._create_connection = public_connection
                return super().connect()
        return Connection

class GuardedRH(UrllibRH):
    RH_NAME = 'guarded'
    def _create_instance(self, proxies, cookiejar, legacy_ssl_support=None):
        opener = super()._create_instance(proxies, cookiejar, legacy_ssl_support)
        for handler in list(opener.handlers):
            if isinstance(handler, HTTPHandler):
                # Remove replaced handler from dispatch lists as well.
                for table in (opener.handle_open, opener.process_request, opener.process_response):
                    for methods in table.values():
                        if isinstance(methods, dict):
                            for chain in methods.values():
                                if handler in chain: chain.remove(handler)
                        elif handler in methods: methods.remove(handler)
                opener.handlers.remove(handler)
        opener.add_handler(PinnedHTTPHandler(context=self._make_sslcontext(legacy_ssl_support=legacy_ssl_support), source_address=self.source_address))
        opener.add_handler(DestinationGuard())
        return opener

class SafeYDL(YoutubeDL):
    def build_request_director(self, handlers, preferences=None):
        return super().build_request_director([GuardedRH], [])

def options():
    return dict(quiet=True, no_warnings=True, logger=QuietLogger(), noplaylist=True,
                socket_timeout=15, retries=2, fragment_retries=2,
                extract_flat=False, cachedir=False, allowed_extractors=['twitter'],
                hls_prefer_native=True, concurrent_fragment_downloads=1)

def extract(url: str):
    with SafeYDL(options()) as ydl:
        info = ydl.extract_info(normalize_url(url), download=False)
    if info and info.get('_type') == 'playlist':
        info = next((entry for entry in info.get('entries', []) if entry), None)
    if not info: raise ValueError('This post has no downloadable video.')
    formats = []
    for f in info.get('formats', []):
        # Progressive MP4 is portable on Android, has audio, and needs no remote FFmpeg input.
        if f.get('ext') != 'mp4' or f.get('vcodec') == 'none' or f.get('acodec') == 'none' or f.get('protocol') != 'https':
            continue
        validate_remote(f['url'])
        formats.append(f)
    if not formats: raise ValueError('No supported public MP4 video was found in this post.')
    formats.sort(key=lambda f: (f.get('height') or 0, f.get('tbr') or 0), reverse=True)
    choices = [{'id': 'best', 'label': 'Best available', 'height': formats[0].get('height')}]
    seen = set()
    for f in formats:
        height = f.get('height')
        if height and height not in seen:
            choices.append({'id': str(height), 'label': f'{height}p', 'height': height})
            seen.add(height)
    thumbnail = info.get('thumbnail')
    if thumbnail:
        try: validate_remote(thumbnail)
        except ValueError: thumbnail = None
    return {'title': str(info.get('title') or 'X video')[:240], 'duration': info.get('duration'),
            'thumbnail': thumbnail, 'qualities': choices}, formats

def download(url, target, progress, limit):
    opts = options() | {'outtmpl': str(target / 'video.%(ext)s'), 'format': 'best',
                        'max_filesize': limit, 'progress_hooks': [progress],
                        'overwrites': False, 'fixup': 'never', 'continuedl': False}
    # This is a server-held, validated progressive format, never a client URL.
    validate_remote(url)
    with SafeYDL(opts) as ydl:
        ydl.process_info({'id': 'video', 'title': 'X video', 'url': url, 'ext': 'mp4', 'protocol': 'https', 'format_id': 'selected', 'vcodec': 'h264', 'acodec': 'aac'})
