# -*-* coding:UTF-8
import os
import sys
import time
import yaml
import threading
import importlib
import functools
from pathlib import Path
from core.request import Request
from urllib.parse import urlparse
from core.base import PluginBase, PluginObject, Logging, YamlPoc
from core.common import get_table_form
from core.common import merge_same_data, keep_data_format
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED


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
            target_list = self.data_handle(self.dataset)
            self.dataset = []
        elif 'input' in self.options.keys():
            target_list = self.options.pop('input')
        else:
            return

        for target_tuple in target_list:
            self.log.root(f"Target: {target_tuple[1]}")
            threading.Thread(target=self.on_monitor, daemon=True).start()
            status, message = self.check_target(*target_tuple)
            if status:
                content = self.job_execute(target_tuple)
                if content:
                    self.dataset.append({'root': target_tuple[1], 'content': {self.options['command']: content}})
            else:
                self.log.error(message)

    def shows(self, att=None):
        """ 获取插件列表 """
        show_list = []
        base_path = os.path.join('plugins', self.options['command'])
        if 'input' in self.options.keys() and self.options['input']:
            att = self.options['input'][0][0]
        for file_path, file_name, file_ext in self.get_plugin_list(base_path, self.options['plugin'], att):
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
                match_result = self.search_plugin_object(base_path, self.options['plugin'], target_tuple)
                obj, prompt = match_result[0][2], self.options['plugin'][0]
            else:
                obj, prompt = None, 'localhost'

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
                        self.log.warn('Not Found Plugin')
                elif command == 'use':
                    self.options['plugin'] = (args[0],)
                    match_result = self.search_plugin_object(base_path, self.options['plugin'], target_tuple)
                    if len(match_result) == 1:
                        obj, prompt = match_result[0][2], match_result[0][1]
                    elif len(match_result) > 1:
                        obj, prompt = None, match_result[0][0].replace('\\', '-')
                        self.log.info(f'Found Plugin: {"、".join([_[1] for _ in match_result])}')
                    else:
                        self.log.warn('Not Found Plugin')
                elif command in ['info']:
                    if obj:
                        self.log.info('插件方法:')
                        custom_method = {}
                        for func_name in obj.__decorate__:
                            desc = getattr(obj, func_name)(FLAG=True)
                            custom_method[func_name] = desc
                        tb = get_table_form([custom_method], layout='vertical', title=['方法', '描述'], rank=False)
                        self.log.echo(tb)
                    else:
                        self.log.warn('Not Found Plugin')
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
                        match_result = self.search_plugin_object(base_path, self.options['plugin'], target_tuple)
                        for plugin_path, plugin_name, plugin_object in match_result:
                            if target_tuple[0] not in dir(plugin_object):
                                continue
                            self.job_total += 1
                            future = executor.submit(self.job_func, plugin_name, target_tuple, plugin_object)
                            future.add_done_callback(self.on_finish)
                            task_list.append(future)

                        cache.add(target_tuple)
                    wait(task_list, return_when=ALL_COMPLETED)
                    for future in as_completed(task_list):
                        result.append(future.result())
                    taskset = self.data_handle(result)
                    depth -= 1
            result = self.final_handle(result)
            data = keep_data_format(merge_same_data(result, {}))
            return data

    def final_handle(self, data):
        """ 提取网段 ip """
        ip_list = []
        res = self.extract_data('ip', data, [])
        for ip in (res or []):
            ip_list.append(ip)
        if ip_list:
            # segment_list = merge_ip_segment(ip_list)
            # if segment_list:
            #     data.append({'网段信息': segment_list})
            pass
        return data

    def data_handle(self, data):
        """ 数据处理 """
        target_list = []
        for subdomain in self.extract_data('subdomain', data, []):
            target_list.append(('url', 'http://{}'.format(subdomain)))
        for url in self.extract_data('url', data, []):
            target_list.append(('url', url))
        return target_list

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

    @staticmethod
    def check_target(key, value):
        """
        检测目标指标:
        1.检测目标是否存活
        """
        return True, ''
        if key == 'url':
            try:
                request = Request({}, {})
                request.request(method="get", url=value, timeout=15)
            except Exception as e:
                return False, 'the target cannot access'
        return True, 'access normal'

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
            if all(map(lambda x: isinstance(x, dict) or isinstance(x, list), data.values())):
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
        time.sleep(0.1)
        try:
            if plugin_name in self.config.keys():
                if self.config[plugin_name].get('enable', False):
                    """ 指定插件时 判断插件是否被禁用 并打印提示 """
                    raise Exception(f'The plug-in is disabled')
            if plugin_object.__condition__():
                data = getattr(plugin_object, target_tuple[0])()
                return data
            else:
                self.log.debug(f'指纹不匹配 (plugin:{plugin_name})')
        except Exception as e:
            self.log.warn(f'{str(e)} (plugin:{plugin_name})')

    def on_finish(self, worker):
        with self.metux:
            self.job_count += 1
            thread = threading.current_thread()
            self.last_job = thread.name
            data = merge_same_data(worker.result(), {})
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
        match_result = []
        for file_path, file_name, file_ext in self.get_plugin_list(base_path, plugin_name, target[0]):
            plugin_class = self.get_plugin_object(os.path.join(file_path, file_name + file_ext))
            target_dict = {'key': target[0], 'value': target[1], 'ip': '', 'port': '', 'url': '', 'host': ''}
            if 'http://' in target[1] or 'https://' in target[1]:
                url_obj = urlparse(target[1])
                target_dict.update(
                    {
                        'url': f'{url_obj.scheme}://{url_obj.hostname}',
                        'scheme': url_obj.scheme,
                        'host': url_obj.netloc,
                        'ip': url_obj.hostname,
                        'port': url_obj.port if url_obj.port else (443 if url_obj.scheme == 'https' else 80)
                    }
                )
            plugin_object = plugin_class(
                self.options,
                self.config,
                target_dict,
                self.event,
                self.threshold
            )
            match_result.append((file_path, file_name, plugin_object))
        return match_result

    @staticmethod
    def list_path_file(path):
        """ 获取目录下所有文件 """
        for root, dir_name, filenames in os.walk(path):
            for filename in filenames:
                yield root, filename

    def get_plugin_list(self, path: str, names: tuple, att=None):
        """ 获取插件列表 """
        is_exclude = all([True if _[0] == '!' else False for _ in names])  # 过滤插件前置判断

        res = set()
        for file_path, filename in self.list_path_file(path):
            file_stem, file_ext = Path(filename).stem, Path(filename).suffix
            if file_ext in ['.py', '.yml'] and not filename.startswith('_'):
                plugin_obj = self.get_plugin_object(os.path.join(file_path, filename))
                if att and att not in dir(plugin_obj):
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
                'description': '',
                'references': content['detail'].get('links', []),
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
