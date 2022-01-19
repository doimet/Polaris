import re
from core.common import get_table_form


class Cli:
    def __init__(self):
        self.t_depth = 0
        self.c_depth = 0

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
            default = v['default']
            if isinstance(default, str) and default.startswith('{') and default.endswith('}'):
                try:
                    v['default'] = eval(default[1:-1].replace('self', 'cls'))
                except:
                    pass
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
                    if not cls.options.shell:
                        args = tuple([_.get('default') for _ in kwargs.values()])
                        return func(cls, *args)

                    cls.log.root(f'开始进入终端模式 [quit:退出|help:帮助|run:运行]{" " * 10}')
                    cls.log.echo(f"\n    {cls.__info__.get('description', '暂无关于此漏洞的描述信息')}\n")
                    while True:
                        keyword = input('[localhost \033[0;31m~\033[0m]# ')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?', 'info']:
                            data = [
                                {
                                    'Variable': k,
                                    'Description': v.get('desc', '-'),
                                    'Default': v.get("default", '-')
                                } for k, v in kwargs.items() if k
                            ]
                            if data:
                                tb = get_table_form(data)
                                cls.log.echo(tb)
                                cls.log.echo('\nGrammar: set {variable} {value}\n')
                        elif keyword in ['exploit', 'run']:
                            # 恢复消息线程
                            cls.event.set()

                            args = tuple([_.get('default') for _ in kwargs.values()])
                            try:
                                if all([True if _ else False for _ in args]):
                                    res = func(cls, *args)
                                else:
                                    res = func(cls)
                                self.echo_handle(cls.log, name=cls.options.plugin, data=res)
                            except Exception as e:
                                cls.log.warn(e)

                            # 暂停消息线程
                            cls.event.clear()
                        else:
                            match = re.match(r'set ([\w-]+)[ :=]?(.*)', keyword)
                            if match:
                                _name, _value = match.group(1), match.group(2)
                                if _name in kwargs.keys():
                                    convert = kwargs[_name].get('type', str)
                                    if convert in [str, float, int]:
                                        kwargs[_name]['default'] = convert(_value)
                                    else:
                                        cls.log.error("error in type")
                                else:
                                    cls.log.error("variable unavailable")
                            else:
                                cls.log.error("syntax error")
                else:
                    return func(cls, **kwargs)

            return inner

        return wrapper
