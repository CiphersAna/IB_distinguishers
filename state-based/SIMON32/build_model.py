#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess
import config_search

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

def and_layer(x, y):
    statement = []
    x0 = lcs_layer(copy.deepcopy(x), 1)
    x1 = lcs_layer(copy.deepcopy(x), 8)
    x2 = lcs_layer(copy.deepcopy(x), 2)
    for i in range(0, len(x)):
        statement.append("{} = BVXOR(({} & {}), {})".format(y[i], x0[i], x1[i], x2[i]))
    return statement

def and_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += and_layer(x[i], y[i])
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
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[0][i], x[1][i], b[0][i]))
    for i in range(0, bs):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[2][i], x[3][i], b[1][i]))
    return statement

def set_diff_out(x, e):
    statement = []
    bs = config_search.bs
    for i in range(0, bs):
        statement.append("BVXOR({}, {}) = 0bin{}".format(x[1][i], x[2][i], e[0][i]))
    for i in range(0, bs):
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

def self_eq(x, m):
    statement = []
    for i in range(1, m):
        for j in range(0, len(x[0])):
            statement.append("{} = {}".format(x[i][j], x[0][j]))
    return statement

def body(r_begin, r_end, b, e, bk, ek):
    statement = []
    all_var = []
    ws = config_search.ws

    x = var_declare_mfold("x", r_begin, ws, 4)
    all_var.append(x)
    y = var_declare_mfold("y", r_begin, ws, 4)
    all_var.append(y)
    b_var = copy.deepcopy(cascade_mfold(x, y, 4))
    for r in range(r_begin, r_end):
        z = var_declare_mfold("z", r, ws, 4)
        u = var_declare_mfold("u", r, ws, 4)
        all_var += [z, u]

        x1 = var_declare_mfold("x", r + 1, ws, 4)
        all_var.append(x1)
        y1 = var_declare_mfold("y", r + 1, ws, 4)
        all_var.append(y1)

        k = var_declare_mfold("k", r, ws, 4)
        all_var.append(k)

        statement += eq_mfold(y, x1, 4)
        statement += and_layer_mfold(y, z, 4)
        statement += xor_layer_mfold(x, z, u, 4)
        statement += xor_layer_mfold(u, k, y1, 4)
        statement += self_eq(k, 4)

        x = copy.deepcopy(x1)
        y = copy.deepcopy(y1)

    e_var = copy.deepcopy(cascade_mfold(x, y, 4))

    statement += set_diff_in(b_var, b)
    statement += set_diff_out(e_var, e)

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
    y = [0 for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[(i + l) % len(x)] = x[i]
    return y

def lcr_mfold(x, l, m):
    y = []
    for i in range(0, m):
        y.append(lcr(x[i], l))
    return y

def verify_eq(x, y):
    for i in range(0, len(x)):
        if x[i] != y[i]:
            return False
    return True

def verify_eq_mfold(x, y, m):
    for i in range(0, m):
        if not verify_eq(x[i], y[i]):
            return False
    return True

def verify_xor(x, y, z):
    for i in range(0, len(x)):
        if (z[i] != (x[i] ^ y[i])):
            return False
    return True

def verify_xor_mfold(x, y, z, m):
    for i in range(0, m):
        if not verify_xor(x[i], y[i], z[i]):
            return False
    return True

def verify_and(x, y):
    x0 = lcr(copy.deepcopy(x), 1)
    x1 = lcr(copy.deepcopy(x), 8)
    x2 = lcr(copy.deepcopy(x), 2)
    for i in range(0, len(x)):
        if (y[i] != ((x0[i] and x1[i]) ^ x2[i])):
            return False
    return True

def verify_and_mfold(x, y, m):
    for i in range(0, m):
        if not verify_and(x[i], y[i]):
            return False
    return True

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

def verify_solution(res, r_begin, r_end):
    value_dict = get_dict(res)
    ws = config_search.ws

    x = get_value(var_declare_mfold("x", r_begin, ws, 4), value_dict)
    y = get_value(var_declare_mfold("y", r_begin, ws, 4), value_dict)
    for r in range(r_begin, r_end):
        z = get_value(var_declare_mfold("z", r, ws, 4), value_dict)
        u = get_value(var_declare_mfold("u", r, ws, 4), value_dict)
        k = get_value(var_declare_mfold("k", r, ws, 4), value_dict)

        x1 = get_value(var_declare_mfold("x", r + 1, ws, 4), value_dict)
        y1 = get_value(var_declare_mfold("y", r + 1, ws, 4), value_dict)

        flag = verify_eq_mfold(y, x1, 4)
        assert(flag)
        flag = verify_and_mfold(y, z, 4)
        flag = verify_xor_mfold(x, z, u, 4)
        assert(flag)
        flag = verify_xor_mfold(u, k, y1, 4)
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
