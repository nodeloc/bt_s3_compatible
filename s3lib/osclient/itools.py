#!/usr/bin/python
# coding: utf-8
from __future__ import division
"""TOOLS"""
import os
import platform
import string
import sys
import time
from datetime import datetime
import random

PROGRESS_FILE_NAME = "PROGRESS_FILE_NAME"

_ver = sys.version_info
#: Python 2.x?
is_py2 = (_ver[0] == 2)

#: Python 3.x?
is_py3 = (_ver[0] == 3)


if is_py2:
    import StringIO
    StringIO = BytesIO = StringIO.StringIO

    builtin_str = str
    bytes = str
    str = unicode  # noqa
    basestring = basestring  # noqa
    numeric_types = (int, long, float)  # noqa

    def b(data):
        return bytes(data)

    def s(data):
        return bytes(data)

    def u(data):
        return unicode(data, 'unicode_escape')  # noqa

elif is_py3:
    import io
    StringIO = io.StringIO
    BytesIO = io.BytesIO

    builtin_str = str
    str = str
    bytes = bytes
    basestring = (str, bytes)
    numeric_types = (int, float)

    def b(data):
        if isinstance(data, str):
            return data.encode('utf-8')
        return data

    def s(data):
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return data

    def u(data):
        return data


def report_progress(consumed_bytes, total_bytes):
    """上传进度回调函数

    本函数依赖系统环境变量 PROGRESS_FILE_NAME 所指定的文件，进度信息会写入到该文件当中
    进度格式:
    上传百分比|速度(Mb/s)|时间(s)|上传字节|总字节|开始时间戳
    :param consumed_bytes: 已上传字节数
    :param total_bytes: 总字节数
    """
    import public
    p_file = os.environ[PROGRESS_FILE_NAME]
    rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
    if consumed_bytes == 0:
        start_time = time.time()
    else:
        p_text = public.readFile(p_file)
        if not p_text:
            return
        start_time = float(p_text.split("|")[-1])
    now = time.time()
    diff = round(now - start_time, 2)
    speed = round(consumed_bytes / diff / 1024 / 1024, 2) if diff > 0 else 0
    progress_text = "{0}%|{1}Mb/s|{2}|{3}|{4}|{5}".format(
        rate, speed, diff, consumed_bytes, total_bytes, start_time
    )
    if consumed_bytes == total_bytes:
        progress_text += "\n"
    public.writeFile(p_file, progress_text)
    sys.stdout.write("\r" + progress_text)
    sys.stdout.flush()


def percentage(consumed_bytes, total_bytes):
    """命令行进度回调

    :param consumed_bytes:
    :param total_bytes:
    :return:
    """
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        display_consumed = round(consumed_bytes / 1024 / 1024, 2)
        display_total = round(total_bytes / 1024 / 1024, 2)
        progress_text = '{0}%|{1}M|{2}M'.format(
            rate, display_consumed, display_total)
        sys.stdout.write("\r" + progress_text)
        sys.stdout.flush()


def process_param_value(text):
    """尝试把字符形式的值类型转换成相应的正确类型

    转换类型有：
    1.有小数点的数值转换成float,其他转换成int。
    2.bool类型字符串转为bool。
    :param text: 参数值文本
    :return:
    """
    try:
        if text:
            if text.lower() == "true":
                return True
            if text.lower() == "false":
                return False

            if text.find(".") > 0:
                return float(text)
            else:
                return int(text)
    except:
        pass
    return text


def parse_params(param_list):
    """归类脚本传入的位置参数和关键字参数

    注意：算术表达式会被看成是字符串。比如: part_size=1024*1024，part_size的值会被赋值为
    字符串"1024*1024"，而不是乘法运算结果。直接传入算术值，避免出现错误。
    :type param_list: str
    :param param_list:
        Example:
            script.py download name=linxiao age=30 job=dev
        param_list:
            [download name=linxiao age=30 job=dev]
    :return: {args: [], kwargs: {}}
    """

    args = []
    kwargs = {}
    for arg in param_list:
        equal_index = arg.find("=")
        if equal_index < 0:
            args.append(process_param_value(arg))
        else:
            key = arg[:equal_index]
            value = process_param_value(arg[equal_index + 1:])
            kwargs.update({key: value})
    return {"args": args, "kwargs": kwargs}


def switch_environment():
    """切换到插件执行路径"""
    import os
    sysstr = platform.system().lower()
    if sysstr == "linux":
        os.chdir("/www/server/panel")
    else:
        raise RuntimeError("未知运行环境。")
    sys.path.insert(0, "class/")


def get_text_timestamp():
    import time
    timestamp = time.time()
    text = "" + repr(timestamp)
    text = text.replace(".", "")
    return text


def generate_random_str():
    text = get_text_timestamp()
    rand_text = "".join(random.sample(string.ascii_letters, 5))
    rand_text = text + rand_text
    return rand_text
