#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess

def hex2binstr(x, length):
    binstr = "0bin"
    for i in range(0, length):
        binstr += str((x >> (length - 1 - i)) & 0x1)
    return binstr

def sbox_single(x, y, sbox):
    xx = "@".join([x[3], x[2], x[1], x[0]])
    yy = "@".join([y[3], y[2], y[1], y[0]])

    s = hex2binstr(sbox[0], 4)
    for i in range(1, len(sbox)):
        in_value = hex2binstr(i, 4)
        out_value = hex2binstr(sbox[i], 4)
        s = "(IF {} = {} THEN {} ELSE {} ENDIF)".format(xx, in_value, out_value, s)
    s = ["{} = {}".format(yy, s)]
    return s

def sbox_layer(x, y):
    statement = []
    sbox_set = [[4,10,9,2,13,8,0,14,6,11,1,12,7,15,5,3],
            [14,11,4,12,6,13,15,10,2,3,8,1,0,7,5,9],
            [5,8,1,13,10,3,4,2,14,15,12,7,6,0,9,11],
            [7,13,10,1,0,8,9,15,14,4,6,12,11,2,5,3],
            [6,12,7,1,5,15,13,8,4,10,9,14,0,3,11,2],
            [4,11,10,0,7,2,1,13,3,6,8,5,9,12,15,14],
            [13,11,4,1,3,15,5,9,0,10,14,7,6,8,2,12],
            [1,15,13,0,5,7,10,4,9,2,3,14,6,11,8,12]]
    for i in range(0, 8):
        statement += sbox_single(x[(4 * i) : (4 * i + 4)], y[(4 * i) : (4 * i + 4)], sbox_set[i])
    return statement

def sbox_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += sbox_layer(x[i], y[i])
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

    statement = "{} = BVPLUS(32, {}, {})".format(zz, xx, yy)
    return [statement]

def add_layer_mfold(x, y, z, m):
    statement = []
    for i in range(0, m):
        statement += add_layer(x[i], y[i], z[i])
    return statement

# left circular shifts
def lcs_layer(x, l):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i + l) % 32] = x[i]
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

def header(all_var):
    statement = ""
    for var in all_var:
        for l in range(0, 4):
            substatement = ", ".join(var[l])
            statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def set_diff_in(x):
    statement = []
    for i in range(0, 63):
        statement.append("{} = {}".format(x[0][i], x[1][i]))
    for i in range(0, 31) + range(32, 64):
        statement.append("{} = {}".format(x[2][i], x[3][i]))

    statement.append("BVXOR({}, {}) = 0bin1".format(x[0][63], x[1][63]))
    statement.append("BVXOR({}, {}) = 0bin1".format(x[2][31], x[3][31]))

    return statement

def set_diff_out(x):
    statement = []
    for i in range(0, 63):
        statement.append("{} = {}".format(x[1][i], x[2][i]))
    for i in range(0, 31) + range(32, 64):
        statement.append("{} = {}".format(x[0][i], x[3][i]))

    statement.append("BVXOR({}, {}) = 0bin1".format(x[1][63], x[2][63]))
    statement.append("BVXOR({}, {}) = 0bin1".format(x[0][31], x[3][31]))

    return statement

def set_diff_kin(k, b):
    statement = []
    for i in range(0, 31):
        statement.append("{} = {}".format(k[2][i], k[3][i]))
    statement.append("BVXOR({}, {}) = 0bin1".format(k[2][31], k[3][31]))
    for i in range(0, 32):
        statement.append("{} = {}".format(k[0][i], k[1][i]))

    for i in range(0, 32):
        statement.append("BVXOR({}, {}) = 0bin{}".format(k[1][i], k[2][i], b[i]))
    for i in range(0, 31):
        statement.append("BVXOR({}, {}) = 0bin{}".format(k[0][i], k[3][i], b[i]))
    statement.append("BVXOR({}, {}) = 0bin{}".format(k[0][31], k[3][31], b[31] ^ 1))

    return statement

def cascade_mfold(x, y, m):
    z = []
    for i in range(0, m):
        z.append(x[i] + y[i])
    return z

def body(r_begin, r_end, b, e):
    statement = []
    all_var = []

    k0 = var_declare_mfold("k", 0, 32, 4)
    all_var.append(k0)
    rkey = [k0, k0]

    x = var_declare_mfold("x", 0, 32, 4)
    all_var.append(copy.deepcopy(x))
    y = var_declare_mfold("y", 0, 32, 4)
    all_var.append(copy.deepcopy(y))

    b_var = copy.deepcopy(cascade_mfold(x, y, 4))

    for r in range(0, 2):
        z = var_declare_mfold("z", r, 32, 4)
        all_var.append(copy.deepcopy(z))
        statement += add_layer_mfold(x, rkey[r], z, 4)

        w = var_declare_mfold("w", r, 32, 4)
        all_var.append(copy.deepcopy(w))
        statement += sbox_layer_mfold(z, w, 4)

        x1 = var_declare_mfold("x", r + 1, 32, 4)
        all_var.append(copy.deepcopy(x1))
        y1 = var_declare_mfold("y", r + 1, 32, 4)
        all_var.append(copy.deepcopy(y1))

        statement += xor_layer_mfold(lcs_layer_mfold(w, 11, 4), y, x1, 4)
        statement += eq_mfold(x, y1, 4)

        x = copy.deepcopy(x1)
        y = copy.deepcopy(y1)

    e_var = copy.deepcopy(cascade_mfold(x, y, 4))

    statement += set_diff_in(b_var)
    statement += set_diff_out(e_var)

    statement += set_diff_kin(k0, b)

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

