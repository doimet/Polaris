# -*-* coding:UTF-8
import asyncio
import hashlib
import json
import os.path
import random
import re
import time
import celpy
import yaml
import functools
import sys
import logging
import urllib.parse
from base64 import b64encode, b64decode
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA256
from flashtext import KeywordProcessor
from logging.handlers import TimedRotatingFileHandler
from core.request import Request


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Logging(logging.Logger):
    """ 日志基类 """

    def __init__(self, level=logging.INFO, mode=0):
        super(Logging, self).__init__(name='error', level=level)
        # self.__setFileHandler__()
        self.__setStreamHandler__()
        self.is_shell_mode = mode # 1表示交互模式, 0非交互模式

    def set_level(self, level):
        self.setLevel(level)

    def set_mode(self, mode):
        self.is_shell_mode = mode

    def __setFileHandler__(self, level=30):
        filename = os.path.join('logs', '{}.log'.format(self.name))
        file_handler = TimedRotatingFileHandler(filename=filename, when='D', interval=1, backupCount=1)
        file_handler.setLevel(level)
        formatter = logging.Formatter("[%(asctime)s] %(message)s")
        file_handler.setFormatter(formatter)
        self.addHandler(file_handler)

    def __setStreamHandler__(self, level=10):
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        self.addHandler(stream_handler)

    def echo(self, msg, *args, **kwargs):
        self._log(70, "{}".format(str(msg)), args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """ 调试输出 """

        if self.isEnabledFor(10):
            msg = str(msg)
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            shape = '[*]' if self.is_shell_mode else ' | '
            self._log(10, "\r\033[0;34m{}\033[0m {}".format(shape, msg + (100 - len(msg)) * ' '), args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(20):
            msg = str(msg)
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            shape = '[i]' if self.is_shell_mode else ' | '
            self._log(20, "\r\033[0;34m{}\033[0m {}".format(shape, msg + (100 - len(msg)) * ' '), args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """ 异常输出 """

        if self.isEnabledFor(30):
            msg = str(msg)
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            shape = '[!]' if self.is_shell_mode else ' | '
            self._log(30, "\r\033[0;33m{}\033[0m {}".format(shape, msg + (100 - len(msg)) * ' '), args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """ 错误输出 """

        if self.isEnabledFor(40):
            msg = str(msg)
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            shape = '[-]' if self.is_shell_mode else ' | '
            self._log(40, "\r\033[0;31m{}\033[0m {}".format(shape, msg + (100 - len(msg)) * ' '), args, **kwargs)

    def child(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(50):
            msg = str(msg)
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(50, "\r\033[0;34m | \033[0m {}".format(msg + (100 - len(msg)) * ' '), args, **kwargs)

    def root(self, msg, *args, **kwargs):
        """ 消息输出 """
        if self.isEnabledFor(60):
            self._log(60, "\r\033[0;34m[+]\033[0m {}".format(msg), args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """ 严重输出 调用会导致程序结束 """

        if self.isEnabledFor(70):
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(70, "\r\033[0;31m[-]\033[0m {}".format(msg), args, **kwargs)
            sys.exit(1)


class EchoQueryExecute:
    def __init__(self):
        rsa = RSA.generate(2048)
        random_str = str(uuid4())
        self.public_key = rsa.publickey().exportKey()
        self.private_key = rsa.exportKey()
        self.secret = random_str
        self.correlation_id = random_str[:20]
        self.result = None
        self.session = Request()
        self.create()

    def create(self):
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.request(
            method="post",
            url="https://interact.sh/register",
            json={
                "public-key": b64encode(self.public_key).decode("utf-8"),
                "secret-key": self.secret,
                "correlation-id": self.correlation_id
            }
        )

    def get_domain(self):
        """ 获取域名 """
        domain = self.correlation_id
        while len(domain) < 33:
            domain += chr(ord('a') + random.randint(1, 24))
        domain += ".interact.sh"
        return domain

    def get_url(self):
        """ 获取url """
        pass

    def select(self):
        """ 轮询结果 """
        count = 3
        result = []
        while count:
            try:
                with self.session.request(
                        method="get",
                        url=f"https://interact.sh/poll?id={self.correlation_id}&secret={self.secret}"
                ) as r:
                    resp = r.json()
                    for i in resp['data']:
                        cipher = PKCS1_OAEP.new(RSA.importKey(self.private_key), hashAlgo=SHA256)
                        decode = b64decode(i)
                        cryptor = AES.new(
                            key=cipher.decrypt(b64decode(resp['aes_key'])),
                            mode=AES.MODE_CFB,
                            IV=decode[:AES.block_size],
                            segment_size=128
                        )
                        plain_text = cryptor.decrypt(decode)
                        result.append(json.loads(plain_text[16:]))
                    return result
            except Exception as e:
                count -= 1
                time.sleep(1)
                continue
        return []

    @property
    def verify(self):
        """ 验证 """
        status, self.result = self.select()
        return True if status else False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self


class AsyncioExecute(object):
    """ 异步执行器 """

    def __init__(self, max_workers=150, threshold=None):
        if int(max_workers) <= 0:
            raise ValueError("max_workers must be greater than 0, default 150")
        self._all_task = []
        self._threshold = threshold
        self._new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._new_loop)
        self._lock = asyncio.Semaphore(int(max_workers))
        self.loop = asyncio.get_event_loop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()

    def submit(self, func, *args):
        task = asyncio.ensure_future(self.work(func, args))
        task.set_name(('-', args[0])[len(args) != 0])
        task.add_done_callback(self.on_finish)
        self._all_task.append(task)

    async def work(self, func, args):
        async with self._lock:
            try:
                res = await functools.partial(func, *args)()
                return res
            except Exception as e:
                pass

    def on_finish(self, future):
        if self._threshold:
            info = future.get_name()
            match = re.search("'name':\s+'([\w().-]+)'", info)
            if match:
                name = match.group(1)
            else:
                name = info
            self._threshold['name'] = str(name)[:25]
            self._threshold['count'] += 1
            self._threshold['status'] = (0, 1)[future.result() is not None]

    def result(self):
        if self._threshold:
            self._threshold['total'] += len(self._all_task)
        res = self.loop.run_until_complete(asyncio.gather(*self._all_task, loop=self.loop, return_exceptions=False))
        res = [_ for _ in res if _ is not None]
        return res[0] if len(res) == 1 else res


class PluginBase(Request):
    """ 插件基类 """

    __info__ = {
        "name": "-",
        "author": "-",
        "description": "-",
        "references": ["-"],
        "datetime": "-"
    }

    def __init__(self, options, config, target, threshold):
        self.config = DictObject(config)
        self.target = DictObject(target)
        self.options = DictObject(options)
        if self.target.key == 'url':
            res = parse.urlparse(self.target.value)
            self.target.update(
                {
                    'url': {
                        'host': res.netloc,
                        'path': res.path
                    }
                }
            )
        Request.__init__(self, self.target)
        self.threshold = threshold
        self.log = Logging(level=target.get('args', {}).get('verbose', 20), mode=self.options.shell)
        self.async_pool = AsyncioExecute
        self.echo_query = EchoQueryExecute

    @property
    def __method__(self):
        method = []
        decorated_func = ''
        for k, v in self.__class__.__dict__.items():
            if type(v).__name__ == 'function' and not k.startswith('__') and not k.startswith('custom'):
                method.append(k)
        return method

    @property
    def __decorate__(self):
        decorate = ''
        for k, v in self.__class__.__dict__.items():
            if type(v).__name__ == 'function' and not k.startswith('__') and not k.startswith('custom'):
                if v.__name__ == 'inner':
                    decorate = k
        return decorate


class XrayPoc(PluginBase):
    """ xray poc模板 """
    __vars__ = {}
    __rule__ = {}
    __logic__ = ""
    __output__ = {}

    def url(self):
        vars = {}
        condition = {}
        env = celpy.Environment()

        for k, v in self.__vars__.items():
            if 'request' in str(v):
                v = v.repalce('request', 'target')
            vars[k] = eval(f'self.{v}')

        for k, v in self.__rule__.items():
            options = {
                "method": v['request']['method'],
                "path": v['request']['path'],
                "allow_redirects": v['request'].get('follow_redirects', True),
                "headers": v['request'].get('headers', {}),
                "data": v['request'].get('body', {})
            }
            for i, j in vars.items():
                options = json.loads(json.dumps(options).replace('{{' + i + '}}', str(j)))

            response = self.request(**options)

            def contains(src, value):
                return True if value in src else False

            def bcontains(src, value):
                return True if value.decode() in src else False

            def icontains(src, value):
                return True if value in src else False

            def bsubmatch(reg, src):
                return re.search(reg, src.decode())

            def bmatches(reg, src):
                return True if re.search(reg, src.decode()) else False

            def md5(value):
                return hashlib.md5(value.encode()).hexdigest()

            def base64(value):
                if isinstance(value, str):
                    value = value.encode()
                return b64encode(value).decode()

            def base64Decode(value):
                if isinstance(value, str):
                    value = value.encode()
                return b64decode(value).decode()

            def urlencode(value):
                return urllib.parse.quote(value, safe='/', encoding=None, errors=None)

            def urldecode(value):
                return urllib.parse.unquote(value, encoding='utf-8')

            def substr(value, start, end):
                return value[start:end]

            def sleep(value):
                time.sleep(value)

            def string(value):
                if isinstance(value, bytes):
                    value = value.decode()
                else:
                    value = str(value)
                return value

            ast = env.compile(v['expression'])
            prgm = env.program(
                ast,
                functions=[
                    contains, bcontains, icontains, bmatches, bsubmatch, urlencode, urldecode, base64, base64Decode,
                    md5, string, bytes, sleep, substr
                ]
            )
            kwargs = {
                'response': celpy.json_to_cel(
                    {
                        'status': response.status_code,
                        'body': response.text,
                        'headers': celpy.json_to_cel(dict(response.headers)),
                        'content_type': response.headers['content-type']
                    }
                )
            }
            kwargs.update(vars)
            res = prgm.evaluate(kwargs)
            condition[k] = str(res)
        for k, v in condition.items():
            self.__logic__ = self.__logic__.replace(f'{k}()', v)
        if eval(self.__logic__.replace('&&', '&').replace('||', '|')):
            return 'success'


class DictObject(dict):
    def __init__(self, *args, **kwargs):
        super(DictObject, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        value = self.get(key, {})
        if isinstance(value, dict):
            value = DictObject(value)
        return value


class PluginObject(dict):
    def __getattr__(self, item):
        return dict.__getitem__(self, item)


class Interval(object):
    def __init__(self):
        self.st = bin(0)
        self.ed = bin(0)

    def change(self, new_st, new_ed):
        self.st = new_st
        self.ed = new_ed
