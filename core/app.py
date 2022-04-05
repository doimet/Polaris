# -*-* coding:UTF-8
import functools
import os
import sys
import time
import yaml
import threading
import importlib
from pathlib import Path
from core.request import Request
from core.base import PluginBase, PluginObject, Logging, YamlPoc
from core.common import get_table_form, merge_ip_segment
from core.common import merge_same_data, keep_data_format
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED, FIRST_EXCEPTION


class Application:

    def __init__(self, config=None, options=None):
        self.log = Logging(level=options['verbose'])
        self.options = options
        self.config = config
        self.dataset = []
        self.job_total = 1
        self.job_count = 0
        self.threshold = {'name': '-', 'count': 0, 'total': 0, 'stop': 0}
        self.last_job = '-'
        self.next_job = '-'
        self.metux = threading.Lock()
        self.event = threading.Event()
        self.event.set()

    def setup(self):
        """ 判断dataset中是否有数据 有数据表示不是第一次运行 需要从dataset中提取数据当输入 """
        if self.dataset:
            target_list = self.build_target(self.dataset)
            self.dataset = []
        else:
            target_list = self.options.pop('input')

        for target_tuple in target_list:
            self.log.root(f"Target: {target_tuple[1]}")
            threading.Thread(target=self.on_monitor, daemon=True).start()
            status, message = self.check_is_live(*target_tuple)
            if status:
                content = self.job_execute(target_tuple)
                if content:
                    self.dataset.append({'root': target_tuple[1], 'content': {self.options['command']: content}})
            else:
                self.log.error(message)

    def shows(self, attribute=None):
        """ 获取插件列表 """
        show_list = []
        base_path = os.path.join('plugins', self.options['command'])
        if 'input' in self.options.keys() and self.options['input']:
            attribute = self.options['input'][0][0]

        for file_path, file_name, file_ext in self.get_plugin_list(base_path, self.options['plugin'], attribute):
            plugin_obj = self.get_plugin_object(os.path.join(file_path, file_name + file_ext))

            plugin_info = plugin_obj.__info__
            plugin_inst = plugin_obj({}, {}, {}, None, {})
            inner_method = plugin_inst.__method__
            decorate_method = plugin_inst.__decorate__
            if self.options['console'] and len(decorate_method) == 0:
                continue

            status = '\033[0;31mDisable\033[0m' if (
                    file_name in self.config.keys() and self.config[file_name].get('enable', False)
            ) else '\033[0;92mEnable\033[0m'
            show_list.append(
                [
                    {
                        '插件': file_name,
                        '名称': plugin_info['name'],
                        '描述': plugin_info['description'],
                        '支持': ','.join(inner_method),
                        '状态': status
                    },
                    {
                        '插件': file_name,
                        '作者': plugin_info['author'],
                        '名称': plugin_info['name'],
                        '描述': plugin_info['description'],
                        '支持': ','.join(inner_method),
                        '来源': ', '.join(plugin_info['references']) if isinstance(plugin_info['references'], list) else
                        plugin_info['references'],
                        '状态': status,
                    }
                ]
            )
        if len(show_list) == 1:
            is_show_detail = True
        else:
            is_show_detail = False

        plugin_list = sorted([_[is_show_detail] for _ in show_list], key=lambda keys: keys['插件'])
        if len(plugin_list) == 0:
            self.log.root(f'Not found {self.options["command"]} plugin')
        else:
            self.log.root(f'List {self.options["command"]} plugin: {len(plugin_list)}')
            table = get_table_form(plugin_list, layout='vertical' if is_show_detail else 'horizontal')
            self.log.child(table)

    def save(self):
        """ 输出处理 """
        if self.dataset:
            dirs, filename = os.path.split(self.options['output'])
            if dirs and not os.path.exists(dirs):
                os.makedirs(dirs)
            file_name, file_ext = os.path.splitext(self.options['output'])
            output_object = importlib.import_module("core.output")

            callback = functools.partial(self.log.critical, 'export file format not support')
            getattr(output_object, 'export_' + file_ext[1:], callback)(self.options['output'], self.dataset)

    def job_execute(self, target_tuple: tuple):
        """ 任务执行器 """

        depth = self.config['general']['depth']
        max_workers = self.config['general']['threads']
        task_list, result, cache, taskset = [], [], set(), [target_tuple]
        base_path = os.path.join('plugins', self.options['command'])
        # 交互/非交互 处理逻辑
        if self.options['console']:
            # 设置日志模式
            self.log.set_mode(1)
            # 暂停消息线程
            self.event.clear()
            self.log.root(rf'开始进入控制台模式 [?]')
            self.log.echo(r"  ____  ____  _      ____  ____  _     _____ ")
            self.log.echo(r" /   _\/  _ \/ \  /|/ ___\/  _ \/ \   /  __/ ")
            self.log.echo(r" |  /  | / \|| |\ |||    \| / \|| |   |  \   ")
            self.log.echo(r" |  \__| \_/|| | \||\___ || \_/|| |_/\|  /_  ")
            self.log.echo(r" \____/\____/\_/  \|\____/\____/\____/\____\ ")
            self.log.echo("")
            if len(self.options['plugin']) == 1:
                prompt = plugin_name = self.options['plugin'][0]
                obj = self.search_plugin_object(base_path, plugin_name, target_tuple)
            else:
                prompt = 'localhost'
                obj = None

            while True:
                keyword = input(f'\r{150 * " "}\r[{prompt} \033[0;31m~\033[0m]# ')
                if not keyword:
                    continue
                sp = keyword.split(' ')
                command, args = (sp[0], []) if len(sp) == 1 else (sp[0], sp[1:])
                if command in ['quit', 'exit']:
                    break
                elif command in ['help', '?']:
                    self.log.info('核心命令:')
                    data = [
                        {
                            'run': '运行插件',
                            'use': '切换插件',
                            'info': '显示信息',
                            'list': '列出方法',
                            'quit': '退出程序',
                            'help': '获取帮助',
                        }
                    ]
                    tb = get_table_form(data, layout='vertical', title=['命令', '描述'], rank=False)
                    self.log.echo(tb)
                elif command in ['run']:
                    if obj:
                        self.event.set()
                        res = getattr(obj, target_tuple[0])()
                        self.event.clear()
                        self.echo_handle(name=prompt, data=res)
                    else:
                        self.log.warn('not found plugin')
                elif command == 'use':
                    obj = self.search_plugin_object(base_path, args[0], target_tuple)
                    if obj:
                        prompt = args[0]
                    else:
                        self.log.warn('not found plugin')
                elif command in ['info']:
                    if obj:
                        obj.log.info('内置方法:')
                        function_dict = {}
                        module_object = importlib.import_module("core.utils")
                        for method_name in dir(module_object):
                            if method_name[0] != '_':
                                class_attr_obj = getattr(module_object, method_name)
                                if type(class_attr_obj).__name__ == 'function' and class_attr_obj.__doc__:
                                    description = class_attr_obj.__doc__
                                    if any(x.isupper() for x in method_name):
                                        continue
                                    function_dict[description] = method_name

                        if function_dict:
                            inner_method = [
                                {
                                    '方法': v,
                                    '描述': k
                                } for k, v in function_dict.items()
                            ]
                            tb = get_table_form(inner_method, rank=False)
                            obj.log.echo(tb)
                        self.log.info('插件方法:')
                        custom_method = {}
                        for func_name in obj.__decorate__:
                            desc = getattr(obj, func_name)(FLAG=True)
                            custom_method[func_name] = desc
                        tb = get_table_form([custom_method], layout='vertical', title=['方法', '描述'], rank=False)
                        self.log.echo(tb)
                    else:
                        self.log.warn('not found plugin')
                elif command in ['list']:
                    self.shows()
                else:
                    # 调用方法并执行
                    callback = functools.partial(self.log.warn, f"unknown usage: {keyword}")
                    res = getattr(obj, command.replace('-', '_'), callback)()
                    if res:
                        self.log.echo(res)
            # 暂停消息线程
            self.event.clear()
            # 恢复日志模式
            self.log.set_mode(0)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                while taskset and depth != 0:
                    for target_tuple in taskset:
                        if target_tuple in cache:
                            continue
                        for file_path, file_name, file_ext in self.get_plugin_list(
                                base_path,
                                self.options['plugin'],
                                target_tuple[0]
                        ):
                            plugin_obj = self.get_plugin_object(os.path.join(file_path, file_name + file_ext))
                            if target_tuple[0] not in dir(plugin_obj):
                                continue
                            self.job_total += 1
                            future = executor.submit(self.job_func, file_name, target_tuple, plugin_obj)
                            future.add_done_callback(self.on_finish)
                            task_list.append(future)
                        cache.add(target_tuple)
                    # wait(task_list, return_when=FIRST_EXCEPTION)
                    # # 反向序列化之前塞入的任务队列，并逐个取消
                    # for task in reversed(task_list):
                    #     task.cancel()
                    wait(task_list, return_when=ALL_COMPLETED)
                    for future in as_completed(task_list):
                        result.append(future.result())
                    taskset = self.build_target(result)
                    depth -= 1
            # result = list(chain(*list(filter(lambda x: x is not None, result))))
            result = self.final_handle(result)
            data = keep_data_format(merge_same_data(result, len(result), {}))
            return data

    def final_handle(self, data):
        """ 提取网段 ip """
        ip_list = []
        res = self.extract_data('ip', data, [])
        for ip in (res or []):
            ip_list.append(ip)
        if ip_list:
            segment_list = merge_ip_segment(ip_list)
            if segment_list:
                data.append({'网段信息': segment_list})
        return data

    def build_target(self, data):
        """ 生成目标 """
        for subdomain in self.extract_data('subdomain', data, []):
            yield 'url', 'http://{}'.format(subdomain)

    def extract_data(self, key, data, res=None):
        """提取数据 """
        if isinstance(data, str) or isinstance(data, int):
            return
        elif isinstance(data, list):
            for one in data:
                self.extract_data(key, one, res)
        elif isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    res.append(v)
                    continue
                self.extract_data(key, v, res)
        return res

    def check_is_live(self, _key, _value):
        return True, ''
        """
        检测目标指标:
        1.检测目标是否存活
        2.检测目标是否是蜜罐
        """
        if _key == 'url':
            request = Request({}, {})
            try:
                r = request.request(method="get", url=_value, timeout=15)
                if self.check_is_honeypot(r.text):
                    return False, 'the target is honeypot'
            except Exception as e:
                return False, 'the target cannot access'
        return True, 'access normal'

    def check_is_honeypot(self, content):
        """ 简单蜜罐检测 后续需要优化 """
        code_list = [
            """
windows--2017
write = system,call,log,verbose,command,agent,user,originate
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
},
荣耀立方
-->
</p>
</body></html>
            """,
            """
WWW-Authenticate: Basic realm="NETGEAR DGN2200"
            """,
            """
var TAB_CODE=9
var DEL_CODE=46
var BS_CODE=8
            """,
            """
 <title>Openfire Admin Console</title>
 <title>Openfire Console d'Administration: Configuration du Serveur</title>
 <title>Openfire Setup</title>
            """
        ]
        if any([True if _ in content else False for _ in code_list]):
            return True
        return False

    def has_attribute(self, attribute):
        plugin_list = self.get_plugin_list('plugins', self.options['plugin'], attribute)
        for file_path, file_name, file_ext in plugin_list:
            plugin_obj = self.get_plugin_object(os.path.join(file_path, file_name + file_ext))
            if attribute in dir(plugin_obj):
                return True
        return False

    def echo_handle(self, name, data=None, key='result'):
        """ 数据回显处理 """
        if not data:
            return
        if name:
            name = f"({name.replace('(', '').replace(')', '')})"
        if isinstance(data, str) or isinstance(data, int):
            self.log.child(f'{key}: {str(data).strip()} {name}')
        elif isinstance(data, list) and len(data) != 0:
            self.log.child(f'{key}: {len(data)} {name}')
            table = get_table_form(data)
            self.log.child(table)
        elif isinstance(data, dict):
            if not all(map(lambda x: isinstance(x, str) or isinstance(x, int), data.values())):
                for n, (k, v) in enumerate(data.items()):
                    name = f'{name}' if n == 0 else ''
                    self.echo_handle(name=name, data=v, key=k)
            else:
                self.log.child(f'{key}: 1 {name}')
                table = get_table_form(data, layout='vertical')
                self.log.child(table)

    def job_func(self, plugin_name, target_tuple: tuple, plugin_object):
        """ 任务函数 """
        thread_object = threading.current_thread()
        self.next_job = thread_object.name = plugin_name
        try:
            if plugin_name in self.config.keys():
                if self.config[plugin_name].get('enable', False):
                    """ 指定插件时 判断插件是否被禁用 并打印提示 """
                    raise Exception(f'The plug-in is disabled')
            # 开始处理传入插件内的参数
            options = self.options
            # 停止处理传入插件内的参数
            obj = plugin_object(
                options,
                self.config,
                {
                    'key': target_tuple[0],
                    'value': target_tuple[1],
                },
                self.event,
                self.threshold
            )
            data = getattr(obj, target_tuple[0])()
            return data
        except Exception as e:
            self.log.warn(f'{str(e)} (plugin:{plugin_name})')

    def on_finish(self, worker):
        with self.metux:
            self.job_count += 1
            thread = threading.current_thread()
            self.last_job = thread.name
            data = merge_same_data(worker.result(), 1, {})
            # 如进入控制台模式则需跳过此逻辑
            if not self.options['console']:
                self.echo_handle(name=thread.name, data=data)

    def on_monitor(self):
        """ 消息线程 """
        charset = ['\\', '|', '/', '-']
        buffer_length = 0
        while True:
            self.event.wait()
            self.next_job = self.threshold['name']
            text = '\r\033[0;34m[{}]\033[0m {:.2%} - Last Job: {} :: {}'.format(
                charset[int(time.time()) % 4],
                (self.job_count + self.threshold['count']) / (self.job_total + self.threshold['total']),
                self.last_job,
                self.next_job
            )
            place = buffer_length - len(text)
            sys.stdout.write(text + (0, place)[place > 0] * ' ')
            buffer_length = len(text)
            sys.stdout.flush()
            time.sleep(1)

    def search_plugin_object(self, base_path, plugin_name=None, target=None):
        """ 通过插件名称获取插件对象 """
        for file_path, file_name, file_ext in self.get_plugin_list(base_path, (plugin_name, ), target[0]):
            plugin_object = self.get_plugin_object(os.path.join(file_path, file_name + file_ext))
            obj = plugin_object(
                self.options,
                self.config,
                {'key': target[0], 'value': target[1]},
                self.event,
                self.threshold
            )
            return obj

    @staticmethod
    def list_path_file(path):
        """ 获取目录下所有文件 """
        for root, dir_name, filenames in os.walk(path):
            for filename in filenames:
                yield root, filename

    def get_plugin_list(self, path: str, names: tuple, attribute=None):
        """ 获取插件列表 """
        is_exclude = all([True if _[0] == '!' else False for _ in names])  # 过滤插件前置判断

        res = set()
        for file_path, filename in self.list_path_file(path):
            file_stem, file_ext = Path(filename).stem, Path(filename).suffix
            if file_ext in ['.py', '.yml'] and not filename.startswith('_'):
                plugin_obj = self.get_plugin_object(os.path.join(file_path, filename))
                if attribute and attribute not in dir(plugin_obj):
                    continue
                elif names:
                    for plugin in names:
                        if plugin[0] == '!' and file_stem in [plugin[1:] for plugin in names]:
                            continue
                        elif plugin.startswith('@'):
                            callback_func = plugin.strip('@')
                            if callback_func not in dir(plugin_obj):
                                continue
                            else:
                                res.add((file_path, file_stem, file_ext))
                        elif plugin.startswith('%') and plugin.strip('%').lower() in file_stem.lower():
                            res.add((file_path, file_stem, file_ext))
                        elif file_stem.lower() == plugin.lower() or is_exclude:
                            res.add((file_path, file_stem, file_ext))
                        elif plugin.lower() in file_path.lower():
                            res.add((file_path, file_stem, file_ext))
                        else:
                            continue
                else:
                    res.add((file_path, file_stem, file_ext))
        return res

    @staticmethod
    def build_plugin_object():
        """
        1.将utils中的函数转化为插件基类的方法
        2.将decorators中的装饰器方法注册进插件基类
        """
        module_object = importlib.import_module("core.utils")

        for method_name in dir(module_object):
            if method_name[0] != '_':
                class_attr_obj = getattr(module_object, method_name)
                if type(class_attr_obj).__name__ == 'function':
                    setattr(PluginBase, method_name, staticmethod(class_attr_obj))

        module_object = importlib.import_module("core.decorators")

        reg_dict = {'Base': PluginBase}
        for method_name in dir(module_object):
            if method_name[0] != '_':
                class_attr_obj = getattr(module_object, method_name)
                if type(class_attr_obj).__name__ == 'function':
                    reg_dict[method_name] = class_attr_obj
                elif type(class_attr_obj).__name__ == 'type':
                    reg_dict[method_name.lower()] = class_attr_obj()

        plugin_object = PluginObject(reg_dict)
        return plugin_object

    def get_plugin_object(self, file_path):
        """
        1.获取插件对象
        2.更新插件信息
        """
        plugin_object = self.build_plugin_object()
        if file_path.endswith('.yml'):
            plugin = YamlPoc
            with open(file_path, encoding='utf8') as f:
                content = yaml.load(f, Loader=yaml.FullLoader)
            plugin.__info__ = {
                'name': content['name'],
                'author': content['detail'].get('author', ''),
                'references': content['detail'].get('links', []),
                'description': ''
            }
            plugin.__vars__ = content.get('set', {})
            plugin.__rule__ = content['rules']
            plugin.__logic__ = content['expression']
            plugin.__output__ = content.get('output', {})
        else:
            with open(file_path, "rb") as f:
                plugin_code = f.read()
            exec(plugin_code, plugin_object)
            plugin = plugin_object['Plugin']
        plugin.__info__.update({k: v for k, v in PluginBase.__info__.items() if k not in plugin.__info__.keys()})
        return plugin
