#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy

'''
PRINTcipher48:
    pbox
    rc
    kp
    sbox
'''

def get_pbox():
    b = 48

    pbox = [0 for i in range(0, b)]

    for i in range(0, b - 1):
        pbox[i] = (3 * i) % (b - 1)
    pbox[b - 1] = b - 1

    return pbox

def get_rc():
    total_round = 48
    n = 6

    rc = []

    rc0 = [0 for i in range(0, n)]
    for r in range(0, total_round):

        rc.append(copy.deepcopy(rc0))

        rc1 = [0 for i in range(0, n)]
        for j in range(1, n):
            rc1[j] = rc0[j - 1]
        rc1[0] = 1 ^ rc0[n - 1] ^ rc0[n - 2]
        rc0 = copy.deepcopy(rc1)

    return rc

'''
k0, k1, x0, x1, x2 --> y0, y1, y2
'''
def get_kp():
    kp = [[0, 0, 0, 1, 2], [1, 0, 0, 2, 1], [0, 1, 1, 0, 2], [1, 1, 2, 1, 0]]
    return kp

def get_sbox():
    sbox = [0, 1, 3, 6, 7, 4, 5, 2]
    return sbox
