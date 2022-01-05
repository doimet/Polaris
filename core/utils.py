import os
import re
import json
import random
import string


def build_random_str(length=8):

    """ 随机字符串 """

    username = ''.join(random.sample(string.ascii_letters, length))
    return username


def build_random_int(length=8):

    """ 随机整数 """

    nickname = ''.join(random.sample(string.ascii_letters + string.digits, length))
    return nickname


def jsonp_to_json(jsonp_str):
    """ jsonp转json """

    return json.loads(re.match(".*?({.*}).*", jsonp_str, re.S).group(1))


def load_file(dict_file):
    """ 加载文件 """
    if os.path.isfile(dict_file):
        file_ext = os.path.splitext(dict_file)[-1]
        with open(dict_file, encoding='utf-8') as f:
            if file_ext == '.json':
                for one in json.load(f):
                    yield one
            else:
                for line in f:
                    yield line.strip()


def build_login_dict(method=1, username='admin', password='admin'):
    """ 构建口令破解字典 """
    if os.path.isfile(username):
        with open(username, encoding='utf-8') as f:
            username_list = [line.strip() for line in f]
    elif isinstance(username, str):
        username_list = username.split(',')
    else:
        raise Exception('username not found!')

    if os.path.isfile(password):
        with open(password, encoding='utf-8') as f:
            password_list = [line.strip() for line in f]
    elif isinstance(password, str):
        password_list = password.split(',')
    else:
        raise Exception('password not found!')

    if method == 0:
        return username_list, password_list
    elif method == 1 and all([isinstance(username_list, list), isinstance(password_list, list)]):
        if len(username_list) != len(password_list):
            raise Exception('单点登录模式: 账密数量不一致')
        for username, password in zip(username_list, password_list):
            yield username, password
    elif method == 2 and all([isinstance(username_list, list), isinstance(password_list, list)]):
        for username in (username_list or ['admin']):
            for password in (password_list or ['admin']):
                yield username, password
    else:
        raise Exception('login method error!')
