#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

def __ptrunc_search_space():
    search_space = []
    for i in range(0, 16):
        for v in range(1, 4):
            b = [0 for ii in range(0, 32)]
            for j in range(0, 2):
                b[2 * i + j] = (v >> j) & 0x1
            search_space.append(copy.deepcopy(b))
    return search_space

def ptrunc_search_space():
    sub_space = __ptrunc_search_space()
    search_space = []
    for b in sub_space:
        for e in sub_space:
            search_space.append(copy.deepcopy([b, b, e, e]))
    return search_space

def search_param_ptrunc():
    param = dict()
    param["type"] = "ptrunc search space"
    param["thread_num"] = 1
    param["search_space"] = ptrunc_search_space()
    return param
