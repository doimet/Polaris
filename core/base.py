# -*-* coding:UTF-8
import asyncio
import json
import os.path
import random
import re
import string
import functools
import sys
import logging
from flashtext import KeywordProcessor
from core.request import Request
from logging.handlers import TimedRotatingFileHandler

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Logging(logging.Logger):
    """ 日志基类 """

    def __init__(self, level=logging.INFO):
        super(Logging, self).__init__(name='error', level=level)
        # self.__setFileHandler__()
        self.__setStreamHandler__()

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
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(10, "\r\033[0;34m | \033[0m {}".format(str(msg) + (100 - len(msg)) * ' '), args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(20):
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(20, "\r\033[0;34m | \033[0m {}".format(str(msg) + (100 - len(msg)) * ' '), args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """ 异常输出 """

        if self.isEnabledFor(30):
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(
                30,
                "\r\033[0;34m | \033[0m\033[0;33m {} \033[0m".format(str(msg) + (100 - len(msg)) * ' '), args, **kwargs
            )

    def error(self, msg, *args, **kwargs):
        """ 错误输出 """

        if self.isEnabledFor(40):
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(
                40,
                "\r\033[0;34m | \033[0m\033[0;31m {} \033[0m".format(str(msg) + (100 - len(msg)) * ' '), args, **kwargs
            )

    def child(self, msg, *args, **kwargs):
        """ 消息输出 """

        if self.isEnabledFor(50):
            sys.stdout.write('\r' + 100 * ' ' + '\r')
            self._log(50, "\r\033[0;34m | \033[0m {}".format(str(msg) + (100 - len(msg)) * ' '), args, **kwargs)

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

    def __init__(self, target, threshold):
        self.target = DictObject(target)
        Request.__init__(self, self.target)
        self.threshold = threshold
        self.log = Logging(level=target.get('args', {}).get('verbose', 20))
        self.async_pool = AsyncioExecute

    @property
    def func_dict(self):
        method_func = []
        decorated_func = ''
        for k, v in self.__class__.__dict__.items():
            if type(v).__name__ == 'function' and k not in ['__init__', 'task']:
                if v.__name__ == 'inner':
                    decorated_func = k
                else:
                    method_func.append(k)

        return {'method': method_func, 'decorate': decorated_func}


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
