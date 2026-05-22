#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

def pspace():
    search_space = []
    for i in range(0, 1):
        for v in range(1, 16):
            b = [0 for ii in range(0, 64)]
            for j in range(0, 4):
                b[4 * i + j] = (v >> j) & 0x1
            search_space.append(copy.deepcopy(b))
    return search_space

def ptrunc_search_space():
    search_space = []
    for b0 in pspace():
        for b1 in pspace():
            for e0 in pspace():
                for e1 in pspace():
                    search_space.append(copy.deepcopy([[b0, b1], [e0, e1]]))
    return search_space

def search_param_ptrunc():
    param = dict()
    param["type"] = "ptrunc search space"
    param["thread_num"] = 1
    param["search_space"] = ptrunc_search_space()
    return param
