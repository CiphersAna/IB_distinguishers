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

    sbox = [0xc, 0x6, 0x9, 0x0, 0x1, 0xa, 0x2, 0xb, 0x3, 0x8, 0x5, 0xd, 0x4, 0xe, 0x7, 0xf]

    s = hex2binstr(sbox[0], 4)
    for i in range(1, len(sbox)):
        in_value = hex2binstr(i, 4)
        out_value = hex2binstr(sbox[i], 4)
        s = "(IF {} = {} THEN {} ELSE {} ENDIF)".format(xx, in_value, out_value, s)
    s = ["{} = {}".format(yy, s)]
    return s

def sbox_layer(x, y):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            xi = [x[i][j][0], x[i][j][1], x[i][j][2], x[i][j][3]]
            yi = [y[i][j][0], y[i][j][1], y[i][j][2], y[i][j][3]]
            statement += sbox_single(xi, yi)
    return statement

def sbox_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += sbox_layer(x[i], y[i])
    return statement

def xor2_layer(x, y, z):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                s = "{} = BVXOR({}, {})".format(z[i][j][k], x[i][j][k], y[i][j][k])
                statement.append(s)
    return statement

def xor2_layer_mfold(x, y, z, m):
    statement = []
    for i in range(0, m):
        statement += xor2_layer(x[i], y[i], z[i])
    return statement

def sc_layer(x):
    y = [[[] for jj in range(0, 4)] for ii in range(0, 4)]
    for i in range(0, 4):
        for j in range(0, 4):
            y[i][j] = x[i][(j - i) % 4]
    return y

def sc_layer_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(sc_layer(x[i]))
    return y

def __mc_layer(x, y):
    # mat = [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]]
    statement = []
    statement.append("{} = BVXOR(BVXOR({}, {}), {})".format(y[0], x[0], x[2], x[3]))
    statement.append("{} = {}".format(y[1], x[0]))
    statement.append("{} = BVXOR({}, {})".format(y[2], x[1], x[2]))
    statement.append("{} = BVXOR({}, {})".format(y[3], x[0], x[2]))
    return statement

def mc_layer(x, y):
    mat = [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]]
    statement = []
    for j in range(0, 4):
        for k in range(0, 4):
            mi = [x[0][j][k], x[1][j][k], x[2][j][k], x[3][j][k]]
            mo = [y[0][j][k], y[1][j][k], y[2][j][k], y[3][j][k]]
            statement += __mc_layer(mi, mo)
    return statement

def mc_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += mc_layer(x[i], y[i])
    return statement

def var_declare(var_name, r):
    return [[["{}_{}_{}_{}_{}".format(var_name, r, i, j, k) for k in range(0, 4)] for j in range(0, 4)] for i in range(0, 4)]

def var_declare_mfold(var_name, r, m):
    v = []
    for i in range(0, m):
        v.append(var_declare("{}{}".format(var_name, i), r))
    return v

def header(all_var):
    statement = ""
    for var in all_var:
        for l in range(0, len(var)):
            v = []
            for i in range(0, 4):
                for j in range(0, 4):
                    v += var[l][i][j]
            substatement = ", ".join(v)
            statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def set_diff_in(x, b):
    statement = []
    hm = len(b)
    for t in range(0, hm):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 4):
                    statement.append("BVXOR({}, {}) = 0bin{}".format(x[2 * t][i][j][k], x[2 * t + 1][i][j][k], b[t][i][j][k]))
    return statement

def set_diff_out(x, e):
    statement = []
    hm = len(e)
    for t in range(0, hm):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 4):
                    statement.append("BVXOR({}, {}) = 0bin{}".format(x[2 * t + 1][i][j][k], x[(2 * t + 2) % (2 * hm)][i][j][k], e[t][i][j][k]))
    return statement

def set_diff_kin(x, b):
    statement = []
    hm = len(b)
    for t in range(0, hm):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 4):
                    statement.append("BVXOR({}, {}) = 0bin{}".format(x[2 * t][i][j][k], x[2 * t + 1][i][j][k], b[t][i][j][k]))
    return statement

def set_diff_kinr(x, b):
    statement = []
    for i in range(0, len(x)):
        statement += set_diff_kin(x[i], b[i])
    return statement

def set_diff_kout(x, e):
    statement = []
    hm = len(e)
    for t in range(0, hm):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 4):
                    statement.append("BVXOR({}, {}) = 0bin{}".format(x[2 * t + 1][i][j][k], x[(2 * t + 2) % (2 * hm)][i][j][k], e[t][i][j][k]))
    return statement

def set_diff_koutr(x, e):
    statement = []
    for i in range(0, len(x)):
        statement += set_diff_kout(x[i], e[i])
    return statement

