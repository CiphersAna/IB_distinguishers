#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess
import config_search

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

# left circular shifts
def lcs_layer(x, l):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i + l) % len(x)] = x[i]
    return y

def lcs_layer_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(lcs_layer(x[i], l))
    return y

# right circular shifts
def rcs_layer(x, l):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i - l) % len(x)] = x[i]
    return y

def rcs_layer_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(rcs_layer(x[i], l))
    return y

def reverse_list(x):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[len(x) - 1 - i] = x[i]
    return y

def add_layer(x, y, z):
    xx = "@".join(reverse_list(x))
    yy = "@".join(reverse_list(y))
    zz = "@".join(reverse_list(z))
    ws = config_search.ws

    statement = "{} = BVPLUS({}, {}, {})".format(zz, ws, xx, yy)
    return [statement]

def add_layer_mfold(x, y, z, m):
    statement = []
    for i in range(0, m):
        statement += add_layer(x[i], y[i], z[i])
    return statement

def add_layer_gebct(alpha, beta, gamma, x, y, z):
    statement = []
    for i in range(0, 4):
        statement += add_layer_mfold(x, y, z, 4)
    for i in range(0, len(x[0])):
        statement += ["BVXOR({}, {}) = {}".format(x[0][i], x[1][i], alpha[0][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[1][i], x[2][i], alpha[1][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[2][i], x[3][i], alpha[2][i])]
        statement += ["BVXOR({}, {}) = {}".format(x[0][i], x[3][i], alpha[3][i])]

        statement += ["BVXOR({}, {}) = {}".format(y[0][i], y[1][i], beta[0][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[1][i], y[2][i], beta[1][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[2][i], y[3][i], beta[2][i])]
        statement += ["BVXOR({}, {}) = {}".format(y[0][i], y[3][i], beta[3][i])]

        statement += ["BVXOR({}, {}) = {}".format(z[0][i], z[1][i], gamma[0][i])]
        statement += ["BVXOR({}, {}) = {}".format(z[1][i], z[2][i], gamma[1][i])]
        statement += ["BVXOR({}, {}) = {}".format(z[2][i], z[3][i], gamma[2][i])]
        statement += ["BVXOR({}, {}) = {}".format(z[0][i], z[3][i], gamma[3][i])]
    return statement

def cascade_mfold(x, y, m):
    z = []
    for i in range(0, m):
        z.append(x[i] + y[i])
    return z

def var_declare(var_name, r, var_len):
    return ["{}_{}_{}".format(var_name, r, i) for i in range(0, var_len)]

def var_declare_mfold(var_name, r, var_len, m):
    v = []
    for i in range(0, m):
        v.append(var_declare("{}_{}".format(var_name, i), r, var_len))
    return v

def set_diff_in(x, b):
    statement = []
    bs = config_search.bs
    for i in range(0, bs):
        statement.append("{} = 0bin{}".format(x[0][i], b[0][i]))
    for i in range(0, bs):
        statement.append("{} = 0bin{}".format(x[2][i], b[1][i]))
    return statement

def set_diff_out(x, e):
    statement = []
    bs = config_search.bs
    for i in range(0, bs):
        statement.append("{} = 0bin{}".format(x[1][i], e[0][i]))
    for i in range(0, bs):
        statement.append("{} = 0bin{}".format(x[3][i], e[1][i]))
    return statement

def set_diff_kin(x, b):
    statement = []
    ks = config_search.ks
    for i in range(0, ks):
        statement.append("{} = 0bin{}".format(x[0][i], b[0][i]))
    for i in range(0, ks):
        statement.append("{} = 0bin{}".format(x[2][i], b[1][i]))
    return statement

def set_diff_kout(x):
    statement = []
    ks = config_search.ks
    for i in range(0, ks):
        statement.append("{} = 0bin0".format(x[1][i], x[2][i]))
    for i in range(0, ks):
        statement.append("{} = 0bin0".format(x[3][i], x[3][i]))
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

def gen_round_cons(r, m):
    ws = config_search.ws
    rc = [0 for i in range(0, ws)]
    for i in range(0, ws):
        if ((r >> i) & 0x1) == 1:
            rc[i] = 1
    rc_str = ["0bin{}".format(rc[i]) for i in range(0, ws)]
    return [rc_str for j in range(0, m)]

def get_mk(k0, l0, l1):
    mk = []
    for i in range(0, 4):
        mk.append(k0[i] + l0[i] + l1[i])
    return mk

def key_relation(r_end):
    statement = []
    all_var = []

    ws = config_search.ws
    alpha = config_search.alpha
    beta = config_search.beta

    k0 = var_declare_mfold("k", 0, ws, 4)
    l0 = var_declare_mfold("l", 0, ws, 4)
    l1 = var_declare_mfold("l", 1, ws, 4)
    mk = get_mk(k0, l0, l1)
    all_var += [k0, l0, l1]
    for r in range(0, r_end):
        k1 = var_declare_mfold("k", r + 1, ws, 4)
        l2 = var_declare_mfold("l", r + 2, ws, 4)
        all_var += [k1, l2]
        sl = rcs_layer_mfold(l0, alpha, 4)
        
        tx = var_declare_mfold("ktx", r + 1, ws, 4)
        ty = var_declare_mfold("kty", r + 1, ws, 4)
        tz = var_declare_mfold("ktz", r + 1, ws, 4)
        all_var += [tx, ty, tz]

        statement += add_layer_gebct(k0, sl, l2, tx, ty, tz)
        sk = lcs_layer_mfold(k0, beta, 4)
        statement += xor_layer_mfold(sk, l2, k1, 4)

        k0 = copy.deepcopy(k1)
        l0 = copy.deepcopy(l1)
        l1 = copy.deepcopy(l2)
    return statement, all_var, mk

def body(r_begin, r_end, b, e, bk, ek):
    statement = []
    all_var = []
    ws = config_search.ws
    alpha = config_search.alpha
    beta = config_search.beta

    x = var_declare_mfold("x", r_begin, ws, 4)
    all_var.append(x)
    y = var_declare_mfold("y", r_begin, ws, 4)
    all_var.append(y)
    b_var = copy.deepcopy(cascade_mfold(x, y, 4))
    for r in range(r_begin, r_end):
        sx = lcs_layer_mfold(x, beta, 4)
        sy = rcs_layer_mfold(y, alpha, 4)

        tx = var_declare_mfold("tx", r, ws, 4)
        ty = var_declare_mfold("ty", r, ws, 4)
        tz = var_declare_mfold("tz", r, ws, 4)
        all_var += [tx, ty, tz]

        z = var_declare_mfold("z", r, ws, 4)
        all_var.append(z)
        statement += add_layer_gebct(sy, x, z, tx, ty, tz)

        x1 = var_declare_mfold("x", r + 1, ws, 4)
        all_var.append(x1)
        y1 = var_declare_mfold("y", r + 1, ws, 4)
        all_var.append(y1)

        k = var_declare_mfold("k", r, ws, 4)

        statement += xor_layer_mfold(z, k, y1, 4)
        statement += xor_layer_mfold(sx, y1, x1, 4)

        x = copy.deepcopy(x1)
        y = copy.deepcopy(y1)

        e_var = copy.deepcopy(cascade_mfold(x, y, 4))

    statement1, all_var1, mk = key_relation(r_end)

    statement += statement1
    all_var += all_var1

    statement += set_diff_in(b_var, b)
    statement += set_diff_out(e_var, e)
    statement += set_diff_kin(mk, bk)
    statement += set_diff_kout(mk)

    return statement, all_var

def build_model(r_begin, r_end, b, e, bk, ek):
    statement = ""

    bst, all_var = body(r_begin, r_end, b, e, bk, ek)

    statement += header(all_var)
    for st in bst:
        statement += "ASSERT({});\n".format(st)
    statement += trailer()
    return statement

def build_model2file(r_begin, r_end, b, e, bk, ek, solve_file):
    statement = build_model(r_begin, r_end, b, e, bk, ek)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

################################################################

def lcr(x):
    beta = config_search.beta
    y = [0 for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i + beta) % len(x)] = x[i]
    return y

def rcr(x):
    alpha = config_search.alpha
    y = [0 for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i - alpha) % len(x)] = x[i]
    return y

def verify_mod_add(x, y, z):
    xx = 0
    yy = 0
    zz = 0
    ws = config_search.ws
    for i in range(0, ws):
        xx = xx ^ (x[i] << i)
        yy = yy ^ (y[i] << i)
        zz = zz ^ (z[i] << i)
    flag = True
    if ((xx + yy) % int(pow(2, ws))) != zz:
        flag = False
    return flag

def verify_xor_key(x, y, k):
    flag = True
    ws = config_search.ws
    for i in range(0, ws):
        if (x[i] ^ k[i]) != y[i]:
            flag = False
            break
    return flag

def verify_xor(x, y, z):
    flag = True
    ws = config_search.ws
    for i in range(0, ws):
        if (x[i] ^ y[i]) != z[i]:
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
    ws = config_search.ws
    x = [[0 for i in range(0, ws)] for m in range(0, 4)]
    for m in range(0, 4):
        for i in range(0, ws):
            x[m][i] = value_dict[var[m][i]]
    return x

def verify_gebct(x, y, z, sx, sy, sz):
    flag = True
    for i in range(0, 4):
        flagx = verify_xor(sx[i], sx[(i + 1) % 4], x[i])
        flagy = verify_xor(sy[i], sy[(i + 1) % 4], y[i])
        flagz = verify_xor(sz[i], sz[(i + 1) % 4], z[i])
        flag = flagx and flagy and flagz
        if not flag:
            break
    if flag:
        for i in range(0, 4):
            flag = verify_mod_add(sx[i], sy[i], sz[i])
            if not flag:
                break
    return flag

def verify_solution(res, r_begin, r_end):
    value_dict = get_dict(res)
    ws = config_search.ws

    x = get_value(var_declare_mfold("x", r_begin, ws, 4), value_dict)
    y = get_value(var_declare_mfold("y", r_begin, ws, 4), value_dict)
    for r in range(r_begin, r_end):
        z = get_value(var_declare_mfold("z", r, ws, 4), value_dict)
        k = get_value(var_declare_mfold("k", r, ws, 4), value_dict)

        tx = get_value(var_declare_mfold("tx", r, ws, 4), value_dict)
        ty = get_value(var_declare_mfold("ty", r, ws, 4), value_dict)
        tz = get_value(var_declare_mfold("tz", r, ws, 4), value_dict)

        x1 = get_value(var_declare_mfold("x", r + 1, ws, 4), value_dict)
        y1 = get_value(var_declare_mfold("y", r + 1, ws, 4), value_dict)

        flag = verify_gebct([rcr(y[0]), rcr(y[1]), rcr(y[2]), rcr(y[3])], x, z, tx, ty, tz)
        assert(flag)

        for i in range(0, 4):
            flag = verify_xor_key(z[i], y1[i], k[i])
            assert(flag)
            flag = verify_xor_key(y1[i], lcr(x[i]), x1[i])
            assert(flag)
        x = x1
        y = y1
    print("verify suceess")

################################################################

def call_solver(thread_num, solve_file, r_begin, r_end):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if (res != "Valid."):
        verify_solution(res, r_begin, r_end)
    return True if res == "Valid." else False
