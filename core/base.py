# -*-* coding:UTF-8
import re
import sys
import time
import json
import yaml
import uuid
import celpy
import random
import asyncio
import hashlib
import os.path
import logging
import functools
import contextlib
import lxml.etree
import urllib.parse
from core.common import parse_raw_request
from core.request import Request
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA
from flashtext import KeywordProcessor
from base64 import b64encode, b64decode
from Cryptodome.Cipher import AES, PKCS1_OAEP
from logging.handlers import TimedRotatingFileHandler

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Logging(logging.Logger):
    """ 日志基类 """

    def __init__(self, level=logging.INFO, mode=0):
        super(Logging, self).__init__(name='error', level=level or 100)
        # self.__setFileHandler__()
        self.__setStreamHandler__()
        self.is_console_mode = mode  # 1表示交互模式, 0非交互模式
        self.records = []

    def set_level(self, level):
        self.setLevel(level)

    def set_mode(self, mode):
        self.is_console_mode = mode

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

    def make_record(self, record):
        self.records.append(record)
        sys.stdout.write('\r' + 100 * ' ' + '\r')
        return record

    def echo(self, msg, *args, **kwargs):
        if msg is not None:
            self._log(70, "{}".format(str(msg)), args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """ 调试输出 """

        if self.isEnabledFor(10) and msg is not None:
            shape = f'\r\033[0;34m[*]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            self._log(10, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), args,
                      **kwargs)

    def info(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(20) and msg is not None:
            shape = '\r\033[0;34m[i]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            self._log(20, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), args,
                      **kwargs)

    def success(self, msg, *args, **kwargs):
        """ 成功输出 """

        if self.isEnabledFor(25) and msg is not None:
            shape = '\r\033[0;32m[+]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            self._log(25, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), args,
                      **kwargs)

    def failure(self, msg, *args, **kwargs):
        """ 失败输出 """

        if self.isEnabledFor(25) and msg is not None:
            shape = '\r\033[0;31m[-]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            self._log(25, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), args,
                      **kwargs)

    def warn(self, msg, *args, **kwargs):
        """ 异常输出 """

        if self.isEnabledFor(30) and msg is not None:
            if not self.is_console_mode:
                msg = f'\033[0;33m{msg}\033[0m'
            shape = '\r\033[0;33m[!]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            # args置空 防止交互异常 日志打印报错信息
            self._log(30, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), (), **kwargs)

    def error(self, msg, *args, **kwargs):
        """ 错误输出 """

        if self.isEnabledFor(40) and msg is not None:
            if not self.is_console_mode:
                msg = f'\033[0;31m{msg}\033[0m'
            shape = '\r\033[0;31m[-]\033[0m' if self.is_console_mode else '\r\033[0;34m | \033[0m'
            self._log(40, self.make_record("{} {}".format(shape, str(msg) + (100 - len(str(msg))) * ' ')), args,
                      **kwargs)

    def child(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(50) and msg is not None:
            if self.is_console_mode:
                self._log(50, "{}".format(str(msg) + (100 - len(str(msg))) * ' '), (), **kwargs)
            else:
                msg = str(msg).replace('\n', '\n\033[0;34m | \033[0m ')
                self._log(50,
                          self.make_record("\r\033[0;34m | \033[0m {}".format(str(msg) + (100 - len(str(msg))) * ' ')),
                          (), **kwargs)

    def root(self, msg, *args, **kwargs):
        """ 消息输出 """
        if self.isEnabledFor(60) and msg is not None:
            self._log(60, self.make_record("\r\033[0;34m[+]\033[0m {}".format(str(msg) + (100 - len(str(msg))) * ' ')),
                      args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """ 严重输出 调用会导致程序结束 """

        if self.isEnabledFor(70):
            self._log(70, self.make_record("\r\033[0;31m[-]\033[0m {}".format(str(msg) + (100 - len(str(msg))) * ' ')),
                      args, **kwargs)
            sys.exit(1)


class EchoQueryExecute(Request):
    def __init__(self):
        Request.__init__(self)
        rsa = RSA.generate(2048)
        random_str = str(uuid.uuid4()).replace('-', '')
        self.public_key = rsa.publickey().exportKey()
        self.private_key = rsa.exportKey()
        self.secret = random_str
        self.correlation_id = random_str[:20]
        self.result_list = []
        self.create()

    def create(self):
        r = self.request(
            method="POST",
            url="https://interact.sh/register",
            json={
                "public-key": b64encode(self.public_key).decode("utf-8"),
                "secret-key": self.secret,
                "correlation-id": self.correlation_id
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        if 'registration successful' not in r.text:
            raise Exception('interact register failure')

    def get_subdomain(self):
        """ 获取域名 """
        subdomain = self.correlation_id
        while len(subdomain) < 33:
            subdomain += chr(ord('a') + random.randint(1, 24))
        subdomain += ".interact.sh"
        return subdomain

    def get_url(self):
        """ 获取url """
        subdomain = self.get_subdomain()
        url = 'http://' + subdomain
        return url

    def result(self):
        """ 获取结果 """
        if self.result_list:
            self.result_list = sorted(self.result_list, key=lambda x: x['timestamp'].split('T')[0])[0]
        return self.result_list

    def select(self):
        """ 轮询结果 """
        count = 3
        status = False
        result = []
        while count:
            with contextlib.suppress(Exception):
                r = self.request(
                    method="GET",
                    url=f"https://interact.sh/poll?id={self.correlation_id}&secret={self.secret}",
                    timeout=7
                )
                resp = r.json()
                for i in resp['data']:
                    cipher = PKCS1_OAEP.new(RSA.importKey(self.private_key), hashAlgo=SHA256)
                    decode = b64decode(i)
                    crypto = AES.new(
                        key=cipher.decrypt(b64decode(resp['aes_key'])),
                        mode=AES.MODE_CFB,
                        IV=decode[:AES.block_size],
                        segment_size=128
                    )
                    plain_text = crypto.decrypt(decode)
                    data = json.loads(plain_text[16:])
                    res = '...'
                    if data['protocol'] == 'http':
                        options = parse_raw_request(data['raw-request'])
                        if options['method'] == 'POST':
                            res = options['data']
                        elif options['method'] == 'GET':
                            res = options['path']
                    result.append(
                        {
                            'result': res,
                            'address': data['remote-address'],
                            'datetime': data['timestamp']
                        }
                    )
                    status = True
            if not result:
                count -= 1
                time.sleep(1)
            break
        return status, result

    def verify(self):
        """ 验证 """
        status, self.result_list = self.select()
        return True if status else False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()


class AsyncioExecute(object):
    """ 异步执行器 """

    def __init__(self, max_workers=50):
        if not isinstance(max_workers, int):
            raise Exception('TypeError: max_workers must be int')
        elif max_workers <= 0:
            raise ValueError("max_workers must be greater than 0, default 50")
        self._all_task = []
        self._new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._new_loop)
        self.lock = asyncio.Semaphore(max_workers)
        self.loop = asyncio.get_event_loop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()

    def submit(self, func, *args):
        task = asyncio.ensure_future(self.work(func, args))
        task.set_name(('-', args[-1])[len(args) != 0])
        task.add_done_callback(self.on_finish)
        self._all_task.append(task)

    async def work(self, func, args):
        async with self.lock:
            with contextlib.suppress(Exception):
                res = await functools.partial(func, *args)()
                return res

    def on_finish(self, future):
        if self.threshold:
            info = future.get_name()
            match = re.search(r"'name':\s+'([\w().-]+)'", info)
            if match:
                name = match.group(1)
            else:
                name = info
            self.threshold['name'] = str(name)[:25]
            self.threshold['count'] += 1
            self.threshold['status'] = (0, 1)[future.result() is not None]

    def result(self):
        if self.threshold:
            self.threshold['total'] += len(self._all_task)
        res = self.loop.run_until_complete(asyncio.gather(*self._all_task, loop=self.loop, return_exceptions=False))
        res = [_ for _ in res if _ is not None]
        return res[0] if len(res) == 1 else res


class PluginBase(Request):
    """ 插件基类 """
    target = None

    __info__ = {
        "name": "",
        "dork": "",
        "description": "",
        "references": ["-"],
    }

    def __init__(self, options, config, target, event, threshold):
        self.config = DictObject(config)
        self.target = DictObject(target)
        self.options = DictObject(options)
        Request.__init__(self, self.target, self.config)
        self.event = event
        self.threshold = threshold
        self.log = Logging(level=self.options.verbose, mode=self.options.console)
        self.async_pool = AsyncioExecute
        setattr(self.async_pool, 'threshold', threshold)
        self.echo_query = EchoQueryExecute
        self.init()

    def init(self):
        """ 自定义初始化方法 """
        ...

    @property
    def __method__(self):
        method = []
        for k, v in self.__class__.__dict__.items():
            if (
                    type(v).__name__ == 'function' and
                    not k.startswith('__') and
                    not k.startswith('custom') and
                    'Cli.command' not in str(v)
            ):
                method.append(k)
        return method

    @property
    def __decorate__(self):
        method = []
        for k, v in self.__class__.__dict__.items():
            if 'Cli.command' in str(v):
                method.append(k)
        return method

    def __condition__(self):
        return True

    def condition(self, matches=None, logic=None):
        condition = []
        for index, match in enumerate(matches or []):
            try:
                r = self.request(method='get', url=urllib.parse.urljoin(self.target.value, match.get('path', '.')))
                search, dom = match.get('search', 'all'), lxml.etree.HTML(r.content)
                if search == 'title':
                    content = str(dom.xpath('/html/head/title/text()')[0])
                elif search == 'headers':
                    content = "\r\n".join(f"{k}: {v}" for k, v in r.headers.items())
                elif search == 'body':
                    content = lxml.etree.tostring(dom.xpath('/html/body')[0]).decode()
                elif search == 'cookies':
                    content = r.headers.get('set-cookie')
                elif search == 'meta':
                    content = ';'.join(dom.xpath('//meta/@content'))
                elif search == 'script':
                    content = ''.join(lxml.etree.tostring(script).decode() for script in dom.xpath('//script'))
                else:
                    content = r.text

                condition.append(
                    any([
                        'md5' in match.keys() and r.md5 == match['md5'],
                        # 'hash' in match.keys() and r.hash == match['hash'],
                        'keyword' in match.keys() and (
                                (isinstance(match['keyword'], str) and match['keyword'] in content) or
                                (isinstance(match['keyword'], list) and all([_ in content for _ in match['keyword']]))
                        ),
                        'status' in match.keys() and r.status_code == match['keyword']
                    ])
                )
            except Exception as e:
                condition.append(False)

        if logic:
            if isinstance(logic, bool):
                return logic
            for index, value in enumerate(condition):
                logic = logic.replace(str(index), str(value))
            return eval(logic)
        return any(condition)


class YamlPoc(PluginBase):
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
                "follow_redirects": v['request'].get('follow_redirects', True),
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
