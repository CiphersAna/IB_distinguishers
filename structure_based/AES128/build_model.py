#!/usr/bin/python
# -*- coding: UTF-8 -*-

import copy
import subprocess
import bc_description

def sbox_single(in_var, out_var):
    bool_set = [[1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, -1],\
            [0, 0, 0, 0, 0, 0, 0, -1, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, -1, 0],\
            [0, 0, 0, 0, 0, 0, -1, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, -1, 0, 0],\
            [0, 0, 0, 0, 0, -1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, -1, 0, 0, 0],\
            [0, 0, 0, 0, -1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, -1, 0, 0, 0, 0],\
            [0, 0, 0, -1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, -1, 0, 0, 0, 0, 0],\
            [0, 0, -1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, 0, -1, 0, 0, 0, 0, 0, 0],\
            [0, -1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1],\
            [1, 1, 1, 1, 1, 1, 1, 1, -1, 0, 0, 0, 0, 0, 0, 0],\
            [-1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]]

    statement = []
    all_var = in_var + out_var
    for bool_cons in bool_set:
        sublist = []
        for i in range(0, len(bool_cons)):
            num = bool_cons[i]
            if num == 1:
                sublist.append(all_var[i])
            elif num == -1:
                sublist.append("~{}".format(all_var[i]))
        if len(sublist) == 1:
            statement = sublist[0]
        else:
            substatment = " | ".join(sublist)
        statement.append("({}) = 0bin1".format(substatment))
    return statement

def sbox_layer(x, y):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            statement += sbox_single(x[i][j], y[i][j])
    return statement

def sbox_diff(x):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 8):
                substatement = "BVXOR(BVXOR(BVXOR({}, {}), {}), {}) = 0bin0".format(x[0][i][j][k], x[1][i][j][k], x[2][i][j][k], x[3][i][j][k])
                statement.append(substatement)
    return statement

def sbox_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += sbox_layer(x[i], y[i])
    statement += sbox_diff(x)
    statement += sbox_diff(y)
    return statement

def __mix_column(in_var, out_var, mat):
    statement = []
    for i in range(0, 32):
        xor_list = []
        for j in range(0, 32):
            if mat[i][j] == 1:
                xor_list.append(in_var[j])
        if (len(xor_list) == 1):
            statement.append("{} = {}".format(in_var[i], xor_list[0]))
        else:
            substatement = "BVXOR({}, {})".format(xor_list[0], xor_list[1])
            for k in range(2, len(xor_list)):
                substatement = "BVXOR({}, {})".format(substatement, xor_list[k])
            statement.append("{} = {}".format(out_var[i], substatement))
    return statement

def mix_column_layer(in_var, out_var):
    statement = []
    mat = bc_description.get_mc_mat()
    for j in range(0, 4):
        in1 = in_var[0][j] + in_var[1][j] + in_var[2][j] + in_var[3][j]
        out1 = out_var[0][j] + out_var[1][j] + out_var[2][j] + out_var[3][j]
        statement += __mix_column(in1, out1, mat)
    return statement

def mix_column_layer_mfold(in_var, out_var, m):
    statement = []
    for i in range(0, m):
        statement += mix_column_layer(in_var[i], out_var[i])
    return statement

def sr_layer(in_var):
    rvar = [[["" for k in range(0, 8)] for j in range(0, 4)] for i in range(0, 4)]
    sr = [0, 1, 2, 3]
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 8):
                rvar[i][(j - sr[i]) % 4][k] = in_var[i][j][k]
    return rvar

def sr_layer_mfold(in_var, m):
    out_var = []
    for i in range(0, m):
        out_var.append(sr_layer(in_var[i]))
    return out_var

def xor_layer(in_var0, in_var1, out_var):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 8):
                substatement = "{} = BVXOR({}, {})".format(out_var[i][j][k], in_var0[i][j][k], in_var1[i][j][k])
                statement.append(substatement)
    return statement

def xor_layer_mfold(in_var0, in_var1, out_var, m):
    statement = []
    for i in range(0, m):
        statement += xor_layer(in_var0[i], in_var1[i], out_var[i])
    return statement

def var_declare(name):
    return [[["{}_{}_{}_{}".format(name, i, j, k) for k in range(0, 8)] for j in range(0, 4)] for i in range(0, 4)]

