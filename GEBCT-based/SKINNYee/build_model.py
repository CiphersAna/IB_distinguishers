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

def sbox_gebct(alpha, beta, x, y):
    statement = []
    for i in range(0, 4):
        statement += sbox_single(x[i], y[i])
    for i in range(0, 4):
        statement += ["BVXOR({}, {}) = {}".format(x[0][i], x[1][i], alpha[0][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[1][i], x[2][i], alpha[1][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[2][i], x[3][i], alpha[2][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[0][i], x[3][i], alpha[3][i])]

        statement += ["BVXOR({}, {}) = {}".format(y[0][i], y[1][i], beta[0][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[1][i], y[2][i], beta[1][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[2][i], y[3][i], beta[2][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[0][i], y[3][i], beta[3][i])]
    return statement

def sbox_layer(alpha, beta, x, y):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            alphai = [alpha[0][i][j], alpha[1][i][j], alpha[2][i][j], alpha[3][i][j]]
            betai = [beta[0][i][j], beta[1][i][j], beta[2][i][j], beta[3][i][j]]
            xi = [x[0][i][j], x[1][i][j], x[2][i][j], x[3][i][j]]
            yi = [y[0][i][j], y[1][i][j], y[2][i][j], y[3][i][j]]
            statement += sbox_gebct(alphai, betai, xi, yi)
    return statement

def xor2_layer(alpha, beta, gamma):
    statement = []
    for m in range(0, 4):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 4):
                    s = "{} = BVXOR({}, {})".format(gamma[m][i][j][k], alpha[m][i][j][k], beta[m][i][j][k])
                    statement.append(s)
    return statement

def sc_layer(x):
    y = [[[[] for jj in range(0, 4)] for ii in range(0, 4)] for ll in range(0, 4)]
    for m in range(0, 4):
        for i in range(0, 4):
            for j in range(0, 4):
                y[m][i][j] = x[m][i][(j - i) % 4]
    return y

def __mc_layer(x, y):
    # mat = [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]]
    statement = []
    statement.append("{} = BVXOR(BVXOR({}, {}), {})".format(y[0], x[0], x[2], x[3]))
    statement.append("{} = {}".format(y[1], x[0]))
    statement.append("{} = BVXOR({}, {})".format(y[2], x[1], x[2]))
    statement.append("{} = BVXOR({}, {})".format(y[3], x[0], x[2]))
    return statement

def mc_layer(alpha, beta):
    mat = [[1, 0, 1, 1], [1, 0, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0]]
    statement = []
    for m in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                mi = [alpha[m][0][j][k], alpha[m][1][j][k], alpha[m][2][j][k], alpha[m][3][j][k]]
                mo = [beta[m][0][j][k], beta[m][1][j][k], beta[m][2][j][k], beta[m][3][j][k]]
                statement += __mc_layer(mi, mo)
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

def set_diff_in(alpha, b):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                statement.append("{} = 0bin{}".format(alpha[0][i][j][k], b[0][i][j][k]))
                statement.append("{} = 0bin{}".format(alpha[2][i][j][k], b[1][i][j][k]))
    return statement

def set_diff_out(beta, e):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                statement.append("{} = 0bin{}".format(beta[1][i][j][k], e[0][i][j][k]))
                statement.append("{} = 0bin{}".format(beta[3][i][j][k], e[1][i][j][k]))
    return statement

def set_diff_kin(x, b):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                statement.append("{} = 0bin{}".format(x[0][i][j][k], b[0][i][j][k]))
                statement.append("{} = 0bin{}".format(x[2][i][j][k], b[1][i][j][k]))
    return statement

def set_diff_kinr(x, b):
    statement = []
    for i in range(0, len(x)):
        statement += set_diff_kin(x[i], b[i])
    return statement

def set_diff_kout(x, e):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 4):
                statement.append("{} = 0bin{}".format(x[1][i][j][k], e[0][i][j][k]))
                statement.append("{} = 0bin{}".format(x[3][i][j][k], e[1][i][j][k]))
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

        tx = var_declare_mfold("tx", r, m)
        all_var.append(copy.deepcopy(tx))
        ty = var_declare_mfold("ty", r, m)
        all_var.append(copy.deepcopy(ty))

        statement += sbox_layer(x, y, tx, ty)

        z = var_declare_mfold("z", r, m)
        all_var.append(copy.deepcopy(z))
        statement += xor2_layer(y, key_var[r - r_begin], z)

        sz = sc_layer(z)
        x1 = var_declare_mfold("x", r + 1, m)
        all_var.append(copy.deepcopy(x1))
        statement += mc_layer(sz, x1)

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

def verify_gebct(x, y, tx, ty):
    assert((tx[0] ^ tx[1]) == x[0])
    assert((tx[1] ^ tx[2]) == x[1])
    assert((tx[2] ^ tx[3]) == x[2])
    assert((tx[0] ^ tx[3]) == x[3])

    assert((ty[0] ^ ty[1]) == y[0])
    assert((ty[1] ^ ty[2]) == y[1])
    assert((ty[2] ^ ty[3]) == y[2])
    assert((ty[0] ^ ty[3]) == y[3])
    return verify_sbox(tx[0], ty[0]) and verify_sbox(tx[1], ty[1]) and verify_sbox(tx[2], ty[2]) and verify_sbox(tx[3], ty[3])

def verify_sbox_layer(x, y, tx, ty):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            xx = [x[0][i][j], x[1][i][j], x[2][i][j], x[3][i][j]]
            yy = [y[0][i][j], y[1][i][j], y[2][i][j], y[3][i][j]]
            txx = [tx[0][i][j], tx[1][i][j], tx[2][i][j], tx[3][i][j]]
            tyy = [ty[0][i][j], ty[1][i][j], ty[2][i][j], ty[3][i][j]]
            if not verify_gebct(xx, yy, txx, tyy):
                flag = False
                break
        if not flag:
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
        tx = get_value(var_declare_mfold("tx", r, m), value_dict)
        ty = get_value(var_declare_mfold("ty", r, m), value_dict)
        flag = verify_sbox_layer(x, y, tx, ty)
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
