# -*-* coding:UTF-8
import json
import os


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://github.com/StudyCat404/WhatAV"],
        "description": "识别进程中的杀软",
    }

    @cli.options('file', description='进程导出文件路径(需执行的命令tasklist /svc)', default='{self.target.value}')
    def file(self, file) -> dict:
        av_list = []
        with open(file, encoding='utf-8') as f:
            content = f.read()
        with open(os.path.join('data', 'av.json'), encoding='utf-8') as f:
            av_dict = json.load(f)
            for name, value in av_dict.items():
                for process in value['processes']:
                    if process in content:
                        av_list.append({'AvName': name, 'AvUrl': value['url']})
        return {'AvList': av_list}
