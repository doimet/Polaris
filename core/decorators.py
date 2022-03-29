# -*-* coding:UTF-8
import functools
import importlib
from core.common import get_table_form


class Cli:
    def __init__(self):
        self._t_depth = 0
        self._c_depth = 0
        self._temp = None
        self.dataset = None
        self.params = {}

    @staticmethod
    def command(description):
        def wrapper(func):
            def inner(cls, *args, **kwargs):
                if kwargs.get('FLAG', False):
                    return description
                else:
                    return func(cls, *args)

            return inner

        return wrapper

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
            params = {
                'default': None,
                'description': '-',
                'type': str,
                'choice': [],
                'required': False,
                'built-in': False
            }
            params.update(v)
            v = params
            # 参数值校验
            if not all(
                    [
                        isinstance(v['description'], str),
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
                'description': '协程并发数量',
                'type': int,
                'choice': [],
                'required': False,
                'built-in': True
            }

        return kwargs

    def options(self, name='', **attrs):
        self._t_depth += 1

        def wrapper(func):
            def inner(cls, *args, **kwargs):
                self._c_depth += 1
                kwargs.update({name: attrs})
                if self._c_depth == self._t_depth:
                    kwargs = self.kwargs_handle(cls, kwargs)
                    if not cls.options.console:
                        args = tuple([_['default'] for _ in kwargs.values()])
                        return func(cls, *args)

                    self.params = {k: v['default'] for k, v in kwargs.items() if not v['built-in']}

                    cls.log.root(rf'开始进入控制台模式 [?]')
                    cls.log.echo(r"  ____  ____  _      ____  ____  _     _____ ")
                    cls.log.echo(r" /   _\/  _ \/ \  /|/ ___\/  _ \/ \   /  __/ ")
                    cls.log.echo(r" |  /  | / \|| |\ |||    \| / \|| |   |  \   ")
                    cls.log.echo(r" |  \__| \_/|| | \||\___ || \_/|| |_/\|  /_  ")
                    cls.log.echo(r" \____/\____/\_/  \|\____/\____/\____/\____\ ")
                    cls.log.echo("")
                    # if cls.__info__.get('description'):
                    #     cls.log.echo(f" {cls.__info__['description']}\n")
                    # else:
                    #     cls.log.echo(f" 暂无关于此漏洞的描述信息\n")
                    while True:
                        keyword = input(f'\r{150 * " "}\r[{cls.name} \033[0;31m~\033[0m]# ')
                        if keyword in ['quit', 'exit']:
                            break
                        elif keyword in ['help', '?']:
                            cls.log.info('核心命令:')
                            data = [
                                {
                                    'info': '显示参数信息',
                                    'set': '设置插件参数',
                                    'get': '查看插件参数',
                                    'run': '运行插件',
                                    'list': '列出方法',
                                    'quit': '退出程序',
                                    'help': '显示帮助信息',
                                }
                            ]
                            tb = get_table_form(data, layout='vertical', title=['命令', '描述'], rank=False)
                            cls.log.echo(tb)
                        elif keyword in ['info']:
                            variable_list = [
                                {
                                    '参数': k,
                                    '描述': v['description'],
                                    '参数值': v['default'],
                                } for k, v in kwargs.items() if k
                            ]
                            if variable_list:
                                tb = get_table_form(variable_list, rank=False)
                                cls.log.echo(tb)
                        elif keyword == 'list':
                            cls.log.info('内置方法:')
                            temp_function_dict = {}
                            module_object = importlib.import_module("core.utils")
                            for method_name in dir(module_object):
                                if method_name[0] != '_':
                                    class_attr_obj = getattr(module_object, method_name)
                                    if type(class_attr_obj).__name__ == 'function' and class_attr_obj.__doc__:
                                        description = class_attr_obj.__doc__
                                        if any(x.isupper() for x in method_name):
                                            continue
                                        temp_function_dict[description] = method_name

                            if temp_function_dict:
                                function_list = [
                                    {
                                        '方法': v,
                                        '描述': k
                                    } for k, v in temp_function_dict.items()
                                ]
                                tb = get_table_form(function_list, rank=False)
                                cls.log.echo(tb)
                            cls.log.info('自定义方法:')
                            alias_dict = {}
                            for func_name in cls.__decorate__['alias']:
                                desc = getattr(cls, func_name)(FLAG=True)
                                alias_dict[func_name] = desc
                            tb = get_table_form([alias_dict], layout='vertical', title=['方法', '描述'], rank=False)
                            cls.log.echo(tb)
                        elif keyword:
                            match = keyword.split(' ')
                            command = match[0]
                            if command == 'set' and len(match) == 3:
                                param = match[1]
                                value = match[2]
                                if param in kwargs.keys():
                                    convert = kwargs[param]['type']
                                    choice = kwargs[param]['choice']
                                    if len(choice) != 0 and value not in choice:
                                        cls.log.failure(f"invalid choice: {value}. (choose from {', '.join(choice)})")
                                    elif convert not in [str, float, int, bool]:
                                        cls.log.failure(f"unknown type: {convert}")
                                    kwargs[param]['default'] = convert(value)
                                    # 避免源类在多次赋值时被替换
                                    if self._temp:
                                        cls.async_pool = self._temp
                                    else:
                                        self._temp = cls.async_pool
                                    cls.async_pool = functools.partial(cls.async_pool, kwargs['count']['default'])
                                    cls.log.success(f"{param} => {kwargs[param]['default']}")
                                else:
                                    cls.log.failure(f"unknown params: {param}")
                            elif command == 'get' and len(match) == 2:
                                if match[1] in self.params.keys():
                                    cls.log.success(f"{match[1]} => {self.params[match[1]]}")
                                else:
                                    cls.log.failure(f'Not Found {match[1]} Params')
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
                                        # 自定命令扩展
                                        sp_temp = command.split(' ')
                                        if len(sp_temp) == 1:
                                            command, values = sp_temp[0], []
                                        else:
                                            command, values = sp_temp[0], sp_temp[1:]
                                        callback = functools.partial(cls.log.warn, f"unknown usage: {keyword}")
                                        obj = getattr(cls, command.replace('-', '_'), callback)
                                        ctx = functools.partial(obj, *values)
                                        res = ctx(*args)
                                        # 更新设定参数值
                                        for k, v in self.params.items():
                                            kwargs[k]['default'] = v

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
