#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess

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

def reverse_list(x):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[len(x) - 1 - i] = x[i]
    return y

def add_layer(x, y, z):
    xx = "@".join(reverse_list(x))
    yy = "@".join(reverse_list(y))
    zz = "@".join(reverse_list(z))

    statement = "{} = BVPLUS(16, {}, {})".format(zz, xx, yy)
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

# left circular shifts
def lcs_layer(x, l):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i + l) % 16] = x[i]
    return y

def lcs_layer_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(lcs_layer(x[i], l))
    return y

def eq2(x, y):
    statement = []
    for i in range(0, len(x)):
        statement.append("{} = {}".format(x[i], y[i]))
    return statement

def eq_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += eq2(x[i], y[i])
    return statement

def left_shift(x, l):
    return lcs_layer(x, l)

def rk1gen(rk, k):
    statement = []
    k1 = left_shift(k, 1)
    k8 = left_shift(k, 8)
    for i in range(0, 16):
        statement.append("BVXOR(BVXOR({}, {}), {}) = {}".format(k[i], k1[i], k8[i], rk[i]))
    return statement

def rk2gen(rk, k):
    statement = []
    k1 = left_shift(k, 1)
    k8 = left_shift(k, 11)
    for i in range(0, 16):
        statement.append("BVXOR(BVXOR({}, {}), {}) = {}".format(k[i], k1[i], k8[i], rk[i]))
    return statement

def round_key(rk, mk):
    statement = []
    rkey = [[] for ii in range(0, 16)]
    for i in range(0, 8):
        statement += rk1gen(rk[(16 * i) : (16 * i + 16)], mk[(16 * i) : (16 * i + 16)])
        rkey[i] = copy.deepcopy(rk[(16 * i) : (16 * i + 16)])
        j = (i + 8) ^ 1
        statement += rk2gen(rk[(16 * j) : (16 * j + 16)], mk[(16 * i) : (16 * i + 16)])
        rkey[j] = copy.deepcopy(rk[(16 * j) : (16 * j + 16)])
    return statement, rkey

def round_key_mfold(rk, mk, m):
    statement = []
    rkey = [[] for i in range(0, 16)]
    for i in range(0, m):
        statement1, rkey1 = round_key(rk[i], mk[i])
        statement += statement1
        for j in range(0, 16):
            rkey[j].append(rkey1[j])
    return statement, rkey

def header(all_var):
    statement = ""
    for var in all_var:
        for l in range(0, len(var)):
            substatement = ", ".join(var[l])
            statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def var_declare(var_name, r, var_len):
    return ["{}_{}_{}".format(var_name, r, i) for i in range(0, var_len)]

def var_declare_mfold(var_name, r, var_len, m):
    var = []
    for i in range(0, m):
        var.append(var_declare("{}{}".format(var_name, i), r, var_len))
    return var

def set_diff_in(x, b):
    statement = []
    for i in range(0, 64):
        statement.append("{} = 0bin{}".format(x[0][i], b[i]))
    for i in range(0, 64):
        statement.append("{} = 0bin{}".format(x[2][i], b[i]))
    return statement

def set_diff_out(x, e):
    statement = []
    for i in range(0, 64):
        statement.append("{} = 0bin{}".format(x[1][i], e[i]))
    for i in range(0, 64):
        statement.append("{} = 0bin{}".format(x[3][i], e[i]))
    return statement

def set_diff_kin(kk, b):
    statement = []
    for i in range(0, 128):
        statement.append("{} = 0bin{}".format(kk[0][i], b[i]))
    for i in range(0, 128):
        statement.append("{} = 0bin{}".format(kk[2][i], b[i]))
    return statement

def set_diff_kout(kk, e):
    statement = []
    for i in range(0, 128):
        statement.append("{} = 0bin{}".format(kk[1][i], e[i]))
    for i in range(0, 128):
        statement.append("{} = 0bin{}".format(kk[3][i], e[i]))
    return statement

def cascade_mfold(x, y, z, w, m):
    xx = []
    for i in range(0, m):
        xx.append(x[i] + y[i] + z[i] + w[i])
    return xx

def body(r_begin, r_end, b, e, bk, ek):
    statement = []
    all_var = []

    mk = var_declare_mfold("mk", 0, 128, 4)
    all_var.append(copy.deepcopy(mk))
    rk = var_declare_mfold("rk", 0, 256, 4)
    all_var.append(copy.deepcopy(rk))

    statement1, rkey = round_key_mfold(copy.deepcopy(rk), copy.deepcopy(mk), 4)
    statement += statement1

    x = var_declare_mfold("x", r_begin, 16, 4)
    y = var_declare_mfold("y", r_begin, 16, 4)
    z = var_declare_mfold("z", r_begin, 16, 4)
    w = var_declare_mfold("w", r_begin, 16, 4)
    all_var += [x, y, z, w]

    statement += set_diff_in(cascade_mfold(x, y, z, w, 4), b)

    for r in range(r_begin, r_end):
        x1 = var_declare_mfold("x", r + 1, 16, 4)
        y1 = var_declare_mfold("y", r + 1, 16, 4)
        z1 = var_declare_mfold("z", r + 1, 16, 4)
        w1 = var_declare_mfold("w", r + 1, 16, 4)
        all_var += [x1, y1, z1, w1]

        u = var_declare_mfold("u", r, 16, 4)
        v = var_declare_mfold("v", r, 16, 4)
        all_var += [u, v]

        tx = var_declare_mfold("tx", r, 16, 4)
        tu = var_declare_mfold("tu", r, 16, 4)
        tv = var_declare_mfold("tv", r, 16, 4)
        all_var += [tx, tu, tv]

        if ((r % 2) == 0):
            statement += eq_mfold(y, x1, 4)
            statement += eq_mfold(z, y1, 4)
            statement += eq_mfold(w, z1, 4)
            statement += xor_layer_mfold(lcs_layer_mfold(y, 1, 4), rkey[r % 16], u, 4)
            statement += add_layer_gebct(x, u, v, tx, tu, tv)
            statement += eq_mfold(lcs_layer_mfold(v, 8, 4), w1, 4)
        else:
            statement += eq_mfold(y, x1, 4)
            statement += eq_mfold(z, y1, 4)
            statement += eq_mfold(w, z1, 4)
            statement += xor_layer_mfold(lcs_layer_mfold(y, 8, 4), rkey[r % 16], u, 4)
            statement += add_layer_gebct(x, u, v, tx, tu, tv)
            statement += eq_mfold(lcs_layer_mfold(v, 1, 4), w1, 4)

        x = x1
        y = y1
        z = z1
        w = w1
    statement += set_diff_out(cascade_mfold(x, y, z, w, 4), e)

    statement += set_diff_kin(mk, bk)
    statement += set_diff_kout(mk, ek)

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

