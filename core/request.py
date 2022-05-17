# -*-* coding:UTF-8
import random
import _socket
import hashlib
import httpx
import httpx_cache
from urllib.parse import urljoin


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

    def __init__(self, target=None, config=None):
        self.target = target
        self.config = config
        if config:
            self.headers = config['network']['headers']
            if not self.headers.get('User-Agent', None):
                self.headers['User-Agent'] = RandomUserAgent.get()
            self.proxies = {f'{k}://': v for k, v in config['network']['proxies'].items() if v}
        else:
            self.headers, self.proxies = None, None
        self.client = httpx_cache.Client(
            verify=False,
            headers=self.headers,
            proxies=self.proxies,
            follow_redirects=True,
            cache=httpx_cache.FileCache(cache_dir='cache')
        )
        self.async_client = httpx_cache.AsyncClient(
            verify=False,
            headers=self.headers,
            proxies=self.proxies,
            follow_redirects=True,
            cache=httpx_cache.FileCache(cache_dir='cache')
        )

    def request(self, method='get', url=None, path=None, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
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
            raise Exception(e)
        return self.decorate_response(response)

    async def async_http(self, method='get', url=None, path=None, *args, **kwargs):

        if not url and path and self.target:
            url = urljoin(self.target.value, path)
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
            raise Exception(e)
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


class RandomUserAgent:
    """ 随机UA """

    @staticmethod
    def get():
        chrome_version = 'Chrome/{}.0.{}.{}'.format(
            random.randint(55, 75),
            random.randint(0, 3200),
            random.randint(0, 140)
        )

        ua = 'Mozilla/5.0 {} AppleWebKit/537.36 (KHTML, like Gecko) {} Safari/537.36'.format(
            random.choice(
                [
                    "(Windows NT 6.1; WOW64)",
                    "(Windows NT 10.0; WOW64)",
                    "(X11; Linux x86_64)",
                    "(X11; Linux i686)",
                    "(Macintosh;U; Intel Mac OS X 10_12_6;en-AU)",
                    "(iPhone; U; CPU iPhone OS 11_0_6 like Mac OS X; en-SG)",
                    "(Windows NT 10.0; Win64; x64; Xbox; Xbox One)",
                    "(iPad; U; CPU OS 11_3_2 like Mac OS X; en-US)",
                    "(Macintosh; Intel Mac OS X 10_14_1)"
                ]
            ),
            chrome_version
        )
        return ua
