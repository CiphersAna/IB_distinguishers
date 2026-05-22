#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

def get_pbox():
    b = 48

    pbox = [0 for i in range(0, b)]

    for i in range(0, b - 1):
        pbox[i] = (3 * i) % (b - 1)
    pbox[b - 1] = b - 1

    return pbox

def perm(x):
    pbox = get_pbox()
    y = [0 for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[i] = x[pbox[i]]
    return y

def __gen_search_space():
    search_space = []
    for i in range(0, 48):
        b = [0 for ii in range(0, 48)]
        b[i] = 1
        search_space.append(copy.deepcopy(b))
    return search_space

# aabc abcc bit active search space, size = (48 * 48 * 48)
def gen_search_space():
    sub_space = __gen_search_space()
    search_space = []
    for b0 in sub_space:
        for b1 in sub_space:
            for e in sub_space:
                search_space.append(copy.deepcopy([b0, b1, e, e]))
    for b in sub_space:
        for e0 in sub_space:
            for e1 in sub_space:
                search_space.append(copy.deepcopy([b, b, e0, e1]))
    return search_space

def search_param():
    param = dict()
    param["type"] = "aabc abcc bit active search space"
    param["thread_num"] = 1
    param["search_space"] = gen_search_space()
    return param
