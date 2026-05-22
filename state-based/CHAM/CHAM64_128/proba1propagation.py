#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy
import subprocess

# proba 1
def add(x, y, z, length):
    statement = []
    statement.append("BVXOR(BVXOR({}, {}), {}) = 0bin0".format(x[0], y[0], z[0]))
    for i in range(0, length - 1):
        statement.append("{} = {}".format(x[i], y[i]))
        statement.append("{} = {}".format(x[i], z[i]))
    for i in range(1, length):
        statement.append("BVXOR(BVXOR({}, {}), {}) = {}".format(x[i], y[i], z[i], x[i - 1]))
    return statement

def left_shift(x, a):
    y = ["" for i in range(0, len(x))]
    for i in range(0, len(x)):
        y[i] = x[(i - a) % len(x)]
    return y

def eq2(x, y):
    statement = []
    for i in range(0, len(x)):
        statement.append("{} = {}".format(x[i], y[i]))
    return statement

def xor2(x, y, z):
    statement = []
    for i in range(0, len(x)):
        statement.append("BVXOR({}, {}) = {}".format(x[i], y[i], z[i]))
    return statement

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

def header(all_var):
    statement = ""
    for var in all_var:
        substatement = ", ".join(var)
        statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def var_declare(var_name, r, var_len):
    return ["{}_{}_{}".format(var_name, r, i) for i in range(0, var_len)]

def init_restrict(var):
    s = " | ".join(var)
    return ["{} = 0bin1".format(s)]

def body(r_begin, r_end):
    statement = []
    all_var = []

    mk = var_declare("mk", 0, 128)
    all_var.append(copy.deepcopy(mk))
    rk = var_declare("rk", 0, 256)
    all_var.append(copy.deepcopy(rk))

    statement1, rkey = round_key(copy.deepcopy(rk), copy.deepcopy(mk))
    statement += statement1

    x = var_declare("x", r_begin, 16)
    y = var_declare("y", r_begin, 16)
    z = var_declare("z", r_begin, 16)
    w = var_declare("w", r_begin, 16)
    all_var += [x, y, z, w]
    statement += init_restrict(x + y + z + w + mk)

    for r in range(r_begin, r_end):
        x1 = var_declare("x", r + 1, 16)
        y1 = var_declare("y", r + 1, 16)
        z1 = var_declare("z", r + 1, 16)
        w1 = var_declare("w", r + 1, 16)
        all_var += [x1, y1, z1, w1]

        u = var_declare("u", r, 16)
        v = var_declare("v", r, 16)
        all_var += [u, v]

        if ((r % 2) == 0):
            statement += eq2(y, x1)
            statement += eq2(z, y1)
            statement += eq2(w, z1)
            statement += xor2(left_shift(y, 1), rkey[r % 16], u)
            statement += add(x, u, v, 16)
            statement += eq2(left_shift(v, 8), w1)
        else:
            statement += eq2(y, x1)
            statement += eq2(z, y1)
            statement += eq2(w, z1)
            statement += xor2(left_shift(y, 8), rkey[r % 16], u)
            statement += add(x, u, v, 16)
            statement += eq2(left_shift(v, 1), w1)

        x = x1
        y = y1
        z = z1
        w = w1

    return statement, all_var

def build_model(r_begin, r_end, add_statement):
    statement = ""

    bst, all_var = body(r_begin, r_end)

    statement += header(all_var)
    for st in bst:
        statement += "ASSERT({});\n".format(st)
    if len(add_statement) != 0:
        for ast in add_statement:
            statement += "ASSERT({});\n".format(ast)
    statement += trailer()
    return statement

def build_model2file(r_begin, r_end, add_statement, solve_file):
    statement = build_model(r_begin, r_end, add_statement)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

########################################################################

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
    x = [0 for i in range(0, len(var))]
    for i in range(0, len(var)):
        x[i] = value_dict[var[i]]
    return x

def remove_point(value_dict):
    l = []
    for key, value in value_dict.items():
        if value == 1:
            l.append("(~{})".format(key))
        else:
            l.append("{}".format(key))
    return "{} = 0bin1".format(" | ".join(l))

