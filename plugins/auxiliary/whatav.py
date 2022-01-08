# -*-* coding:UTF-8
import json
import os


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://github.com/StudyCat404/WhatAV"],
        "description": "执行命令(tasklist /svc), 识别进程中杀软",
        "datetime": "2022-01-09"
    }

    @cli.options('file_path', desc="指定杀软指纹文件", default=os.path.join('data', 'av.json'))
    def file(self, file_path) -> dict:
        av_list = []
        with open(self.target.value, encoding='utf-16') as f:
            content = f.read()
        with open(file_path, encoding='utf-8') as f:
            av_dict = json.load(f)
            for name, value in av_dict.items():
                for process in value['processes']:
                    if process in content:
                        av_list.append({'AvName': name, 'AvUrl': value['url']})

        return {'AvList': av_list}
