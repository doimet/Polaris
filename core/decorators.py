# -*-* coding:UTF-8
import asyncio
import functools
import importlib
import os
import re
import mmh3
import base64
import hashlib
from core.common import get_table_form


class Cli:
    def __init__(self):
        self.t_depth = 0
        self.c_depth = 0
        self.dataset = None
        self.temp = None

    # def command(self):
    #
    #     def wrapper(func):
    #         def inner(cls, *args, **kwargs):
    #             return func(cls, *args)
    #
    #         return inner
    #
    #     return wrapper

    def command(self, func):

        def inner(cls, *args, **kwargs):
            return func(cls, *args)

        return inner

    def echo_handle(self, log, name=None, data=None, key='result'):
        """ 数据回显处理 """

        if isinstance(data, str) or isinstance(data, int):
            data = str(data).strip()
            if data.count('\n') > 0:
                data = '\n' + data
            log.info(f'{key}: {data}')
        elif isinstance(data, tuple):
            log.info(f'{key}: {", ".join(data)}')
        elif isinstance(data, list) and len(data) != 0:
            log.info(f'{key}: {len(data)}')
            table = get_table_form(data)
            log.echo(str(table))
        elif isinstance(data, dict):
            if not all(map(lambda x: isinstance(x, str) or isinstance(x, int), data.values())):
                for k, v in data.items():
                    self.echo_handle(log, name=name, data=v, key=k)
            else:
                log.info(f'{key}: 1')
                table = get_table_form(data, layout='vertical')
                log.echo(str(table))

    @staticmethod
    def kwargs_handle(cls, value):
        """ 输入参数处理 """
        kwargs = {}
        for k, v in value.items():
            params = {'default': None, 'desc': '-', 'type': str, 'choice': [], 'required': False, 'built-in': False}
            params.update(v)
            v = params
            # 参数值校验
            if not all(
                    [
                        isinstance(v['desc'], str),
                        v['type'] in [str, int, float, bool],
                        isinstance(v['choice'], list),
                        isinstance(v['required'], bool)
                    ]
            ):
                raise Exception(f'plugin {cls.options.plugin} cli-params value type is wrong')

            if isinstance(v['default'], str) and v['default'].startswith('{') and v['default'].endswith('}'):
                try:
                    v['default'] = eval(v['default'][1:-1].replace('self', 'cls'))
                except Exception as e:
                    raise Exception(f"plugin {cls.options.plugin} cli-params value parse error")
            # 必备参数未传值需异常处理
            if v['required'] and not v['default']:
                raise Exception(f"Undefined variable: {k}")
            kwargs[k] = v

        # 附加内置参数
        if 'count' not in kwargs.keys():
            kwargs['count'] = {
                'default': cls.config.general.asyncio,
                'desc': '协程并发数量',
                'type': int,
                'choice': [],
                'required': False,
                'built-in': True
            }

        return kwargs

    def options(self, name='', **attrs):
        self.t_depth += 1

        def wrapper(func):
            def inner(cls, *args, **kwargs):
                self.c_depth += 1
                kwargs.update({name: attrs})
                if self.c_depth == self.t_depth:
                    kwargs = self.kwargs_handle(cls, kwargs)
                    if not cls.options.console:
                        args = tuple([_['default'] for _ in kwargs.values()])
                        return func(cls, *args)

                    cls.log.root(rf'Start entering console mode [:?]{" " * 10}')
                    cls.log.echo(f"\n    {cls.__info__.get('description', '暂无关于此漏洞的描述信息')}\n")
                    while True:
                        keyword = input(f'\r{150 * " "}\r[localhost \033[0;31m~\033[0m]# ')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?']:
                            cls.log.info('Usage:')
                            cls.log.echo('set {variable} {value} / {function} {param} {param} ...')
                            cls.log.echo('')
                            cls.log.echo(':show options   显示可变参数')
                            cls.log.echo(':show function  显示调用函数')
                            cls.log.echo(':set            设置参数')
                            cls.log.echo(':run            运行插件')
                            cls.log.echo(':help           显示帮助信息')
                        elif keyword in ['show options']:
                            variable_list = [
                                {
                                    'variable': k,
                                    'description': v['desc'],
                                    'default': v['default'],
                                } for k, v in kwargs.items() if k
                            ]
                            if variable_list:
                                tb = get_table_form(variable_list)
                                cls.log.echo(tb)
                        elif keyword in ['show function']:
                            temp_function_dict = {}
                            module_object = importlib.import_module("core.utils")
                            for method_name in dir(module_object):
                                if method_name[0] != '_':
                                    class_attr_obj = getattr(module_object, method_name)
                                    if type(class_attr_obj).__name__ == 'function' and class_attr_obj.__doc__:
                                        description = class_attr_obj.__doc__
                                        if description in temp_function_dict.keys():
                                            temp_function_dict[description].append(method_name)
                                        else:
                                            temp_function_dict[description] = [method_name]

                            if temp_function_dict:
                                function_list = [
                                    {
                                        'function': ' / '.join(v),
                                        'description': k
                                    } for k, v in temp_function_dict.items()
                                ]
                                tb = get_table_form(function_list)
                                cls.log.echo(tb)
                        elif keyword:
                            match = keyword.split(' ')
                            command = match[0]
                            if command == 'set' and len(match) == 3:
                                variable = match[1]
                                value = match[2]
                                if variable in kwargs.keys():
                                    convert = kwargs[variable]['type']
                                    choice = kwargs[variable]['choice']
                                    if len(choice) != 0 and value not in choice:
                                        cls.log.error(
                                            f"invalid choice: {value}. (choose from {', '.join(choice)})")
                                    elif convert not in [str, float, int, bool]:
                                        cls.log.error(f"Unknown type: {convert}")
                                    kwargs[variable]['default'] = convert(value)
                                    # 避免源类在多次赋值时被替换
                                    if self.temp:
                                        cls.async_pool = self.temp
                                    else:
                                        self.temp = cls.async_pool
                                    cls.async_pool = functools.partial(cls.async_pool, kwargs['count']['default'])
                                else:
                                    cls.log.error(f"Unknown variable: {variable}")
                            else:
                                if command in ['start', 'run']:
                                    args = tuple([v['default'] for k, v in kwargs.items() if not v['built-in']])
                                elif len(match) > 1:
                                    args = tuple(match[1:])
                                else:
                                    args = ()
                                # 恢复消息线程
                                cls.event.set()
                                try:
                                    if command in ['start', 'run']:
                                        res = func(cls, *args)
                                        self.dataset = res
                                    else:
                                        callback = functools.partial(cls.log.warn, f"Unknown usage: {keyword}")
                                        res = getattr(cls, command, callback)(*args)
                                    self.echo_handle(cls.log, name=cls.options.plugin, data=res)
                                except Exception as e:
                                    cls.log.warn(e)
                                # 暂停消息线程
                                cls.event.clear()
                    return self.dataset
                else:
                    return func(cls, **kwargs)

            return inner

        return wrapper
