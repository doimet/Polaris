# -*-* coding:UTF-8
import json
import csv
import xlwt


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

    def export_txt(self):
        """ 生成txt文件 """
        ...

    def export_csv(self):
        """ 生成csv文件 """
        with open(self.export_path, newline='', encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # writer.writerow(columns)
            # for num, key in enumerate(data["results"]):
            #     writer.writerow([str(num + 1), key[0], key[1], key[2], key[3], key[4], key[5], key[6]])
