#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import config_search

def ibit_active():
    sp = []
    for i in range(0, 16):
        b = [0 for ii in range(0, 32)]
        b[i + 16] = 1
        sp.append(b)
    return sp

def obit_active():
    sp = []
    for i in range(0, 16):
        e = [0 for ii in range(0, 32)]
        e[i] = 1
        sp.append(e)
    return sp

def bit_search_space():
    search_space = []
    din = ibit_active()
    dout = obit_active()

    for i0 in range(0, len(din)):
        for i1 in range(i0 + 1, len(din)):
            for j0 in range(0, len(dout)):
                for j1 in range(j0 + 1, len(dout)):
                    search_space.append(copy.deepcopy([din[i0], din[i1], dout[j0], dout[j1], [], []]))

    return search_space

def search_param_bit():
    param = dict()
    param["type"] = "bit search space"
    param["thread_num"] = 1
    param["search_space"] = bit_search_space()
    return param
