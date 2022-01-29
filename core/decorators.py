import base64
import hashlib
import os
import re
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
            log.info(f'{key}: {str(data).strip()} ({name})')
        elif isinstance(data, list) and len(data) != 0:
            log.info(f'{key}: {len(data)} ({name})')
            table = get_table_form(data)
            log.echo(str(table))
        elif isinstance(data, dict):
            if not all(map(lambda x: isinstance(x, str) or isinstance(x, int), data.values())):
                for k, v in data.items():
                    self.echo_handle(log, name=name, data=v, key=k)
            else:
                log.info(f'{key}: 1 ({name})')
                table = get_table_form(data, layout='vertical')
                log.echo(str(table))

    @staticmethod
    def kwargs_handle(cls, value):
        """ 输入参数处理 """
        kwargs = {}
        for k, v in value.items():
            params = {'default': None, 'desc': '-', 'type': str, 'choice': []}
            params.update(v)
            v = params
            # 参数值校验
            if not all(
                    [
                        isinstance(v['desc'], str),
                        v['type'] in [str, int, float, bool],
                        isinstance(v['choice'], list)
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

                    cls.log.root(f'开始进入控制台模式 [quit:退出|help:帮助|run:运行]{" " * 10}')
                    cls.log.echo(f"\n    {cls.__info__.get('description', '暂无关于此漏洞的描述信息')}\n")
                    while True:
                        keyword = input('[localhost \033[0;31m~\033[0m]# ')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?', 'show']:
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
                                cls.log.echo('\nGrammar: ')
                                cls.log.echo('  set {variable} {value}')
                                cls.log.echo('  get {function} {value}\n')
                                cls.log.echo('Function: ')
                                cls.log.echo('  md5、base64Encode、base64Decode\n')
                        elif keyword in ['start', 'run']:
                            # 恢复消息线程
                            cls.event.set()

                            args = tuple([v['default'] for k, v in kwargs.items()])
                            try:
                                if all([True if _ else False for _ in args]):
                                    res = func(cls, *args)
                                else:
                                    res = func(cls)
                                self.dataset = res
                                self.echo_handle(cls.log, name=cls.options.plugin, data=res)
                            except Exception as e:
                                cls.log.warn(e)

                            # 暂停消息线程
                            cls.event.clear()
                        else:
                            set_match = re.match(r'set ([\w-]+)[ :=]?(.*)', keyword)
                            get_match = re.match(r'get ([\w-]+)[ :=]?(.*)', keyword)
                            if set_match:
                                _name, _value = set_match.group(1), set_match.group(2)
                                if _name in kwargs.keys():
                                    convert = kwargs[_name]['type']
                                    choice = kwargs[_name]['choice']
                                    if len(choice) != 0 and _value not in choice:
                                        cls.log.error(f"invalid choice: {_value}. (choose from {', '.join(choice)})")
                                    elif convert not in [str, float, int, bool]:
                                        cls.log.error("error in type")
                                    kwargs[_name]['default'] = convert(_value)
                                else:
                                    cls.log.error("variable unavailable")

                            elif get_match:
                                _name, _value = get_match.group(1), get_match.group(2)
                                if os.path.isfile(_value):
                                    with open(_value, encoding='utf-8-sig') as f:
                                        _value = f.read()
                                elif re.match(r'^http[s]://.*', _value):
                                    with cls.request('get', _value) as r:
                                        _value = r.content

                                if _name == 'md5':
                                    cls.log.info(hashlib.md5(_value.encode()).hexdigest())
                                elif _name == 'base64Encode':
                                    cls.log.info(base64.b64encode(_value.encode()).decode())
                                elif _name == 'base64Decode':
                                    cls.log.info(base64.b64decode(_value).decode())
                                else:
                                    cls.log.error("function unavailable")
                            else:
                                cls.log.error("input is wrong")
                    return self.dataset
                else:
                    return func(cls, **kwargs)

            return inner

        return wrapper
