# -*-* coding:UTF-8
import json
import csv


def export_json(path, data):
    """ 输出json文件 """
    with open(path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def export_csv(path, data):
    """ 输出csv文件 """
    with open(path, 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        for source in data:

            writer.writerow(['目标: ' + source['root']])

            for k, v in source['content'].items():
                if not v:
                    continue
                writer.writerow([k])
                if isinstance(v, list):
                    one = v[0]
                    if isinstance(one, dict):
                        field_names = list(one.keys())
                        writer1 = csv.DictWriter(f, fieldnames=field_names)
                        writer1.writeheader()
                        for row in v:
                            writer1.writerow(row)

                    elif isinstance(one, str):
                        for row in v:
                            writer.writerow([row])
                    elif isinstance(one, list):
                        raise Exception('List nested list data')
                elif isinstance(v, dict):
                    field_names = list(v.keys())
                    writer1 = csv.DictWriter(f, fieldnames=field_names)
                    writer1.writeheader()
                    writer1.writerow(v)
                    writer1.writerow({})
