#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess

def hex2binstr(x, length):
    binstr = "0bin"
    for i in range(0, length):
        binstr += str((x >> (length - 1 - i)) & 0x1)
    return binstr

def sbox_single(x, y):
    xx = "@".join([x[3], x[2], x[1], x[0]])
    yy = "@".join([y[3], y[2], y[1], y[0]])

    sbox = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]

    s = hex2binstr(sbox[0], 4)
    for i in range(1, len(sbox)):
        in_value = hex2binstr(i, 4)
        out_value = hex2binstr(sbox[i], 4)
        s = "(IF {} = {} THEN {} ELSE {} ENDIF)".format(xx, in_value, out_value, s)
    s = ["{} = {}".format(yy, s)]
    return s

def sbox_layer(x, y):
    statement = []
    for i in range(0, 16):
        statement += sbox_single(x[(4 * i) : (4 * i + 4)], y[(4 * i) : (4 * i + 4)])
    return statement


def sbox_layer_mfold(x, y):
    statement = []
    for i in range(0, 4):
        statement += sbox_layer(x[i], y[i])

    return statement

def pbox_layer(x):
    perm = [0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51, \
        4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55, \
        8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59, \
        12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63]
    y = ["" for i in range(0, 64)]
    for i in range(0, 64):
        y[i] = x[perm[i]]
    return y

def pbox_layer_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(pbox_layer(x[i]))
    return y

def xor_layer(x, k, y):
    statement = []
    for i in range(0, len(x)):
        sub = "{} = BVXOR({}, {})".format(y[i], x[i], k[i])
        statement.append(sub)
    return statement

def xor_layer_mfold(x, k, y, m):
    statement = []
    for i in range(0, m):
        statement += xor_layer(x[i], k[i], y[i])
    return statement

def var_declare(var_name, r, var_len):
    return ["{}_{}_{}".format(var_name, r, i) for i in range(0, var_len)]

def var_declare_mfold(var_name, r, var_len, m):
    v = []
    for i in range(0, m):
        v.append(var_declare("{}{}".format(var_name, i), r, var_len))
    return v

def self_eq(var):
    statement = []
    for i in range(0, len(var)):
        for j in range(1, len(var[0])):
            for k in range(0, len(var[0][0])):
                statement.append("{} = {}".format(var[i][0][k], var[i][j][k]))
    return statement

def set_diff_in(x, b):
    statement = []
    for i in range(0, 64):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[0][i], x[1][i], b[0][i]))
    for i in range(0, 64):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[2][i], x[3][i], b[1][i]))
    return statement

def set_diff_out(x, e):
    statement = []
    for i in range(0, 64):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[1][i], x[2][i], e[0][i]))
    for i in range(0, 64):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[0][i], x[3][i], e[1][i]))
    return statement

def header(all_var):
    statement = ""
    for var in all_var:
        for i in range(0, len(var)):
            substatement = ", ".join(var[i])
            statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def body(r_begin, r_end, b, e):
    statement = []
    all_var = []
    key_var = []

    x = var_declare_mfold("x", r_begin, 64, 4)
    all_var.append(x)
    b_var = copy.deepcopy(x)
    for r in range(r_begin, r_end):
        y = var_declare_mfold("y", r, 64, 4)
        all_var.append(y)
        k = var_declare_mfold("k", r, 64, 4)
        all_var.append(k)
        key_var.append(copy.deepcopy(k))
        statement += xor_layer_mfold(x, k, y, 4)

        x1 = var_declare_mfold("x", r + 1, 64, 4)
        all_var.append(x1)
        if r != (r_end - 1):
            statement += sbox_layer_mfold(y, pbox_layer_mfold(x1, 4))
        else:
            statement += sbox_layer_mfold(y, x1)
        x = copy.deepcopy(x1)

    e_var = copy.deepcopy(x)

    statement += self_eq(key_var)

    statement += set_diff_in(b_var, b)
    statement += set_diff_out(e_var, e)

    return statement, all_var

def build_model(r_begin, r_end, b, e):
    statement = ""

    bst, all_var = body(r_begin, r_end, b, e)

    statement += header(all_var)
    for st in bst:
        statement += "ASSERT({});\n".format(st)
    statement += trailer()
    return statement

def build_model2file(r_begin, r_end, b, e, solve_file):
    statement = build_model(r_begin, r_end, b, e)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

################################################################

def verify_sbox(x, y):
    sbox = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]
    return True if sbox[x] == y else False

def verify_sbox_layer(x, y):
    flag = True
    for i in range(0, 16):
        if not verify_sbox(x[i], y[i]):
            flag = False
            break
    return flag

def verify_sbox_layer_mfold(x, y):
    flag = True
    for i in range(0, 4):
        if not verify_sbox_layer(x[i], y[i]):
            flag = False
            break
    return flag

def verify_pbox_layer(x):
    xx = [0 for i in range(0, 64)]
    yy = [0 for i in range(0, 64)]
    y = [0 for i in range(0, 16)]
    for i in range(0, 16):
        for j in range(0, 4):
            xx[4 * i + j] = (x[i] >> j) & 0x1

    perm = [0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51, \
            4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55, \
            8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59, \
            12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63]

    for i in range(0, 64):
        yy[i] = xx[perm[i]]
    for i in range(0, 16):
        for j in range(0, 4):
            y[i] = y[i] ^ (yy[4 * i + j] << j)

    return y

def verify_pbox_layer_mfold(x):
    y = []
    for i in range(0, 4):
        y.append(verify_pbox_layer(x[i]))
    return y

def verify_xor_layer(x, k, y):
    flag = True
    for i in range(0, 16):
        if (x[i] ^ k[i]) != y[i]:
            flag = False
            break
    return flag

def verify_xor_layer_mfold(x, k, y):
    flag = True
    for i in range(0, 4):
        if not verify_xor_layer(x[i], k[i], y[i]):
            flag = False
            break
    return flag

def get_dict(res):
    tmp = res.split(" );\n")
    tmp = tmp[ : -1]
    value_dict = dict()
    for t in tmp:
        t = t.replace("ASSERT( ", "")
        x0, x1 = t.split(" = 0b")
        value_dict[x0] = int(x1)
    return value_dict

def get_value(var, value_dict, l):
    x = [[0 for i in range(0, 16)] for m in range(0, 4)]
    for m in range(0, 4):
        for i in range(0, 16):
            for j in range(0, l):
                x[m][i] = x[m][i] ^ (value_dict[var[m][l * i + j]] << j)
    return x

def verify_solution(res, r_begin, r_end):
    value_dict = get_dict(res)

    x = get_value(var_declare_mfold("x", r_begin, 64, 4), value_dict, 4)
    for r in range(r_begin, r_end):
        y = get_value(var_declare_mfold("y", r, 64, 4), value_dict, 4)
        k = get_value(var_declare_mfold("k", r, 64, 4), value_dict, 4)
        x1 = get_value(var_declare_mfold("x", r + 1, 64, 4), value_dict, 4)

        flag = verify_xor_layer_mfold(x, k, y)
        assert(flag)

        if r != (r_end - 1):
            flag = verify_sbox_layer_mfold(y, verify_pbox_layer_mfold(x1))
            assert(flag)
        else:
            flag = verify_sbox_layer_mfold(y, x1)
            assert(flag)
        x = x1
    print("verify pass")

################################################################

def call_solver(thread_num, solve_file, r_begin, r_end):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if res != "Valid.":
        verify_solution(res, r_begin, r_end)

    return True if res == "Valid." else False
