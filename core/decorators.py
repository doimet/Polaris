# -*-* coding:UTF-8
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

    def command(self):
        self.t_depth += 1

        def wrapper(func):
            def inner(cls):
                return func(cls)

            return inner

        return wrapper

    def echo_handle(self, log, name=None, data=None, key='result'):
        """ 数据回显处理 """

        if isinstance(data, str) or isinstance(data, int):
            data = str(data).strip()
            if data.count('\n') > 0:
                data = '\n' + data
            log.info(f'{key}: {data}')
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
            params = {'default': None, 'desc': '-', 'type': str, 'choice': [], 'required': False}
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
            kwargs[k] = v
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

                    cls.log.root(rf'Start entering console mode [help|show|run|quit]{" " * 10}')
                    cls.log.echo(f"\n    {cls.__info__.get('description', '暂无关于此漏洞的描述信息')}\n")
                    while True:
                        keyword = input(f'\r{150 * " "}\r[localhost \033[0;31m~\033[0m]# ')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?']:
                            cls.log.info('Grammar:')
                            cls.log.echo('set {variable} {value}')
                            cls.log.echo('get {function} {value}')
                            cls.log.echo('')
                            cls.log.info('Function:')
                            data = [
                                {
                                    'md5': 'MD5加密',
                                    'mmh3': 'MMH3加密',
                                    'base64Encode': 'Base64编码',
                                    'base64Decode': 'Base64解码',
                                }
                            ]
                            tb = get_table_form(data, layout='vertical', title=['name', 'notes'])
                            cls.log.echo(tb)
                        elif keyword in ['show']:
                            data = [
                                {
                                    'variable': k,
                                    'description': v['desc'],
                                    'default': v['default'],
                                } for k, v in kwargs.items() if k
                            ]
                            if data:
                                tb = get_table_form(data)
                                cls.log.echo(tb)

                        elif keyword in ['start', 'run']:
                            # 参数值是否必须检测
                            for k, v in kwargs.items():
                                if v['required'] and not v['default']:
                                    cls.log.error(f"Undefined variable: {k}")
                                    break
                            else:
                                # 恢复消息线程
                                cls.event.set()
                                args = tuple([v['default'] for k, v in kwargs.items()])
                                try:
                                    if all([True if _ else False for _ in args]):
                                        res = func(cls, *args)
                                    else:
                                        res = func(cls)
                                    if res:
                                        self.dataset = res
                                        self.echo_handle(cls.log, name=cls.options.plugin, data=res)
                                    else:
                                        cls.log.warn('')
                                except Exception as e:
                                    cls.log.warn(e)
                                # 暂停消息线程
                                cls.event.clear()
                        else:
                            match = re.match(r'([\w]{3}) ([\w-]+)[ :=]?(.*)', keyword)
                            if not match:
                                cls.log.error("Input is wrong")
                            else:
                                match_op, match_name, match_value = match.group(1), match.group(2), match.group(3)
                                if match_op == 'set':
                                    if match_name in kwargs.keys():
                                        convert = kwargs[match_name]['type']
                                        choice = kwargs[match_name]['choice']
                                        if len(choice) != 0 and match_value not in choice:
                                            cls.log.error(f"invalid choice: {match_value}. (choose from {', '.join(choice)})")
                                        elif convert not in [str, float, int, bool]:
                                            cls.log.error(f"Unknown type: {convert}")
                                        kwargs[match_name]['default'] = convert(match_value)
                                    else:
                                        cls.log.error(f"Unknown variable: {match_name}")
                                elif match_op == 'get':
                                    if os.path.isfile(match_value):
                                        with open(match_value, encoding='utf-8-sig') as f:
                                            match_value = f.read()
                                    elif re.match(r'^http[s]://.*', match_value):
                                        r = cls.request('get', match_value)
                                        match_value = r.content
                                    if match_name == 'md5':
                                        cls.log.info(f'Result: {hashlib.md5(match_value.encode()).hexdigest()}')
                                    elif match_name == 'mmh3':
                                        cls.log.info(f'Result: {mmh3.hash(match_value)}')
                                    elif match_name == 'base64Encode':
                                        cls.log.info(f'Result: {base64.b64encode(match_value.encode()).decode()}')
                                    elif match_name == 'base64Decode':
                                        cls.log.info(f'Result: {base64.b64decode(match_value).decode()}')
                                    else:
                                        cls.log.error(f"Unknown function: {match_name}")
                                else:
                                    cls.log.error(f"Unknown grammar: {match_op}")
                    return self.dataset
                else:
                    return func(cls, **kwargs)

            return inner

        return wrapper