def lcr(x, l):
    y = [0 for i in range(0, 16)]
    for i in range(0, len(x)):
        y[(i + l) % 16] = x[i]
    return y

def lcr_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(lcr(x[i], l))
    return y

def verify_add(x, y, z):
    xx = 0
    yy = 0
    zz = 0
    for i in range(0, 16):
        xx = xx ^ (x[i] << i)
        yy = yy ^ (y[i] << i)
        zz = zz ^ (z[i] << i)
    flag = True
    if ((xx + yy) % int(pow(2, 16))) != zz:
        flag = False
    return flag

def verify_add_mfold(x, y, z, m):
    flag = True
    for i in range(0, m):
        if not verify_add(x[i], y[i], z[i]):
            flag = False
            break
    return flag

def verify_xor(x, y, k):
    flag = True
    for i in range(0, 16):
        if (x[i] ^ k[i]) != y[i]:
            flag = False
            break
    return flag

def verify_xor_mfold(x, y, z, m):
    flag = True
    for i in range(0, m):
        if not verify_xor(x[i], y[i], z[i]):
            flag = False
            break
    return flag

def verify_eq(x, y):
    flag = True
    for i in range(0, 16):
        if (x[i] != y[i]):
            flag = False
            break
    return flag

def verify_eq_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_eq(x[i], y[i]):
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
    x = [[0 for i in range(0, len(var[0]))] for m in range(0, 4)]
    for m in range(0, 4):
        for i in range(0, len(var[0])):
            x[m][i] = value_dict[var[m][i]]
    return x

def verify_xor_const(x, y, r):
    flag = True
    for i in range(0, 16):
        if y[i] != (x[i] ^ ((r >> i) & 0x1)):
            flag = False
            break
    return flag

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
            flag = verify_add(sx[i], sy[i], sz[i])
            if not flag:
                break
    return flag

def verify_xor_const_mfold(x, y, r, m):
    flag = True
    for i in range(0, m):
        if not verify_xor_const(x[i], y[i], r):
            flag = False
            break
    return flag

def verify_solution(res, r_begin, r_end):
    value_dict = get_dict(res)

    rkey = [[] for i in range(0, 16)]
    rk = get_value(var_declare_mfold("rk", 0, 256, 4), value_dict)
    for i in range(0, 8):
        ek = []
        for j in range(0, 4):
            ek.append(rk[j][(16 * i) : (16 * i + 16)])
        rkey[i] = ek
        k = (i + 8) ^ 1
        ek = []
        for j in range(0, 4):
            ek.append(rk[j][(16 * k) : (16 * k + 16)])
        rkey[k] = ek

    x = get_value(var_declare_mfold("x", r_begin, 16, 4), value_dict)
    y = get_value(var_declare_mfold("y", r_begin, 16, 4), value_dict)
    z = get_value(var_declare_mfold("z", r_begin, 16, 4), value_dict)
    w = get_value(var_declare_mfold("w", r_begin, 16, 4), value_dict)

    for r in range(r_begin, r_end):
        x1 = get_value(var_declare_mfold("x", r + 1, 16, 4), value_dict)
        y1 = get_value(var_declare_mfold("y", r + 1, 16, 4), value_dict)
        z1 = get_value(var_declare_mfold("z", r + 1, 16, 4), value_dict)
        w1 = get_value(var_declare_mfold("w", r + 1, 16, 4), value_dict)

        u = get_value(var_declare_mfold("u", r, 16, 4), value_dict)
        v = get_value(var_declare_mfold("v", r, 16, 4), value_dict)

        tx = get_value(var_declare_mfold("tx", r, 16, 4), value_dict)
        tu = get_value(var_declare_mfold("tu", r, 16, 4), value_dict)
        tv = get_value(var_declare_mfold("tv", r, 16, 4), value_dict)

        flag = verify_eq_mfold(x1, y, 4)
        assert(flag)
        flag = verify_eq_mfold(y1, z, 4)
        assert(flag)
        flag = verify_eq_mfold(z1, w, 4)
        assert(flag)

        flag = verify_gebct(x, u, v, tx, tu, tv)
        assert(flag)

        if ((r % 2) == 0):
            flag = verify_xor_mfold(lcr_mfold(y, 1, 4), rkey[r % 16], u, 4)
            assert(flag)
            flag = verify_eq_mfold(lcr_mfold(v, 8, 4), w1, 4)
            assert(flag)
        else:
            flag = verify_xor_mfold(lcr_mfold(y, 8, 4), rkey[r % 16], u, 4)
            assert(flag)
            flag = verify_eq_mfold(lcr_mfold(v, 1, 4), w1, 4)
            assert(flag)

        x = x1
        y = y1
        z = z1
        w = w1
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
