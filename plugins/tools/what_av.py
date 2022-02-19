# -*-* coding:UTF-8
import json
import os


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://github.com/StudyCat404/WhatAV"],
        "description": "识别进程中的杀软",
        "datetime": "2022-01-09"
    }

    @cli.options('file', desc='进程导出文件路径(需执行命令tasklist /svc)', default='{self.target.value}')
    @cli.options('path', desc='杀软识别指纹路径', default=os.path.join('data', 'av.json'))
    def file(self, file, path) -> dict:
        av_list = []
        with open(file, encoding='utf-8') as f:
            content = f.read()
        with open(path, encoding='utf-8') as f:
            av_dict = json.load(f)
            for name, value in av_dict.items():
                for process in value['processes']:
                    if process in content:
                        av_list.append({'AvName': name, 'AvUrl': value['url']})
        return {'AvList': av_list}
