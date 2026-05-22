#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

def check_zero(x):
    flag = True
    for i in range(0, 4):
        y = x[i] ^ x[i + 4] ^ x[i + 8]
        if y != 0:
            flag = False
            break
    return flag

def lfsr_forward(x):
    x0 = [x[0], x[1], x[2], x[3]]
    x1 = [x[4], x[5], x[6], x[7]]
    x2 = [x[8], x[9], x[10], x[11]]

    xx0 = x0
    xx1 = [x1[3] ^ x1[2], x1[0], x1[1], x1[2]]
    xx2 = [x2[1], x2[2], x2[3], x2[0] ^ x2[3]]

    y = xx0 + xx1 + xx2

    return y

def v_forward():
    s = []
    for v in range(0, 4096):
        x0 = [((v >> i) & 0x1) for i in range(0, 12)]
        x1 = lfsr_forward(x0)
        x2 = lfsr_forward(x1)
        if check_zero(x0) and check_zero(x1):
            s.append(x2)
    return s

def lfsr_backward(x):
    x0 = [x[0], x[1], x[2], x[3]]
    x1 = [x[4], x[5], x[6], x[7]]
    x2 = [x[8], x[9], x[10], x[11]]

    xx0 = x0
    xx1 = [x1[1], x1[2], x1[3], x1[0] ^ x1[3]]
    xx2 = [x2[2] ^ x2[3], x2[0], x2[1], x2[2]]

    y = xx0 + xx1 + xx2

    return y

def v_backward():
    s = []
    for v in range(0, 4096):
        x0 = [((v >> i) & 0x1) for i in range(0, 12)]
        x1 = lfsr_backward(x0)
        x2 = lfsr_backward(x1)
        if check_zero(x0) and check_zero(x1):
            s.append(x2)
    return s

def derive_rk(x):
    y = [[[0 for kk in range(0, 4)] for jj in range(0, 4)] for ii in range(0, 4)]
    for i in range(0, 2):
        for j in range(0, 4):
            if len(x[i][j]) != 0:
                for k in range(0, 4):
                    y[i][j][k] = x[i][j][k] ^ x[i][j][k + 4] ^ x[i][j][k + 8]
    return y

def propagation_forward1r(x):
    y = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
    pt = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    xx = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
    for i in range(0, 2):
        for j in range(0, 4):
            if len(x[i][j]) != 0:
                xx[i][j] = lfsr_forward(x[i][j])
    for i in range(2, 4):
        for j in range(0, 4):
            xx[i][j] = x[i][j]
    for i in range(0, 16):
        j = pt[i]
        y[i // 4][i % 4] = xx[j // 4][j % 4]
    return y

def propagation_forward(x, rounds):
    y = copy.deepcopy(x)
    rks = []
    for r in range(0, rounds):
        rk = derive_rk(y)
        rks.append(copy.deepcopy(rk))
        y = copy.deepcopy(propagation_forward1r(y))
    return rks

def sp_forward(rounds):
    sp = []
    for i in range(0, 2):
        for j in range(0, 4):
            for v in v_forward():
                x = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
                x[i][j] = v
                rks = propagation_forward(x, rounds)
                sp.append(copy.deepcopy(rks))
    return sp

def propagation_backward1r(x):
    y = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
    pt = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    xx = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
    for i in range(0, 2):
        for j in range(0, 4):
            if len(x[i][j]) != 0:
                xx[i][j] = lfsr_backward(x[i][j])
    for i in range(2, 4):
        for j in range(0, 4):
            xx[i][j] = x[i][j]
    for i in range(0, 16):
        j = pt[i]
        y[j // 4][j % 4] = xx[i // 4][i % 4]
    return y

def propagation_backward(x, rounds):
    y = copy.deepcopy(x)
    rks = [[] for ii in range(0, rounds)]
    for r in range(0, rounds):
        rk = derive_rk(y)
        rks[rounds - 1 - r] = copy.deepcopy(rk)
        y = copy.deepcopy(propagation_backward1r(y))
    return rks

def sp_backward(rounds):
    sp = []
    for i in range(0, 2):
        for j in range(0, 4):
            for v in v_backward():
                x = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
                x[i][j] = v
                rks = propagation_backward(x, rounds)
                sp.append(copy.deepcopy(rks))
    return sp

def extend_ks(kv):
    y = []
    for v in kv:
        y.append([v, v])
    return y

def bit_search_space(rounds):
    zero = [[[0 for kk in range(0, 4)] for jj in range(0, 4)] for ii in range(0, 4)]
    search_space = []

    bks = sp_forward(rounds)
    eks = sp_backward(rounds)

    for bk in bks:
        for ek in eks:
            search_space.append(copy.deepcopy([[zero, zero], [zero, zero], extend_ks(bk), extend_ks(ek)]))

    return search_space

def search_param_bit(rounds):
    param = dict()
    param["type"] = "bit search space"
    param["thread_num"] = 1
    param["search_space"] = bit_search_space(rounds)
    return param
