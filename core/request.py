# -*-* coding:UTF-8
import httpx
import random
import hashlib
import contextlib
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


class Request:
    """ 网络封装 """

    def __init__(self, target=None, config=None):
        self.target, self.config, self.headers, self.proxies = target, config, None, None
        with contextlib.suppress(Exception):
            self.headers = {
                k: (RandomUserAgent.get() if k == 'User-Agent' and not v else v)
                for k, v in config['network']['headers'].items()
            }
            self.proxies = {f'{k}://': v for k, v in config['network']['proxies'].items() if v}
        kwargs = {
            "verify": False,
            "headers": self.headers,
            "proxies": self.proxies,
            "follow_redirects": True,
            "cache": httpx_cache.FileCache(cache_dir='cache'),
            "cacheable_methods": ('GET', 'POST'),
            "cacheable_status_codes": (200, 404)
        }
        self.client = httpx_cache.Client(**kwargs)
        self.async_client = httpx_cache.AsyncClient(**kwargs)

    def request(self, method='get', url=None, path=None, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        try:
            response = self.client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            url = url.replace('https://', 'http://') if 'https://' in url else url.replace('http://', 'https://')
            response = self.client.request(method=method, url=url, *args, **kwargs)
        except Exception as e:
            raise Exception(e)
        return self.decorate_response(response)

    async def async_http(self, method='get', url=None, path=None, *args, **kwargs):
        if not url and path and self.target:
            url = urljoin(self.target.value, path)
        try:
            response = await self.async_client.request(method=method, url=url, *args, **kwargs)
        except httpx.ConnectError as connect_error:
            url = url.replace('https://', 'http://') if 'https://' in url else url.replace('http://', 'https://')
            response = await self.async_client.request(method=method, url=url, *args, **kwargs)
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
