import ipaddress
import re
import socket
from urllib.parse import urlsplit
from urllib.request import BaseHandler

POST = re.compile(r'^/(?:[A-Za-z0-9_]{1,15}/status|i/status|i/web/status)/(\d{1,25})/?$')
POST_HOSTS = {'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com', 'mobile.twitter.com'}
NETWORK_HOSTS = POST_HOSTS | {'api.x.com', 'api.twitter.com', 'syndication.twitter.com', 'cdn.syndication.twimg.com', 'video.twimg.com', 'pbs.twimg.com', 'abs.twimg.com'}

def normalize_url(value: str) -> str:
    try:
        u = urlsplit(value.strip())
        match = POST.fullmatch(u.path)
        if u.scheme != 'https' or u.hostname not in POST_HOSTS or u.username or u.password or u.port not in (None, 443) or not match:
            raise ValueError()
        return f'https://x.com/i/status/{match[1]}'
    except (ValueError, AttributeError):
        raise ValueError('Paste a valid HTTPS X or Twitter post link.') from None

def validate_remote(url: str, resolve=True):
    try:
        u = urlsplit(url)
        if u.scheme != 'https' or u.hostname not in NETWORK_HOSTS or u.username or u.password or u.port not in (None, 443):
            raise ValueError('Blocked media destination')
        if resolve:
            addresses = socket.getaddrinfo(u.hostname, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise ValueError('Blocked non-public destination')
    except (OSError, ValueError) as exc:
        raise ValueError('Media destination is not permitted or could not be resolved') from exc

class DestinationGuard(BaseHandler):
    # Runs for original requests AND each redirect before any connection is made.
    handler_order = 100
    def https_request(self, request):
        validate_remote(request.full_url)
        return request
    def http_request(self, request):
        raise ValueError('Insecure media request blocked')
