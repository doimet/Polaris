# -*-* coding:UTF-8
import json


class OutputModule:

    def __init__(self, export_path, source_data):
        self.export_path = export_path
        self.source_data = source_data

    def export_json(self):
        """ 生成json文件 """
        with open(self.export_path, "w", encoding='utf-8') as f:
            json.dump(self.source_data, f, indent=4, ensure_ascii=False)

    def export_md(self):
        """ 生成md文件 """
        ...
