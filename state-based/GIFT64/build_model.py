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

    sbox = [0x1, 0xa, 0x4, 0xc, 0x6, 0xf, 0x3, 0x9, 0x2, 0xd, 0xb, 0x7, 0x5, 0x0, 0x8, 0xe]

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

def sbox_layer_mfold(x, y, m):
    statement = []
    for i in range(0, m):
        statement += sbox_layer(x[i], y[i])
    return statement

def xor_layer(x, y, z):
    statement = []
    for i in range(0, len(x)):
        s = "{} = BVXOR({}, {})".format(z[i], x[i], y[i])
        statement.append(s)
    return statement

def xor_layer_mfold(x, k, y, m):
    statement = []
    for i in range(0, m):
        statement += xor_layer(x[i], k[i], y[i])
    return statement

# y_r = p(x_(r + 1))
def pbox_layer(x):
    pbox = [0, 17, 34, 51, 48, 1, 18, 35, 32, 49, 2, 19, 16, 33, 50, 3,
            4, 21, 38, 55, 52, 5, 22, 39, 36, 53, 6, 23, 20, 37, 54, 7,
            8, 25, 42, 59, 56, 9, 26, 43, 40, 57, 10, 27, 24, 41, 58, 11,
            12, 29, 46, 63, 60, 13, 30, 47, 44, 61, 14, 31, 28, 45, 62, 15]
    y = ["" for i in range(0, 64)]
    for i in range(0, 64):
        y[i] = x[pbox[i]]
    return y

def pbox_layer_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(pbox_layer(x[i]))
    return y

def update_rk(xk, addk):
    yk = ["" for i in range(0, 128)]
    statement = []

    # k7 || k6 || ... || k0  <-- k1 >>> 2 || k0 >>> 12 || ... || k3 || k2
    for i in range(0, 6):
        for j in range(0, 16):
            yk[16 * i + j] = xk[16 * (i + 2) + j]

    for i in range(0, 2):
        for j in range(0, 16):
            yk[16 * (6 + i) + j] = addk[16 * i + j]

    for j in range(0, 16):
        statement.append("{} = {}".format(addk[16 * 0 + j], xk[0 * 16 + (j + 12) % 16]))

    for j in range(0, 16):
        statement.append("{} = {}".format(addk[16 * 1 + j], xk[1 * 16 + (j + 2) % 16]))

    return yk, statement

def update_rk_mfold(xk, addk, m):
    yk = []
    statement = []
    for i in range(0, m):
        yk1, statement1 = update_rk(xk[i], addk[i])
        yk.append(yk1)
        statement += statement1
    return yk, statement

def real_round_xor(k, r):
    pos = [3, 7, 11, 15, 19, 23, 63]
    rx = ["" for i in range(0, 64)]

    gift64_rc = [0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3E, 0x3D, 0x3B, 0x37, 0x2F, 0x1E, 0x3C, 0x39, 0x33, 0x27, 0x0E,
            0x1D, 0x3A, 0x35, 0x2B, 0x16, 0x2C, 0x18, 0x30, 0x21, 0x02, 0x05, 0x0B, 0x17, 0x2E, 0x1C, 0x38]

    for i in range(0, 16):
        rx[4 * i + 0] = k[i]
        rx[4 * i + 1] = k[i + 16]
        rx[4 * i + 2] = "0bin0"
        rx[4 * i + 3] = "0bin0"

    # set distinguisher begin at round 16
    rb = r + 16
    rx[3] = "0bin" + str((gift64_rc[rb] >> 0) & 0x1)
    rx[7] = "0bin" + str((gift64_rc[rb] >> 1) & 0x1)
    rx[11] = "0bin" + str((gift64_rc[rb] >> 2) & 0x1)
    rx[15] = "0bin" + str((gift64_rc[rb] >> 3) & 0x1)
    rx[19] = "0bin" + str((gift64_rc[rb] >> 4) & 0x1)
    rx[23] = "0bin" + str((gift64_rc[rb] >> 5) & 0x1)
    rx[63] = "0bin" + str((gift64_rc[rb] >> 6) & 0x1)

    return rx

def real_round_xor_mfold(k, r, m):
    rx = []
    for i in range(0, m):
        rx.append(real_round_xor(k[i], r))
    return rx

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

def header(all_var):
    statement = ""
    for var in all_var:
        for i in range(0, len(var)):
            substatement = ", ".join(var[i])
            statement += "{} : BITVECTOR(1);\n".format(substatement)
    return statement

def trailer():
    return "QUERY(FALSE);\nCOUNTEREXAMPLE;"

