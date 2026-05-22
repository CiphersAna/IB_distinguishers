#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy
import time
from multiprocessing import Process, Manager

import build_model
import proba1propagation

def determine_IB(r_begin, r_end, b, e, bk, ek, solve_file, thread_num):
    flag = False
    build_model.build_model2file(r_begin, r_end, b, e, bk, ek, solve_file)
    flag = build_model.call_solver(thread_num, solve_file, r_begin, r_end)
    return flag

def format_out(hmk, tmk, hrkey, trkey, hinit_state, hfini_state, tinit_state, tfini_state):
    statement = ""
    statement += "hmk:\n"
    for i in range(0, 8):
        statement += "{}\n".format(hmk[(32 * i) : (32 * i + 32)])
    statement += "hrkey:\n"
    for k in hrkey:
        statement += "{}\n".format(k)
    statement += "tmk:\n"
    for i in range(0, 8):
        statement += "{}\n".format(tmk[(32 * i) : (32 * i + 32)])
    statement += "trkey:\n"
    for k in trkey:
        statement += "{}\n".format(k)
    statement += "htini_state:\n"
    statement += "{}\n".format(hinit_state)
    statement += "hfini_state:\n"
    statement += "{}\n".format(hfini_state)
    statement += "tinit_state:\n"
    statement += "{}\n".format(tinit_state)
    statement += "tfini_state:\n"
    statement += "{}\n".format(tfini_state)
    return statement

def search_IBs():

    dir0 = "Results"
    dir1 = "Results/CHAM128_256more"
    if not os.path.exists(dir0):
        os.makedirs(dir0)
    if not os.path.exists(dir1):
        os.makedirs(dir1)

    search_round = 8
    distinguisher_count = 0
    d_br = 0
    h_round = 10
    d_round = search_round
    t_round = 10

    tt0 = time.time()

    hast = []
    while True:
        hstatement, hflag, hmk, hrkey, hinit_state, hfini_state, hrp = proba1propagation.search_proba1_header(d_br, d_br + h_round, hast)
        if hflag:
            break
        hast.append(hrp)
    print("number of hast {}".format(len(hast)))

    tast = []
    while True:
        tstatement, tflag, tmk, trkey, tinit_state, tfini_state, trp = proba1propagation.search_proba1_trailer(d_br + h_round + d_round, d_br + h_round + d_round + t_round, tast)
        if tflag:
            break
        tast.append(trp)
    print("number of tast {}".format(len(tast)))


    hast = []
    while True:

        statement, hflag, hmk, hrkey, hinit_state, hfini_state, hrp = proba1propagation.search_proba1_header(d_br, d_br + h_round, hast)
        hast.append(hrp)
        if hflag:
            break

        tast = []
        while True:
            statement, tflag, tmk, trkey, tinit_state, tfini_state, trp = proba1propagation.search_proba1_trailer(d_br + h_round + d_round, d_br + h_round + d_round + t_round, tast)
            tast.append(trp)
            if tflag:
                break

            solve_file = "{}/{}".format(dir1, "model_r{}.stp".format(d_round))
            result_file = "{}/{}".format(dir1, "model_r{}.txt".format(d_round))

            t1 = time.time()
            flag = determine_IB(d_br + h_round, d_br + h_round + d_round, hfini_state, tinit_state, hmk, tmk, solve_file, 1)
            t2 = time.time()
            if flag:
                print(hstatement)
                print("\n\n\n")
                print(tstatement)
                print("\n\n\n")
                distinguisher_count += 1

            print(h_round, d_round, t_round, flag, t2 - t1)
            print("############\n\n\n")
            if flag:
                f = open(result_file, "a")
                f.write("Count {}\nCost {}, we find {}-round ({}, {}, {}) distinguisher\n".format(distinguisher_count, t2 - t1, h_round + t_round + search_round, h_round, search_round, t_round))
                f.write(format_out(hmk, tmk, hrkey, trkey, hinit_state, hfini_state, tinit_state, tfini_state))
                f.close()
    tt1 = time.time()
    f = open(result_file, "a")
    f.write("######\n\nTotal time is {}".format(tt1 - tt0))
    f.close()

if __name__ == "__main__":
    search_IBs()
