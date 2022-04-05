# -*-* coding:UTF-8
import httpx
import random
import _socket
import hashlib
import requests.packages.urllib3
from urllib.parse import urljoin

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

    def __init__(self, target=None, config=None):
        self.target = target
        self.config = config
        self.url_cache = {}
        self.current_url = ''
        self.headers = {
            'User-Agent': RandomUserAgent.get(),
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.headers.update(config['network']['headers'] if 'network' in config.keys() else {})
        self.client = httpx.Client(verify=False)
        self.async_client = httpx.AsyncClient(verify=False)

    def request(self, method='get', url=None, path=None, cache=False, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        if url in self.url_cache and cache:
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
            raise Exception(e)
        self.url_cache[url] = response
        return self.decorate_response(response)

    async def async_http(self, method='get', url=None, path=None, cache=False, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        if url in self.url_cache and cache:
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
            raise Exception(e)
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
        response.condition = self.condition
        return response

    @staticmethod
    def condition(exp):
        return exp


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
