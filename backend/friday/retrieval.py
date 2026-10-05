"""Bounded HTTPS retrieval with pinned public IPs and TLS hostname verification."""
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urlsplit, urljoin
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
from .config import settings


class RetrievalError(Exception):
    pass


def resolve_public(url):
    if len(url) > 2048 or any(ord(c) < 33 for c in url) or '\\' in url:
        raise RetrievalError('Invalid source URL.')
    try:
        parts = urlsplit(url)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.port not in (None, 443):
            raise RetrievalError('Only public HTTPS URLs on port 443 are allowed.')
        host = parts.hostname.encode('idna').decode('ascii')
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        ips = list(dict.fromkeys(a[4][0] for a in addresses))
        if not ips or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast for ip in ips):
            raise RetrievalError('Private, reserved, or internal network address blocked.')
        return parts, host, ips[0]
    except (ValueError, UnicodeError, OSError) as exc:
        raise RetrievalError('Source address could not be safely resolved.') from exc


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, ip, timeout):
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.ip = ip

    def connect(self):
        # No second hostname lookup: connect only to the validated literal address.
        raw = socket.create_connection((self.ip, 443), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


@dataclass
class Page:
    url: str
    title: str
    text: str


def fetch_page(url):
    started = time.monotonic()
    for _ in range(4):
        parts, host, ip = resolve_public(url)
        conn = PinnedHTTPS(host, ip, 8)
        try:
            path = parts.path or '/'
            if parts.query:
                path += '?' + parts.query
            conn.request('GET', path, headers={'User-Agent': 'FRIDAYResearch/0.1', 'Accept': 'text/html,text/plain', 'Accept-Encoding': 'identity'})
            res = conn.getresponse()
            if res.status in (301, 302, 303, 307, 308):
                url = urljoin(url, res.getheader('Location', ''))
                continue
            if res.status != 200:
                raise RetrievalError(f'Source returned HTTP {res.status}.')
            if res.getheader('Content-Encoding', 'identity') != 'identity':
                raise RetrievalError('Compressed source not accepted.')
            media = res.getheader('Content-Type', '').split(';')[0].lower()
            if media not in ('text/html', 'text/plain', 'application/xhtml+xml'):
                raise RetrievalError('Source is not an HTML or text page.')
            buf = bytearray()
            while True:
                if time.monotonic() - started > 25:
                    raise RetrievalError('Source retrieval timed out.')
                part = res.read(16384)
                if not part:
                    break
                buf.extend(part)
                if len(buf) > 1_000_000:
                    raise RetrievalError('Source exceeded the 1 MB limit.')
            soup = BeautifulSoup(buf.decode('utf-8', errors='replace'), 'html.parser')
            title = soup.title.get_text(' ', strip=True) if soup.title else host
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                element.decompose()
            text = ' '.join(soup.get_text(' ', strip=True).split())[:12000]
            if len(text) < 100:
                raise RetrievalError('Source contains insufficient extractable text.')
            return Page(url, title[:300], text)
        except (OSError, http.client.HTTPException) as exc:
            raise RetrievalError('Source download failed.') from exc
        finally:
            conn.close()
    raise RetrievalError('Source exceeded the redirect limit.')


def search_web(query):
    if not settings.search_key:
        raise RetrievalError('Configure FRIDAY_SEARCH_KEY on the server for Brave Search.')
    try:
        with httpx.Client(timeout=20, trust_env=False) as client:
            res = client.get('https://api.search.brave.com/res/v1/web/search',
                headers={'X-Subscription-Token': settings.search_key, 'Accept': 'application/json'},
                params={'q': ' '.join(query[:600].split()[:75]), 'count': 5})
        if res.status_code != 200:
            raise RetrievalError(f'Search provider returned HTTP {res.status}.')
        results = res.json().get('web', {}).get('results', [])
        urls = list(dict.fromkeys(r['url'] for r in results if isinstance(r.get('url'), str)))[:5]
        if not urls:
            raise RetrievalError('Search returned no sources.')
        return urls
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise RetrievalError('Search service failed.') from exc
