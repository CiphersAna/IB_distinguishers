#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import config_search

def s_beta(x):
    ws = config_search.ws
    beta = config_search.beta
    y = [0 for i in range(0, ws)]
    for i in range(0, ws):
        y[(i + beta) % ws] = x[i]
    return y

def small_space():
    ws = config_search.ws
    l31_eq1 = [0 for i in range(0, ws)]
    l31_eq1[ws - 1] = 1
    sl31_eq1 = s_beta(l31_eq1)

    l0 = [0 for i in range(0, 2 * ws)]
    for i in range(0, ws):
        l0[i] = l31_eq1[i] ^ sl31_eq1[i]
        l0[i + ws] = l31_eq1[i]
    l1 = [0 for i in range(0, 2 * ws)]
    for i in range(0, ws):
        l1[i] = l31_eq1[i]
        l1[i + ws] = l31_eq1[i]
    l2 = [0 for i in range(0, 2 * ws)]
    for i in range(0, ws):
        l2[i] = sl31_eq1[i]
        l2[i + ws] = 0

    return [l0, l1, l2]

def bit_search_space():
    sub_space = small_space()
    search_space = []
    b = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    bk = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for e0 in sub_space:
        for e1 in sub_space:
            search_space.append(copy.deepcopy([b, b, e0, e1, bk, bk]))
    return search_space

def search_param_bit():
    param = dict()
    param["type"] = "bit search space"
    param["thread_num"] = 1
    param["search_space"] = bit_search_space()
    return param
