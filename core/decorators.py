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

    def options(self, name='', **attrs):
        self.t_depth += 1

        def wrapper(func):
            def inner(cls, *args, **kwargs):
                self.c_depth += 1
                kwargs.update({name: attrs})
                if self.c_depth == self.t_depth:
                    if not cls.target.args.shell:
                        args = tuple([_.get('default') for _ in kwargs.values()])
                        return func(cls, *args)

                    cls.log.root(f'开始进入终端模式 [quit:退出|help:帮助|run:运行]{" " * 10}')
                    cls.log.echo(f"\n    {cls.__info__.get('description', '暂无关于此漏洞的描述信息')}\n")
                    while True:
                        keyword = input('shell>')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?', 'info']:
                            data = [
                                {
                                    '变量': k, '描述': v.get('description', '无'), '赋值': v.get("default", '无')
                                } for k, v in kwargs.items() if k
                            ]
                            if data:
                                tb = get_table_form(data, border=False)
                                cls.log.echo(tb)
                                cls.log.echo('\n语法: set {变量} {赋值}\n')
                        elif keyword in ['exploit', 'run']:
                            args = tuple([_.get('default') for _ in kwargs.values()])
                            try:
                                if all([True if _ else False for _ in args]):
                                    res = func(cls, *args)
                                else:
                                    res = func(cls)
                                cls.log.echo(res)
                            except Exception as e:
                                cls.log.echo(e)
                        else:
                            match = re.match(r'set ([\w-]+)[ :=]?(.*)', keyword)
                            if match:
                                _name, _value = match.group(1), match.group(2)
                                if _name in kwargs.keys():
                                    kwargs[_name]['default'] = _value
                                else:
                                    cls.log.echo("[-] 变量不存在")
                            else:
                                cls.log.echo("[-] 语法错误")
                else:
                    return func(cls, **kwargs)

            return inner

        return wrapper
