# -*-* coding:UTF-8
import json


def export_json(path, data):
    """ 输出json文件 """
    with open(path, "w", encoding='utf-8') as f:
        json.dump([_ for _ in data], f, indent=4, ensure_ascii=False)


def export_md(path, data):
    """ 输出Markdown文档 """
    with open(path, 'w', encoding='utf-8') as f:
        for one in data:
            # 写入一级标题
            f.write(f'# {one["root"]}\n')
            for second_title, second_content in one['content'].items():
                # 写入二级标题
                f.write(f'## {second_title}\n')
                for third_title, third_content in second_content.items():
                    # 写入三级标题
                    f.write(f'### {third_title}\n')
                    # 写入三级内容
                    if isinstance(third_content, str):
                        f.write(f'{third_content}\n')
                    elif isinstance(third_content, dict):
                        content = []
                        for k, v in third_content.items():
                            if k == 'image':
                                content.append(f'![Image]({v})   ')
                            else:
                                content.append(f'{k}: {v}   ')
                        f.write('\n'.join(content) + '\n')
                    elif isinstance(third_content, list):
                        if len(third_content) == 0:
                            continue
                        example = third_content[0]
                        if isinstance(example, str):
                            content = "\n".join(["+ " + _ for _ in third_content])
                            f.write(content + '\n')
                        elif isinstance(example, dict):
                            table_title = list(example.keys())
                            f.write(f'| {" | ".join([_ for _ in table_title])} |\n')
                            f.write(f'| {" | ".join([" :----: " for _ in range(len(table_title))])} |\n')
                            for row in third_content:
                                f.write(f'| {" | ".join([_ for _ in row.values()])} |\n')
