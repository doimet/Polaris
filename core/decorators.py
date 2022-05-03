# -*-* coding:UTF-8


class Cli:
    def __init__(self):
        self._w_depth = {}
        self._i_depth = {}
        self.params = {}
        self.silent_args = None

    def command(self, description):

        def wrapper(func):
            if func.__name__ in self._w_depth:
                self._w_depth[func.__name__] += 1
            else:
                self._w_depth[func.__name__] = 1

            def inner(cls, *args, **kwargs):
                if func.__name__ in self._i_depth:
                    self._i_depth[func.__name__] += 1
                else:
                    self._i_depth[func.__name__] = 1

                if kwargs.get('FLAG', False):
                    self._i_depth[func.__name__] = self._w_depth[func.__name__]
                    return description
                else:
                    return func(cls, *args)

            inner.__name__ = func.__name__
            return inner

        return wrapper

    @staticmethod
    def kwargs_handle(cls, value):
        """ 输入参数处理 """
        kwargs = {}
        for k, v in value.items():
            params = {
                'default': None,
                'help': '-',
                'type': str,
                'choice': [],
                'required': False,
                'built-in': False,
            }
            params.update(v)
            v = params
            # 参数值校验
            if not all(
                    [
                        isinstance(v['help'], str),
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

        def wrapper(func):
            if func.__name__ in self._w_depth:
                self._w_depth[func.__name__] += 1
            else:
                self._w_depth[func.__name__] = 1

            def inner(cls, *args, **kwargs):
                if func.__name__ in self._i_depth:
                    self._i_depth[func.__name__] += 1
                else:
                    self._i_depth[func.__name__] = 1
                # 方法调用 不产生交互
                if not self.silent_args and args:
                    self.silent_args = args

                kwargs.update({name: attrs})
                if (
                        self._w_depth[func.__name__] != 0 and
                        self._i_depth[func.__name__] % self._w_depth[func.__name__] == 0
                ):
                    if self.silent_args is not None:
                        return func(cls, *self.silent_args)

                    kwargs = self.kwargs_handle(cls, kwargs)
                    for k, v in kwargs.items():
                        while True:
                            default_value = v['default']
                            try:
                                default = f'[默认值 {v["default"]}]' if v["default"] else ''
                                content = input(f'\r\033[0;34m[i]\033[0m {v["help"]}{default}: ')
                            except KeyboardInterrupt:
                                return
                            if content:
                                default_value = content
                            if default_value:
                                default_value = v['type'](default_value)
                            if v['type'] not in [str, float, int, bool]:
                                cls.log.warn(f"unknown type: {str(v['type'])}")
                            elif len(v['choice']) != 0 and not default_value:
                                cls.log.warn(f"invalid choice: {default_value}. (choose from {', '.join([str(_) for _ in v['choice']])})")
                            elif not default_value and v['required']:
                                # 必备参数未传值需异常处理
                                cls.log.warn(f"{k} parameter value is required")
                            else:
                                v['default'] = default_value
                                break
                    args = tuple([_['default'] for _ in kwargs.values()])
                    cls.event.set()
                    result = func(cls, *args)
                    cls.event.clear()
                    return result
                else:
                    return func(cls, **kwargs)

            inner.__name__ = func.__name__
            return inner

        return wrapper


def login_method(func):
    def wrapper(self, username_list, password_list, method=0):
        self.log.debug(f'login method: {method}')
        if method == 1 and all([isinstance(username_list, list), isinstance(password_list, list)]):
            if len(username_list) != len(password_list):
                raise Exception('单点爆破模式: 账密数量不一致')
            for username, password in zip(username_list, password_list):
                res = func(self, username, password)
                if res:
                    self.log.debug(f'login => username: {username}, password: {password} success')
                    return {'username': username, 'password': password}
                self.log.debug(f'login => username: {username}, password: {password} failure')
        elif method == 2 and all([isinstance(username_list, list), isinstance(password_list, list)]):
            for username in (username_list or ['admin']):
                for password in (password_list or ['admin']):
                    res = func(self, username, password)
                    if res:
                        self.log.debug(f'login => username: {username}, password: {password} success')
                        return {'username': username, 'password': password}
                    self.log.debug(f'login => username: {username}, password: {password} failure')
        else:
            raise Exception('login method error!')

    return wrapper
