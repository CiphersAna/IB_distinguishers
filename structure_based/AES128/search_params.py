#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

def space():
    search_space = []
    for i in range(0, 4):
        for j in range(0, 4):
            b = [[0 for jj in range(0, 4)] for ii in range(0, 4)]
            b[i][j] = 1
            search_space.append(b)
    return search_space

def trunc1word_search_space():
    search_space = []
    #b = [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    #e0 = [[0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]]
    #e1 = [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    #search_space = [[b, b, e0, e1]]
    for b in space():
        for e0 in space():
            for e1 in space():
                search_space.append(copy.deepcopy([b, b, e0, e1]))
    return search_space

def search_param_trunc1word():
    param = dict()
    param["type"] = "trunc1word search space"
    param["thread_num"] = 1
    param["search_space"] = trunc1word_search_space()
    return param