def var_declare_mfold(name, m):
    return [var_declare("{}{}".format(name, i)) for i in range(0, m)]

def header(all_var, tmp_key_var):
    statement = ""

    for var in all_var:
        for l in range(0, 4):
            for i in range(0, 4):
                for j in range(0, 4):
                    substatement = ", ".join(var[l][i][j])
                    statement += "{} : BITVECTOR(1);\n".format(substatement)
    for var in tmp_key_var:
        for i in range(0, 4):
            substatement = ", ".join(var[i])
            statement += "{} : BITVECTOR(1);\n".format(substatement)

    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def set_diff_in(x, b):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            s = " | ".join(x[0][i][j])
            statement.append("({}) = 0bin{}".format(s, b[0][i][j]))
            s = " | ".join(x[2][i][j])
            statement.append("({}) = 0bin{}".format(s, b[1][i][j]))
    return statement

def set_diff_out(x, e):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            s = " | ".join(x[1][i][j])
            statement.append("({}) = 0bin{}".format(s, e[0][i][j]))
            s = " | ".join(x[3][i][j])
            statement.append("({}) = 0bin{}".format(s, e[1][i][j]))
    return statement

def __set_diff_k(key, x):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            for k in range(0, 8):
                statement.append("{} = {}".format(key[i][j][k], x[i][j][k]))
    return statement

def set_diff_kin(key, x):
    statement = []
    statement += __set_diff_k(key[0], x[0])
    statement += __set_diff_k(key[2], x[2])
    return statement

def set_diff_kout(x):
    statement = []
    for i in range(0, 4):
        for j in range(0, 4):
            s = " | ".join(x[1][i][j])
            statement.append("({}) = 0bin0".format(s))
            s = " | ".join(x[3][i][j])
            statement.append("({}) = 0bin0".format(s))
    return statement

def key_sbox_layer(x, y):
    statement = []

    for i in range(0, 4):
        statement += sbox_single(x[i], y[i])
    return statement

def key_xor_layer(in1, in2, out1):
    statement = []
    for i in range(0, 4):
        for j in range(0, 8):
            statement.append("{} = BVXOR({}, {})".format(out1[i][j], in1[i][j], in2[i][j]))
    return statement

def get_column_value(var, col):
    return [var[0][col], var[1][col], var[2][col], var[3][col]]

def build_key_relation(in_k, out_k, tmp_k):
    statement = []

    statement += key_sbox_layer([in_k[1][3], in_k[2][3], in_k[3][3], in_k[0][3]], tmp_k)

    for l in range(0, 4):
        statement += key_xor_layer(get_column_value(in_k, 0), tmp_k, get_column_value(out_k, 0))
        statement += key_xor_layer(get_column_value(in_k, 1), get_column_value(out_k, 0), get_column_value(out_k, 1))
        statement += key_xor_layer(get_column_value(in_k, 2), get_column_value(out_k, 1), get_column_value(out_k, 2))
        statement += key_xor_layer(get_column_value(in_k, 3), get_column_value(out_k, 2), get_column_value(out_k, 3))

    return statement

def build_key_relation_mfold(in_k, out_k, r, m):
    statement = []
    tmp_key_var = []

    for i in range(0, m):
        tmp_k = [["tk{}_{}_{}_{}".format(i, r, ii, jj) for jj in range(0, 8)] for ii in range(0, 4)]
        tmp_key_var.append(copy.deepcopy(tmp_k))
        statement += build_key_relation(in_k[i], out_k[i], tmp_k)

    for j in range(0, 4):
        for k in range(0, 8):
            statement.append("BVXOR(BVXOR(BVXOR({}, {}), {}), {}) = 0bin0".format(in_k[0][j][3][k], in_k[1][j][3][k], in_k[2][j][3][k], in_k[3][j][3][k]))
            statement.append("BVXOR(BVXOR(BVXOR({}, {}), {}), {}) = 0bin0".format(tmp_key_var[0][j][k], tmp_key_var[1][j][k], tmp_key_var[2][j][k], tmp_key_var[3][j][k]))

    return statement, tmp_key_var