def set_diff_in(x):
    statement = []
    for j in range(0, len(x[0])):
        statement.append("{} = {}".format(x[0][j], x[1][j]))
    for j in range(0, len(x[0])):
        statement.append("{} = {}".format(x[2][j], x[3][j]))
    return statement

def set_diff_out(x):
    statement = []
    for j in range(0, len(x[0])):
        statement.append("{} = {}".format(x[1][j], x[2][j]))
    for j in range(0, len(x[0])):
        statement.append("{} = {}".format(x[0][j], x[3][j]))
    return statement

def split_key(k):
    rk = ["" for i in range(0, 32)]
    for i in range(0, 16):
        rk[2 * i] = k[i]
        rk[2 * i + 1] = k[i + 16]
    nrk = k[32 : 128]
    return rk, nrk

def set_diff_kin(k, b):
    statement = []

    rk0, nrk0 = split_key(k[0])
    rk1, nrk1 = split_key(k[1])
    rk2, nrk2 = split_key(k[2])
    rk3, nrk3 = split_key(k[3])

    for i in range(0, 32):
        statement.append("BVXOR({}, {}) = 0bin{}".format(rk0[i], rk1[i], b[0][i]))
        statement.append("BVXOR({}, {}) = 0bin{}".format(rk2[i], rk3[i], b[1][i]))

    for i in range(0, 96):
        statement.append("{} = {}".format(nrk0[i], nrk1[i]))
        statement.append("{} = {}".format(nrk2[i], nrk3[i]))
    return statement

def set_diff_kout(k, e):
    statement = []

    rk0, nrk0 = split_key(k[0])
    rk1, nrk1 = split_key(k[1])
    rk2, nrk2 = split_key(k[2])
    rk3, nrk3 = split_key(k[3])

    for i in range(0, 32):
        statement.append("BVXOR({}, {}) = 0bin{}".format(rk1[i], rk2[i], e[0][i]))
        statement.append("BVXOR({}, {}) = 0bin{}".format(rk0[i], rk3[i], e[1][i]))

    for i in range(0, 96):
        statement.append("{} = {}".format(nrk1[i], nrk2[i]))
        statement.append("{} = {}".format(nrk0[i], nrk3[i]))
    return statement

def body(total_round, b, e):
    statement = []
    all_var = []

    b_var = []
    e_var = []
    bk_var = []
    ek_var = []

    x = var_declare_mfold("x", 0, 64, 4)
    all_var.append(copy.deepcopy(x))
    b_var = copy.deepcopy(x)

    curr_var = var_declare_mfold("k", 0, 128, 4)
    all_var.append(copy.deepcopy(curr_var))
    bk_var = copy.deepcopy(curr_var)
    for r in range(0, total_round):
        k = curr_var
        rx = real_round_xor_mfold(k, r, 4)

        y = var_declare_mfold("y", r, 64, 4)
        all_var.append(copy.deepcopy(y))

        statement += xor_layer_mfold(x, rx, y, 4)

        x1 = var_declare_mfold("x", r + 1, 64, 4)
        all_var.append(copy.deepcopy(x1))
        px1 = pbox_layer_mfold(x1, 4)
        statement += sbox_layer_mfold(y, px1, 4)

        addk = var_declare_mfold("addk", r, 32, 4)
        all_var.append(addk)

        curr_var, statement1 = update_rk_mfold(k, addk, 4)
        statement += statement1
        x = copy.deepcopy(x1)

    k = curr_var
    ek_var = copy.deepcopy(curr_var)
    rx = real_round_xor_mfold(k, r, 4)
    y = var_declare_mfold("y", total_round, 64, 4)
    all_var.append(copy.deepcopy(y))

    statement += xor_layer_mfold(x, rx, y, 4)
    e_var = copy.deepcopy(y)

    statement += set_diff_in(b_var)
    statement += set_diff_out(e_var)

    statement += set_diff_kin(bk_var, b)
    statement += set_diff_kout(ek_var, e)

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
    xx = (x[3] << 3) ^ (x[2] << 2) ^ (x[1] << 1) ^ (x[0] << 0)
    yy = (y[3] << 3) ^ (y[2] << 2) ^ (y[1] << 1) ^ (y[0] << 0)

    sbox = [0x1, 0xa, 0x4, 0xc, 0x6, 0xf, 0x3, 0x9, 0x2, 0xd, 0xb, 0x7, 0x5, 0x0, 0x8, 0xe]

    return True if sbox[xx] == yy else False

def verify_sbox_layer(x, y):
    flag = True
    for i in range(0, 16):
        if not verify_sbox(x[(4 * i) : (4 * i + 4)], y[(4 * i) : (4 * i + 4)]):
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