def verify_sbox(x, y, sbox):
    return True if sbox[x] == y else False

def verify_sbox_layer(x, y):
    flag = True
    sbox_set = [[4,10,9,2,13,8,0,14,6,11,1,12,7,15,5,3],
            [14,11,4,12,6,13,15,10,2,3,8,1,0,7,5,9],
            [5,8,1,13,10,3,4,2,14,15,12,7,6,0,9,11],
            [7,13,10,1,0,8,9,15,14,4,6,12,11,2,5,3],
            [6,12,7,1,5,15,13,8,4,10,9,14,0,3,11,2],
            [4,11,10,0,7,2,1,13,3,6,8,5,9,12,15,14],
            [13,11,4,1,3,15,5,9,0,10,14,7,6,8,2,12],
            [1,15,13,0,5,7,10,4,9,2,3,14,6,11,8,12]]
    for i in range(0, 8):
        xx = x[4 * i] ^ (x[4 * i + 1] << 1) ^ (x[4 * i + 2] << 2) ^ (x[4 * i + 3] << 3)
        yy = y[4 * i] ^ (y[4 * i + 1] << 1) ^ (y[4 * i + 2] << 2) ^ (y[4 * i + 3] << 3)
        if not verify_sbox(xx, yy, sbox_set[i]):
            flag = False
            break

    return flag

def verify_sbox_layer_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_sbox_layer(x[i], y[i]):
            flag = False
            break
    return flag

def verify_xor_layer(x, k, y):
    flag = True
    for i in range(0, 32):
        if ((x[i] ^ k[i]) != y[i]):
            flag = False
            break

    return flag

def verify_xor_layer_mfold(x, k, y, m):
    flag = True
    for i in range(0, m):
        if not verify_xor_layer(x[i], k[i], y[i]):
            flag = False
            break
    return flag

def verify_eq_layer(x, y):
    flag = True
    for i in range(0, 32):
        if (x[i] != y[i]):
            flag = False
            break

    return flag

def verify_eq_layer_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_eq_layer(x[i], y[i]):
            flag = False
            break
    return flag

def verify_add(x, y, z):
    xx = 0
    yy = 0
    zz = 0
    for i in range(0, 32):
        xx = xx ^ (x[i] << i)
        yy = yy ^ (y[i] << i)
        zz = zz ^ (z[i] << i)
    flag = True
    if ((xx + yy) % int(pow(2, 32))) != zz:
        flag = False
    return flag

def verify_add_mfold(x, y, z, m):
    flag = True
    for i in range(0, m):
        if not verify_add(x[i], y[i], z[i]):
            flag = False
            break
    return flag

def lcr(x, l):
    y = [0 for i in range(0, 32)]
    for i in range(0, len(x)):
        y[(i + l) % 32] = x[i]
    return y

def lcr_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(lcr(x[i], l))
    return y

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
    x = [[0 for i in range(0, 32)] for m in range(0, 4)]
    for m in range(0, 4):
        for i in range(0, 32):
            if var[m][i] in value_dict:
                x[m][i] = value_dict[var[m][i]]
    return x

def verify_solution(res, r_begin, r_end):
    value_dict = get_dict(res)

    k0 = get_value(var_declare_mfold("k", 0, 32, 4), value_dict)
    k1 = get_value(var_declare_mfold("k", 1, 32, 4), value_dict)
    k2 = get_value(var_declare_mfold("k", 2, 32, 4), value_dict)
    k3 = get_value(var_declare_mfold("k", 3, 32, 4), value_dict)
    k4 = get_value(var_declare_mfold("k", 4, 32, 4), value_dict)
    k5 = get_value(var_declare_mfold("k", 5, 32, 4), value_dict)
    k6 = get_value(var_declare_mfold("k", 6, 32, 4), value_dict)
    k7 = get_value(var_declare_mfold("k", 7, 32, 4), value_dict)
    rkey = [k0, k1, k2, k3, k4, k5, k6, k7,
            k0, k1, k2, k3, k4, k5, k6, k7,
            k0, k1, k2, k3, k4, k5, k6, k7,
            k7, k6, k5, k4, k3, k2, k1, k0]

    x = get_value(var_declare_mfold("x", r_begin, 32, 4), value_dict)
    y = get_value(var_declare_mfold("y", r_begin, 32, 4), value_dict)

    for r in range(r_begin, r_end):
        z = get_value(var_declare_mfold("z", r, 32, 4), value_dict)
        flag = verify_add_mfold(x, rkey[r], z, 4)
        assert(flag)

        w = get_value(var_declare_mfold("w", r, 32, 4), value_dict)
        flag = verify_sbox_layer_mfold(z, w, 4)
        assert(flag)

        x1 = get_value(var_declare_mfold("x", r + 1, 32, 4), value_dict)
        y1 = get_value(var_declare_mfold("y", r + 1, 32, 4), value_dict)
        flag = verify_xor_layer_mfold(lcr_mfold(w, 11, 4), y, x1, 4)
        assert(flag)
        flag = verify_eq_layer_mfold(x, y1, 4)
        assert(flag)
        x = x1
        y = y1

    print("verify pass")

################################################################

def call_solver(thread_num, solve_file, r_begin, r_end):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    #if (res != "Valid."):
    #    verify_solution(res, r_begin, r_end)
    return True if res == "Valid." else False