def body(r_begin, r_end, r_middle, b, e, bk, ek):
    statement = []
    all_var = []
    tmp_key_var = []

    x = var_declare_mfold("x{}".format(r_begin), 4)
    all_var.append(copy.deepcopy(x))
    k = var_declare_mfold("k{}".format(r_begin), 4)
    all_var.append(copy.deepcopy(k))

    for r in range(r_begin, r_end - 1):
        y = var_declare_mfold("y{}".format(r), 4)
        all_var.append(copy.deepcopy(y))
        statement += xor_layer_mfold(x, k, y, 4)

        z = var_declare_mfold("z{}".format(r), 4)
        all_var.append(copy.deepcopy(z))
        statement += sbox_layer_mfold(y, z, 4)

        sz = sr_layer_mfold(z, 4)
        x1 = var_declare_mfold("x{}".format(r + 1), 4)
        all_var.append(copy.deepcopy(x1))

        statement += mix_column_layer_mfold(sz, x1, 4)
        x = copy.deepcopy(x1)

        k1 = var_declare_mfold("k{}".format(r + 1), 4)
        all_var.append(copy.deepcopy(k1))
        statement0, tmp_key_var0 = build_key_relation_mfold(k, k1, r, 4)
        statement += statement0
        tmp_key_var += tmp_key_var0

        k = copy.deepcopy(k1)

    y = var_declare_mfold("y{}".format(r_end - 1), 4)
    all_var.append(copy.deepcopy(y))
    statement += xor_layer_mfold(x, k, y, 4)

    z = var_declare_mfold("z{}".format(r_end - 1), 4)
    all_var.append(copy.deepcopy(z))
    statement += sbox_layer_mfold(y, z, 4)

    b_var = var_declare_mfold("x{}".format(r_begin), 4)
    e_var = sr_layer_mfold(var_declare_mfold("z{}".format(r_end - 1), 4), 4)

    bk_var = var_declare_mfold("k{}".format(r_begin), 4)
    ek_var = var_declare_mfold("k{}".format(r_end - 1), 4)

    statement += set_diff_in(b_var, b)
    statement += set_diff_out(e_var, e)
    statement += set_diff_kin(bk_var, b_var)
    statement += set_diff_kout(bk_var)

    return statement, all_var, tmp_key_var

def build_model(r_begin, r_end, r_middle, b, e, bk, ek):
    body0, all_var, tmp_key_var = body(r_begin, r_end, r_middle, b, e, bk, ek)

    statement = header(all_var, tmp_key_var)
    for st in body0:
        statement += "ASSERT({});\n".format(st)
    statement += trailer()
    return statement

def build_model2file(r_begin, r_end, r_middle, b, e, bk, ek, solve_file):
    statement = build_model(r_begin, r_end, r_middle, b, e, bk, ek)

    f = open(solve_file, "w")
    f.write(statement)
    f.close()

#######################################################################

def verify_sbox(x, y):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            if (x[i][j] == 0 and y[i][j] != 0) or (x[i][j] != 0 and y[i][j] == 0):
                flag = False
                break
        if not flag:
            break
    return flag

def verify_sbox_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_sbox(x[i], y[i]):
            flag = False
            break
    return flag

def verify_sr(x):
    y = [["" for j in range(0, 4)] for i in range(0, 4)]
    p = [0, 1, 2, 3]
    for i in range(0, 4):
        for j in range(0, 4):
            y[i][(j - p[i]) % 4] = x[i][j]
    return y

def verify_sr_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(verify_sr(x[i]))
    return y

def tranhex2bin(value):
    b = [0 for i in range(0, 8)]
    for i in range(0, 8):
        b[i] = (value >> i) & 0x1
    return b

def transbin2hex(b):
    value = 0
    for i in range(0, 8):
        value = value ^ (b[i] << i)
    return value

def multi_0x02(value):
    b = tranhex2bin(value)
    a = [0 for i in range(0, 8)]
    for i in range(1, 8):
        a[i] = b[i - 1]
    c = [0 for i in range(0, 8)]
    c[0] = a[0] ^ b[7]
    c[1] = a[1] ^ b[7]
    c[2] = a[2]
    c[3] = a[3] ^ b[7]
    c[4] = a[4] ^ b[7]
    c[5] = a[5]
    c[6] = a[6]
    c[7] = a[7]
    return transbin2hex(c)

