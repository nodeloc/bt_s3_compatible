#!/usr/bin/python
# coding: utf-8
"""自定义异常

author: linxiao
date: 2020/4/22
"""


class OsError(Exception):
    """OS端异常"""


class ObjectNotFound(OsError):
    """对象不存在时抛出的异常"""

    def __init__(self, *args, **kwargs):
        message = "文件对象不存在。"
        super(ObjectNotFound, self).__init__(message, *args, **kwargs)


class ConfigurationError(Exception):
    """配置错误异常"""