def body(r_begin, r_end, b, e, bk, ek, m):
    statement = []
    all_var = []

    key_var = []
    for r in range(r_begin, r_end):
        key_var.append(var_declare_mfold("k", r, m))
    all_var += copy.deepcopy(key_var)

    x = var_declare_mfold("x", r_begin, m)
    all_var.append(copy.deepcopy(x))
    b_var = copy.deepcopy(x)
    for r in range(r_begin, r_end):
        y = var_declare_mfold("y", r, m)
        all_var.append(copy.deepcopy(y))
        statement += sbox_layer_mfold(x, y, m)

        z = var_declare_mfold("z", r, m)
        all_var.append(copy.deepcopy(z))
        statement += xor2_layer_mfold(y, key_var[r - r_begin], z, m)

        sz = sc_layer_mfold(z, m)
        x1 = var_declare_mfold("x", r + 1, m)
        all_var.append(copy.deepcopy(x1))
        statement += mc_layer_mfold(sz, x1, m)

        x = copy.deepcopy(x1)
    e_var = copy.deepcopy(x)

    statement += set_diff_in(b_var, b)
    statement += set_diff_out(e_var, e)

    statement += set_diff_kinr(key_var, bk)
    statement += set_diff_koutr(key_var, ek)

    return statement, all_var

def build_model(r_begin, r_end, b, e, bk, ek, m):
    statement = ""

    bst, all_var = body(r_begin, r_end, b, e, bk, ek, m)

    statement += header(all_var)
    for st in bst:
        statement += "ASSERT({});\n".format(st)
    statement += trailer()
    return statement

def build_model2file(r_begin, r_end, b, e, bk, ek, m, solve_file):
    statement = build_model(r_begin, r_end, b, e, bk, ek, m)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

################################################################

def verify_sbox(x, y):
    sbox = [0xc, 0x6, 0x9, 0x0, 0x1, 0xa, 0x2, 0xb, 0x3, 0x8, 0x5, 0xd, 0x4, 0xe, 0x7, 0xf]
    return True if y == sbox[x] else False

def verify_sbox_layer(x, y):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            if not verify_sbox(x[i][j], y[i][j]):
                flag = False
                break
        if not flag:
            break
    return flag

def verify_sbox_layer_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_sbox_layer(x[i], y[i]):
            flag = False
            break
    return flag

def verify_xor_layer(x, y, z):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            if (z[i][j] != (x[i][j] ^ y[i][j])):
                flag = False
                break
        if not flag:
            break
    return flag

def verify_xor_layer_mfold(x, y, z, m):
    flag = True
    for i in range(0, m):
        if not verify_xor_layer(x[i], y[i], z[i]):
            flag = False
            break
    return flag

def verify_sr_layer(x):
    y = [[0 for jj in range(0, 4)] for ii in range(0, 4)]
    for i in range(0, 4):
        for j in range(0, 4):
            y[i][j] = x[i][(j - i) % 4]
    return y

def verify_sr_layer_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(verify_sr_layer(x[i]))
    return y

def __verify_mc_layer(x, y):
    mat = [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]]
    yy = [0, 0, 0, 0]
    for i in range(0, 4):
        for j in range(0, 4):
            if mat[i][j] == 1:
                yy[i] = yy[i] ^ x[j]
    for i in range(0, 4):
        if yy[i] != y[i]:
            return False
    return True

def verify_mc_layer(x, y):
    flag = True
    for i in range(0, 4):
        xx = [x[0][i], x[1][i], x[2][i], x[3][i]]
        yy = [y[0][i], y[1][i], y[2][i], y[3][i]]
        if not __verify_mc_layer(xx, yy):
            flag = False
            break
    return flag

def verify_mc_layer_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_mc_layer(x[i], y[i]):
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

def get_value(var, value_dict):
    x = [[[0 for k in range(0, 4)] for j in range(0, 4)] for i in range(0, len(var))]
    for i in range(0, len(var)):
        for j in range(0, 4):
            for k in range(0, 4):
                for t in range(0, 4):
                    x[i][j][k] ^= (value_dict[var[i][j][k][t]] << t)
    return x

def verify_solution(res, r_begin, r_end, m):
    value_dict = get_dict(res)

    key_var = []
    for r in range(r_begin, r_end):
        key_var.append(get_value(var_declare_mfold("k", r, m), value_dict))
    x = get_value(var_declare_mfold("x", r_begin, m), value_dict)
    for r in range(r_begin, r_end):
        y = get_value(var_declare_mfold("y", r, m), value_dict)
        flag = verify_sbox_layer_mfold(x, y, m)
        assert(flag)
        z = get_value(var_declare_mfold("z", r, m), value_dict)
        flag = verify_xor_layer_mfold(y, key_var[r - r_begin], z, m)
        assert(flag)
        sz = verify_sr_layer_mfold(z, m)
        x1 = get_value(var_declare_mfold("x", r + 1, m), value_dict)
        flag = verify_mc_layer_mfold(sz, x1, m)
        assert(flag)
        x = copy.deepcopy(x1)
    print("verify suceess")

################################################################

def call_solver(thread_num, solve_file, r_begin, r_end, m):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if (res != "Valid."):
        verify_solution(res, r_begin, r_end, m)
    return True if res == "Valid." else False
