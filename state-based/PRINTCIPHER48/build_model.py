#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess

import bc_description

'''
y = P[x]
'''
def pbox_layer(x):
    pbox = bc_description.get_pbox()
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[pbox[i]] = x[i]
    return y

def xor_layer(x, k, y):
    statement = []
    for i in range(0, len(x)):
        sub = "{} = BVXOR({}, {})".format(y[i], x[i], k[i])
        statement.append(sub)
    return statement

def kp_single(k, x, y):
    kp = bc_description.get_kp()

    kk = "{}@{}".format(k[1], k[0])
    xx0 = "@".join([x[kp[0][4]], x[kp[0][3]], x[kp[0][2]]])
    yy = "@".join([y[2], y[1], y[0]])
    statement_t = "{}".format(xx0)
    for i in range(1, len(kp)):
        xxi = "@".join([x[kp[i][4]], x[kp[i][3]], x[kp[i][2]]])
        statement_t = "(IF {} = 0bin{}{} THEN {} ELSE {} ENDIF)".format(kk, kp[i][1], kp[i][0], xxi, statement_t)
    statement = ["{} = {}".format(yy, statement_t)]
    return statement

def kp_layer(k, x, y):
    statement = []
    for i in range(0, 16):
        statement += kp_single(k[(2 * i) : (2 * i + 2)], x[(3 * i) : (3 * i + 3)], y[(3 * i) : (3 * i + 3)])
    return statement

def hex2binstr(value):
    return "0bin{}{}{}".format((value >> 2) & 0x1, (value >> 1) & 0x1, (value >> 0) & 0x1)

def sbox_single(x, y):

    sbox = bc_description.get_sbox()

    xx = "@".join([x[2], x[1], x[0]])
    yy = "@".join([y[2], y[1], y[0]])

    statement_t = hex2binstr(sbox[0])
    for i in range(1, len(sbox)):
        in_value = hex2binstr(i)
        out_value = hex2binstr(sbox[i])
        statement_t = "(IF {} = {} THEN {} ELSE {} ENDIF)".format(xx, in_value, out_value, statement_t)
    statement = ["{} = {}".format(yy, statement_t)]
    return statement

def sbox_layer(x, y):
    statement = []
    for i in range(0, 16):
        statement += sbox_single(x[(3 * i) : (3 * i + 3)], y[(3 * i) : (3 * i + 3)])
    return statement

def xor_cons_layer(x, y, r):
    statement = []
    rc = bc_description.get_rc()
    rcr = rc[r + 1]
    for i in range(0, 6):
        statement.append("{} = BVXOR({}, 0bin{})".format(y[i], x[i], rcr[i]))
    for i in range(6, 48):
        statement.append("{} = {}".format(y[i], x[i]))
    return statement

'''
Support operation:
    pbox
    xor
    kp
    sbox
    xor_cons
'''
def pbox_layer_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(pbox_layer(x[i]))
    return y

def xor_layer_mfold(x, k, y, m):
    statement = []
    for i in range(0, m):
        statement += xor_layer(x[i], k[i], y[i])
    return statement

def kp_layer_mfold(k, x, y, m):
    statement = []
    for i in range(0, m):
        statement += kp_layer(k[i], x[i], y[i])
    return statement

def sbox_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += sbox_layer(x[i], y[i])
    return statement

def xor_cons_layer_mfold(x, y, r, m):
    statement = []
    for i in range(0, m):
        statement += xor_cons_layer(x[i], y[i], r)
    return statement

def var_declare(var_name, r, var_len):
    return ["{}_{}_{}".format(var_name, r, i) for i in range(0, var_len)]

def var_declare_mfold(var_name, r, var_len, m):
    v = []
    for i in range(0, m):
        v.append(var_declare("{}_{}".format(var_name, i), r, var_len))
    return v

def self_eq(var):
    statement = []
    for i in range(1, len(var)):
        for j in range(0, len(var[0])):
            statement.append("{} = {}".format(var[i][j], var[0][j]))
    return statement

def be_value(var0, var1, value):
    statement = []
    for i in range(0, len(value)):
        statement.append("BVXOR({}, {}) = 0bin{}".format(var0[i], var1[i], value[i]))
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

def body(total_round, b, e):
    statement = []
    all_var = []

    k0 = var_declare_mfold("k0", 0, 48, 4)
    k1 = var_declare_mfold("k1", 0, 32, 4)
    all_var.append(k0)
    all_var.append(k1)

    x = var_declare_mfold("x", 0, 48, 4)
    all_var.append(x)
    b_var = copy.deepcopy(x)
    for r in range(0, total_round):
        y = var_declare_mfold("y", r, 48, 4)
        all_var.append(y)
        statement += xor_layer_mfold(x, k0, y, 4)
        py = pbox_layer_mfold(y, 4)
        z = var_declare_mfold("z", r, 48, 4)
        all_var.append(z)
        statement += xor_cons_layer_mfold(py, z, r, 4)
        w = var_declare_mfold("w", r, 48, 4)
        all_var.append(w)
        statement += kp_layer_mfold(k1, z, w, 4)
        x1 = var_declare_mfold("x", r + 1, 48, 4)
        all_var.append(x1)
        statement += sbox_layer_mfold(w, x1, 4)
        x = copy.deepcopy(x1)
        e_var = copy.deepcopy(x)

    statement += self_eq(k0)
    statement += self_eq(k1)

    statement += be_value(b_var[0], b_var[1], b[0])
    statement += be_value(b_var[2], b_var[3], b[1])

    statement += be_value(e_var[1], e_var[2], e[0])
    statement += be_value(e_var[0], e_var[3], e[1])

    return statement, all_var

