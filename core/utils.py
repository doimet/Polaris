import os
import re
import json
import base64 as b64
import random
import string


def build_random_str(length=8):

    """ 随机字符串 """

    return ''.join(random.sample(string.ascii_letters, length))


def build_random_lower_str(length=8):
    """ 随机小写字符串 """

    return ''.join(random.sample(string.ascii_lowercase, length))


randomLowercase = build_random_lower_str


def build_random_upper_str(length=8):
    """ 随机大写字符串 """

    return ''.join(random.sample(string.ascii_uppercase, length))


randomUppercase = build_random_upper_str


def build_random_int(min_length=8, max_length=16):

    """ 随机整数 """

    return random.randint(min_length, max_length)


randomInt = build_random_int


base64 = b64.b64encode


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
