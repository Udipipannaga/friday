import socket
import pytest
from friday import retrieval


@pytest.mark.parametrize('url', ['http://example.com','file:///etc/passwd','https://user:pass@example.com','https://example.com:444','https://example.com/\r\nX:bad','https://example.com\\@127.0.0.1'])
def test_invalid_url_blocked(url):
    with pytest.raises(retrieval.RetrievalError):
        retrieval.resolve_public(url)


@pytest.mark.parametrize('ip',['127.0.0.1','10.1.1.1','169.254.169.254','192.168.1.1','172.16.0.1','0.0.0.0','::1','fe80::1','fc00::1','::ffff:127.0.0.1','224.0.0.1'])
def test_private_dns_blocked(monkeypatch, ip):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',(ip,443))])
    with pytest.raises(retrieval.RetrievalError):
        retrieval.resolve_public('https://attacker.example')


def test_mixed_public_private_dns_blocked(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('127.0.0.1',443))])
    with pytest.raises(retrieval.RetrievalError):
        retrieval.resolve_public('https://attacker.example')


def test_redirect_to_private_network_blocked(monkeypatch):
    def dns(host,*args,**kwargs):
        return [(2,1,6,'',('127.0.0.1' if host == 'localhost' else '8.8.8.8',443))]
    monkeypatch.setattr(socket,'getaddrinfo',dns)
    class Redirect:
        status = 302
        def getheader(self, name, default=''): return 'https://localhost/secrets'
    class Connection:
        def __init__(self,*args): pass
        def request(self,*args,**kwargs): pass
        def getresponse(self): return Redirect()
        def close(self): pass
    monkeypatch.setattr(retrieval,'PinnedHTTPS',Connection)
    with pytest.raises(retrieval.RetrievalError, match='Private'):
        retrieval.fetch_page('https://example.org')