def build_model(total_round, b, e):
    statement = ""

    bst, all_var = body(total_round, b, e)

    statement += header(all_var)
    for st in bst:
        statement += "ASSERT({});\n".format(st)
    statement += trailer()
    return statement

def build_model2file(total_round, b, e, solve_file):
    statement = build_model(total_round, b, e)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

################################################################

def verify_sbox(x, y):
    sbox = [0, 1, 3, 6, 7, 4, 5, 2]
    return True if sbox[x] == y else False

def verify_sbox_layer(x, y):
    flag = True
    for i in range(0, 16):
        if not verify_sbox(x[i], y[i]):
            flag = False
            break
    return flag

def verify_perm(x):
    xx = [0 for i in range(0, 48)]
    yy = [0 for i in range(0, 48)]
    y = [0 for i in range(0, 16)]
    for i in range(0, 16):
        for j in range(0, 3):
            xx[3 * i + j] = (x[i] >> j) & 0x1
    pbox = bc_description.get_pbox()
    flag = True
    for i in range(0, 48):
        yy[pbox[i]] = xx[i]
    for i in range(0, 16):
        for j in range(0, 3):
            y[i] = y[i] ^ (yy[3 * i + j] << j)
    return y

def __verify_key_perm(k, x, y):
    flag = True
    if k[0] == 0 and k[1] == 0:
        if not (y[0] == x[0] and y[1] == x[1] and y[2] == x[2]):
            flag = False
    if k[0] == 1 and k[1] == 0:
        if not (y[0] == x[0] and y[1] == x[2] and y[2] == x[1]):
            flag = False
    if k[0] == 0 and k[1] == 1:
        if not (y[0] == x[1] and y[1] == x[0] and y[2] == x[2]):
            flag = False
    if k[0] == 1 and k[1] == 1:
        if not (y[0] == x[2] and y[1] == x[1] and y[2] == x[0]):
            flag = False
    return flag

def verify_key_perm(k, x, y):
    flag = True
    xx = [0 for i in range(0, 48)]
    yy = [0 for i in range(0, 48)]
    kk = [0 for i in range(0, 32)]

    for i in range(0, 16):
        for j in range(0, 3):
            xx[3 * i + j] = (x[i] >> j) & 0x1
            yy[3 * i + j] = (y[i] >> j) & 0x1
        for j in range(0, 2):
            kk[2 * i + j] = (k[i] >> j) & 0x1

    for i in range(0, 16):
        if not __verify_key_perm(kk[(2 * i) : (2 * i + 2)], xx[(3 * i) : (3 * i + 3)], yy[(3 * i) : (3 * i + 3)]):
            flag = False
            break
    return flag

def verify_xor_key(x, y, k):
    flag = True
    for i in range(0, 16):
        if (x[i] ^ k[i]) != y[i]:
            flag = False
            break
    return flag

def verify_xor_cons(x, y, r):
    rc = bc_description.get_rc()
    cons = rc[r + 1]
    cons0 = (cons[2] << 2) ^ (cons[1] << 1) ^ (cons[0] << 0)
    cons1 = (cons[5] << 2) ^ (cons[4] << 1) ^ (cons[3] << 0)
    flag = True
    for i in range(0, 16):
        if (i == 0) and (y[i] != (x[i] ^ cons0)):
            flag = False
            break
        if (i == 1) and (y[i] != (x[i] ^ cons1)):
            flag = False
            break
        if (i >= 2) and (y[i] != x[i]):
            flag = False
            break
    return flag

def verify_self_eq(x):
    flag = True
    for i in range(1, 4):
        for j in range(0, 16):
            if (x[i][j] != x[0][j]):
                flag = False
                break
        if not flag:
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

def verify_solution(res, total_round):
    value_dict = get_dict(res)

    k0 = get_value(var_declare_mfold("k0", 0, 48, 4), value_dict, 3)
    k1 = get_value(var_declare_mfold("k1", 0, 32, 4), value_dict, 2)

    flag = verify_self_eq(k0)
    assert(flag)
    flag = verify_self_eq(k1)
    assert(flag)

    x = get_value(var_declare_mfold("x", 0, 48, 4), value_dict, 3)
    for r in range(0, total_round):
        y = get_value(var_declare_mfold("y", r, 48, 4), value_dict, 3)
        z = get_value(var_declare_mfold("z", r, 48, 4), value_dict, 3)
        w = get_value(var_declare_mfold("w", r, 48, 4), value_dict, 3)
        x1 = get_value(var_declare_mfold("x", r + 1, 48, 4), value_dict, 3)

        for i in range(0, 4):
            flag = verify_xor_key(x[i], y[i], k0[i])
            assert(flag)
            flag = verify_xor_cons(verify_perm(y[i]), z[i], r)
            assert(flag)
            flag = verify_key_perm(k1[i], z[i], w[i])
            assert(flag)
            flag = verify_sbox_layer(w[i], x1[i])
            assert(flag)
        x = x1
    print("verify suceess")

################################################################

def call_solver(thread_num, solve_file, total_round):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if res != "Valid.":
        verify_solution(res, total_round)

    return True if res == "Valid." else False