def verify_solution(res, r_begin, r_end):
    statement = ""

    value_dict = get_dict(res)

    mk = get_value(var_declare("mk", 0, 128), value_dict)

    rk = get_value(var_declare("rk", 0, 256), value_dict)

    rkey = [[] for ii in range(0, 16)]
    for i in range(0, 8):
        rkey[i] = copy.deepcopy(rk[(16 * i) : (16 * i + 16)])
        j = (i + 8) ^ 1
        rkey[j] = copy.deepcopy(rk[(16 * j) : (16 * j + 16)])

    x = get_value(var_declare("x", r_begin, 16), value_dict)
    y = get_value(var_declare("y", r_begin, 16), value_dict)
    z = get_value(var_declare("z", r_begin, 16), value_dict)
    w = get_value(var_declare("w", r_begin, 16), value_dict)

    init_state = copy.deepcopy(x + y + z + w)

    statement += "{}        {}        {}        {}\n\n".format(x, y, z, w)

    for r in range(r_begin, r_end):
        u = get_value(var_declare("u", r, 16), value_dict)
        v = get_value(var_declare("v", r, 16), value_dict)

        x1 = get_value(var_declare("x", r + 1, 16), value_dict)
        y1 = get_value(var_declare("y", r + 1, 16), value_dict)
        z1 = get_value(var_declare("z", r + 1, 16), value_dict)
        w1 = get_value(var_declare("w", r + 1, 16), value_dict)

        if ((r % 2) == 0):
            statement += "        {}\n\n".format(rkey[r % 16])
            statement += "    {}  {}\n\n".format(u, left_shift(y, 1))
            statement += "{}\n\n".format(v)
            statement += "{}\n\n".format(left_shift(v, 8))
        else:
            statement += "        {}\n\n".format(rkey[r % 16])
            statement += "    {}  {}\n\n".format(u, left_shift(y, 8))
            statement += "{}\n\n".format(v)
            statement += "{}\n\n".format(left_shift(v, 1))
        x = x1
        y = y1
        z = z1
        w = w1
        statement += "{}        {}        {}        {}\n\n".format(x, y, z, w)

    fini_state = copy.deepcopy(x + y + z + w)
    #print(statement)
    print("verify pass")
    return statement, mk, rkey, init_state, fini_state, remove_point(value_dict)

########################################################################

def call_solver(thread_num, solve_file, r_begin, r_end):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    mk = []
    init_state = []
    fini_state = []
    rkey = []
    statement = ""
    rp = ""
    if (res != "Valid."):
        statement, mk, rkey, init_state, fini_state, rp = verify_solution(res, r_begin, r_end)
    flag = True if res == "Valid." else False
    return statement, flag, mk, rkey, init_state, fini_state, rp

def search_proba1_header(r_begin, r_end, add_statement):
    dir0 = "Results"
    dir1 = "Results/CHAM64_128_proba1_header_{}_{}".format(r_begin, r_end)
    if not os.path.exists(dir0):
        os.makedirs(dir0)
    if not os.path.exists(dir1):
        os.makedirs(dir1)

    solve_file = "{}/{}".format(dir1, "model_proba1_r{}_{}.stp".format(r_begin, r_end))
    #result_file = "{}/{}".format(dir1, "model_proba1_r{}_{}.txt".format(r_begin, r_end))

    build_model2file(r_begin, r_end, add_statement, solve_file)
    statement, flag, mk, rkey, init_state, fini_state, rp = call_solver(1, solve_file, r_begin, r_end)
    #print(flag)
    #print(mk)
    #print(state)
    return statement, flag, mk, rkey, init_state, fini_state, rp

def search_proba1_trailer(r_begin, r_end, add_statement):
    dir0 = "Results"
    dir1 = "Results/CHAM64_128_proba1_trailer_{}_{}".format(r_begin, r_end)
    if not os.path.exists(dir0):
        os.makedirs(dir0)
    if not os.path.exists(dir1):
        os.makedirs(dir1)

    solve_file = "{}/{}".format(dir1, "model_proba1_r{}_{}.stp".format(r_begin, r_end))
    #result_file = "{}/{}".format(dir1, "model_proba1_r{}_{}.txt".format(r_begin, r_end))

    build_model2file(r_begin, r_end, add_statement, solve_file)
    statement, flag, mk, rkey, init_state, fini_state, rp = call_solver(1, solve_file, r_begin, r_end)
    #print(flag)
    #print(mk)
    #print(state)
    return statement, flag, mk, rkey, init_state, fini_state, rp

if __name__ == "__main__":
    search_proba1_trailer(10, 20, [])