def verify_xor_layer(x, k, y, r):
    flag = True
    for i in range(0, 16):
        if ((x[4 * i] ^ k[i]) != y[4 * i]):
            flag = False
            break
        if ((x[4 * i + 1] ^ k[i + 16]) != y[4 * i + 1]):
            flag = False
            break

    gift64_rc = [0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3E, 0x3D, 0x3B, 0x37, 0x2F, 0x1E, 0x3C, 0x39, 0x33, 0x27, 0x0E,
            0x1D, 0x3A, 0x35, 0x2B, 0x16, 0x2C, 0x18, 0x30, 0x21, 0x02, 0x05, 0x0B, 0x17, 0x2E, 0x1C, 0x38]
    rb = r + 16
    if (x[3] ^ ((gift64_rc[rb] >> 0) & 0x1)) != y[3]:
        flag = False
    if (x[7] ^ ((gift64_rc[rb] >> 1) & 0x1)) != y[7]:
        flag = False
    if (x[11] ^ ((gift64_rc[rb] >> 2) & 0x1)) != y[11]:
        flag = False
    if (x[15] ^ ((gift64_rc[rb] >> 3) & 0x1)) != y[15]:
        flag = False
    if (x[19] ^ ((gift64_rc[rb] >> 4) & 0x1)) != y[19]:
        flag = False
    if (x[23] ^ ((gift64_rc[rb] >> 5) & 0x1)) != y[23]:
        flag = False
    if (x[63] ^ ((gift64_rc[rb] >> 6) & 0x1)) != y[63]:
        flag = False

    for i in range(0, 16):
        for j in range(0, 2):
            if ((4 * i + 2 + j) not in [3, 7, 11, 15, 19, 23, 63]):
                if (x[4 * i + 2 + j] != y[4 * i + 2 + j]):
                    flag = False
                    break
        if not flag:
            break
    return flag

def verify_xor_layer_mfold(x, k, y, r, m):
    flag = True
    for i in range(0, m):
        if not verify_xor_layer(x[i], k[i], y[i], r):
            flag = False
            break
    return flag

def verify_pbox(x):
    pbox = [0, 17, 34, 51, 48, 1, 18, 35, 32, 49, 2, 19, 16, 33, 50, 3,
            4, 21, 38, 55, 52, 5, 22, 39, 36, 53, 6, 23, 20, 37, 54, 7,
            8, 25, 42, 59, 56, 9, 26, 43, 40, 57, 10, 27, 24, 41, 58, 11,
            12, 29, 46, 63, 60, 13, 30, 47, 44, 61, 14, 31, 28, 45, 62, 15]
    y = [0 for i in range(0, 64)]
    for i in range(0, 64):
        y[i] = x[pbox[i]]
    return y

def verify_pbox_mfold(x, m):
    y = []
    for i in range(0, m):
        y.append(verify_pbox(x[i]))
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
    x = [[0 for i in range(0, len(var[0]))] for m in range(0, len(var))]
    for m in range(0, len(var)):
        for i in range(0, len(var[0])):
            x[m][i] = value_dict[var[m][i]]
    return x

def verify_solution(res, total_round):
    value_dict = get_dict(res)

    x = get_value(var_declare_mfold("x", 0, 64, 4), value_dict)

    curr_var = get_value(var_declare_mfold("k", 0, 128, 4), value_dict)

    for r in range(0, total_round):
        y = get_value(var_declare_mfold("y", r, 64, 4), value_dict)
        flag = verify_xor_layer_mfold(x, curr_var, y, r, 4)
        assert(flag)

        x1 = get_value(var_declare_mfold("x", r + 1, 64, 4), value_dict)
        px1 = verify_pbox_mfold(x1, 4)
        flag = verify_sbox_layer_mfold(y, px1, 4)
        assert(flag)

        addk = get_value(var_declare_mfold("addk", r, 32, 4), value_dict)
        curr_var = [curr_var[0][32 : 128] + addk[0], curr_var[1][32 : 128] + addk[1],
                curr_var[2][32 : 128] + addk[2], curr_var[3][32 : 128] + addk[3]]
        x = x1

    y = get_value(var_declare_mfold("y", total_round, 64, 4), value_dict)
    flag = verify_xor_layer_mfold(x, curr_var, y, r, 4)
    assert(flag)

    print("verify pass")

################################################################

def call_solver(thread_num, solve_file, total_round):
    stp_parameters = ["stp", "--CVC", "--cryptominisat", "--thread", str(thread_num), solve_file]
    res = subprocess.check_output(stp_parameters)
    res = res.replace("\r", "")[0:-1]
    #print(res)
    if (res != "Valid."):
        verify_solution(res, total_round)
    return True if res == "Valid." else False