def multi_0x03(value):
    return multi_0x02(value) ^ value

def multi_column(in1, out1):
    t = [0, 0, 0, 0]
    t[0] = multi_0x02(in1[0]) ^ multi_0x03(in1[1]) ^ in1[2] ^ in1[3]
    t[1] = in1[0] ^ multi_0x02(in1[1]) ^ multi_0x03(in1[2]) ^ in1[3]
    t[2] = in1[0] ^ in1[1] ^ multi_0x02(in1[2]) ^ multi_0x03(in1[3])
    t[3] = multi_0x03(in1[0]) ^ in1[1] ^ in1[2] ^ multi_0x02(in1[3])
    flag = True
    for i in range(0, 4):
        if t[i] != out1[i]:
            flag = False
            break
    return flag

def verify_mc(in1, out1):
    flag = True
    for j in range(0, 4):
        flag = multi_column([in1[0][j], in1[1][j], in1[2][j], in1[3][j]], [out1[0][j], out1[1][j], out1[2][j], out1[3][j]])
        if not flag:
            break
    return flag

def verify_mc_mfold(x, y, m):
    flag = True
    for i in range(0, m):
        if not verify_mc(x[i], y[i]):
            flag = False
            break
    return flag

def verify_xor(x, y, z):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            if ((x[i][j] ^ y[i][j]) != z[i][j]):
                flag = False
                break
        if not flag:
            break
    return flag

def verify_xor_mfold(x, y, z, m):
    flag = True
    for i in range(0, m):
        if not verify_xor(x[i], y[i], z[i]):
            flag = False
            break
    return flag

def verify_connect(x, y):
    flag = True
    for i in range(0, 4):
        for j in range(0, 4):
            if ((x[0][i][j] ^ x[1][i][j]) != (y[0][i][j] ^ y[1][i][j])):
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

def get_value(var, value_dict):
    x = [[[0 for j in range(0, 4)] for i in range(0, 4)] for l in range(0, 4)]
    for l in range(0, 4):
        for i in range(0, 4):
            for j in range(0, 4):
                for k in range(0, 8):
                    x[l][i][j] = x[l][i][j] ^ (value_dict[var[l][i][j][k]] << k)
    return x

def get_value_tk(var, value_dict):
    x = [0 for i in range(0, 4)]
    for i in range(0, 4):
        for j in range(0, 8):
            x[i] = x[i] ^ (value_dict[var[i][j]] << j)
    

def format_out(x, isp=False):
    if isp:
        for i in range(0, len(x)):
            print(x[i])
        print("\n\n")

def verify_solution(res, r_begin, r_end, r_middle):
    value_dict = get_dict(res)

    x = get_value(var_declare_mfold("x{}".format(r_begin), 4), value_dict)
    format_out(x)
    for r in range(r_begin, r_end - 1):
        k = get_value(var_declare_mfold("k{}".format(r), 4), value_dict)
        format_out(k)
        y = get_value(var_declare_mfold("y{}".format(r), 4), value_dict)
        format_out(y)
        flag = verify_xor_mfold(x, k, y, 4)
        assert(flag)

        z = get_value(var_declare_mfold("z{}".format(r), 4), value_dict)
        format_out(z)
        flag = verify_sbox_mfold(y, z, 4)
        assert(flag)

        x1 = get_value(var_declare_mfold("x{}".format(r + 1), 4), value_dict)
        format_out(x1)
        sz = verify_sr_mfold(z, 4)
        flag = verify_mc_mfold(sz, x1, 4)
        assert(flag)
        x = x1

    k = get_value(var_declare_mfold("k{}".format(r_end - 1), 4), value_dict)
    format_out(k)
    y = get_value(var_declare_mfold("y{}".format(r_end - 1), 4), value_dict)
    format_out(y)
    flag = verify_xor_mfold(x, k, y, 4)
    assert(flag)
    z = get_value(var_declare_mfold("z{}".format(r_end - 1), 4), value_dict)
    flag = verify_sbox_mfold(y, z, 4)
    format_out(z)
    assert(flag)

    print("verify pass")

#######################################################################

def call_solver(thread_num, solve_file, r_begin, r_end, r_middle):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if res != "Valid.":
        verify_solution(res, r_begin, r_end, r_middle)
    return True if res == "Valid." else False
