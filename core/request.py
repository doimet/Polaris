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

    def __init__(self, target):
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
        DNSProxy([self.resolve_name], self.resolve_host)

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
        if not url and path:
            url = urljoin(self.target.value, path)
        if url in self.url_cache:
            return self.url_cache[url]
        self.current_url = url
        self.headers.update(kwargs.get('headers', {}))
        kwargs.update({'headers': self.headers})
        try:
            response = self.client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            response = self.client.request(method=method, url=url.replace('http://', 'https://'), *args, **kwargs)
        except Exception as e:
            return Exception({"Error": e})
        self.url_cache[url] = response
        return self.decorate_response(response)

    async def async_http(self, method='get', url='', *args, **kwargs):
        if url in self.url_cache:
            return self.url_cache[url]
        self.current_url = url

        self.headers.update(kwargs.get('headers', {}))
        kwargs.update({'headers': self.headers})
        try:
            response = await self.async_client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            response = await self.async_client.request(method=method, url=url.replace('http://', 'https://'), *args,
                                                       **kwargs)
        except Exception as e:
            return Exception({"Error": e})
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
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.01',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
            'Mozilla/5.0 (Linux; Ubuntu 14.04) AppleWebKit/537.36 Chromium/35.0.1870.2 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0',
            "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
            "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
            "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
            "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
        ]

        return random.choice(ua_list)
