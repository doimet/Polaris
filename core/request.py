# -*-* coding:UTF-8
import _socket
import hashlib
import random
import socket
import httpx
from urllib.parse import urlparse, urljoin
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()


class RewriteString(str):
    def __new__(cls, value):
        return super().__new__(cls, value)

    def contains(self, value):
        if str(value) in self:
            return True
        else:
            return False


class DNSProxy:
    _rules, _host, old = [], None, _socket.getaddrinfo

    def __init__(self, rules, host):
        self.is_patch = False
        self.monkey_patch()
        self.rules = rules
        self.host = host

    def get_address_info(self):
        def wrapper(host, *args, **kwargs):
            if host in self.rules:
                host = self.host
            return self.old(host, *args, **kwargs)

        return wrapper

    def monkey_patch(self):
        if self.is_patch:
            return
        self.is_patch = True
        _socket.getaddrinfo = self.get_address_info()

    def remove_monkey_patch(self):
        if not self.is_patch:
            return
        self.is_patch = False
        _socket.getaddrinfo = self.old


class Request:
    """ 网络封装 """

    def __init__(self, target=None):
        self.target = target
        self.url_cache = {}
        self.current_url = ''
        self.headers = {
            'User-Agent': RandomUserAgent.get(),
            "Accept": "*/*",
            "Connection": "close"
        }
        self.client = httpx.Client(verify=False)
        self.async_client = httpx.AsyncClient(verify=False)
        # DNSProxy([self.resolve_name], self.resolve_host)

    def __del__(self):
        self.client.close()
        self.async_client.aclose()

    @property
    def resolve_name(self):
        return urlparse(self.current_url).netloc.split(":")[0]

    @property
    def resolve_host(self):
        name = urlparse(self.current_url).netloc.split(":")[0]
        try:
            host = socket.gethostbyname(name)
        except socket.gaierror:

            # Check if hostname resolves to IPv6 address only
            try:
                host = socket.gethostbyname(host, None, socket.AF_INET6)
            except socket.gaierror:
                raise Exception({"message": "Couldn't resolve DNS"})
        return host

    def request(self, method='get', url=None, path=None, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        if url in self.url_cache:
            return self.url_cache[url]
        self.current_url = url
        self.headers.update(kwargs.get('headers', {}))
        kwargs.update({'headers': self.headers})
        try:
            response = self.client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            response = self.client.request(
                method=method,
                url=url.replace('http://', 'https://'),
                *args,
                **kwargs
            )
        except Exception as e:
            raise Exception({"Error": e})
        self.url_cache[url] = response
        return self.decorate_response(response)

    async def async_http(self, method='get', url=None, path=None, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        if url in self.url_cache:
            return self.url_cache[url]
        self.current_url = url
        self.headers.update(kwargs.get('headers', {}))
        kwargs.update({'headers': self.headers})
        try:
            response = await self.async_client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            response = await self.async_client.request(
                method=method,
                url=url.replace('http://', 'https://'),
                *args,
                **kwargs
            )
        except Exception as e:
            raise Exception({"Error": e})
        self.url_cache[url] = response
        return self.decorate_response(response)

    @staticmethod
    def unit_convert(num):

        """ 单位换算 """

        base = 1024
        for x in ["B ", "KB", "MB", "GB"]:
            if base > num > -base:
                return "%3.0f%s" % (num, x)
            num /= base
        return "%3.0f %s" % (num, "TB")

    def decorate_response(self, response):
        response.encoding = response.apparent_encoding
        if "Content-Length" in dict(response.headers):
            content_length = int(response.headers.get("Content-Length"))
        else:
            content_length = len(response.content)

        response.md5 = hashlib.md5(response.content).hexdigest()
        response.length = self.unit_convert(content_length)
        response.body = response.text

        return response


class RandomProxy:
    """ 随机代理 """

    @staticmethod
    def get():
        proxy = ''
        return {'http': proxy, 'https': proxy}


class RandomUserAgent:
    """ 随机UA """

    @staticmethod
    def get():
        ua_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36 Edg/97.0.1072.69',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'
        ]

        return random.choice(ua_list)
