#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy
import time
from multiprocessing import Process, Manager

import build_model
import search_params

def determine_IB(r_begin, r_end, b, e, bk, ek, m, solve_file, thread_num):
    build_model.build_model2file(r_begin, r_end, b, e, bk, ek, m, solve_file)
    return build_model.call_solver(thread_num, solve_file, r_begin, r_end, m)

def __search_IBs_process(share_dict, search_space, search_round, process_index, thread_num):

    dir0 = "Results"
    dir1 = "Results/SKINNY_{}".format(search_round)
    dir2 = dir1 + "/process{}".format(process_index)
    if not os.path.exists(dir0):
        os.makedirs(dir0)
    if not os.path.exists(dir1):
        os.makedirs(dir1)
    if not os.path.exists(dir2):
        os.makedirs(dir2)

    solve_file = "{}/{}".format(dir2, "model_r{}.stp".format(search_round))
    result_file = "{}/{}".format(dir2, "model_r{}.txt".format(search_round))

    distinguisher_count = 0
    search_count = 0
    total_search_count = len(search_space)

    f = open(result_file, "w")

    at1 = time.time()
    for each_search in search_space:
        search_count += 1
        b = each_search[0]
        e = each_search[1]
        bk = each_search[2]
        ek = each_search[3]
        m = 4
        t1 = time.time()
        flag = determine_IB(10, 10 + search_round, b, e, bk, ek, 4, solve_file, thread_num)
        t2 = time.time()
        print(search_count, total_search_count, flag, t2 - t1)
        if flag:
            distinguisher_count += 1
            f.write("Cost time {}, distinguisher count {}\n".format(t2 - t1, distinguisher_count))
            f.write(str(each_search) + "\n\n\n")
    at2 = time.time()
    f.write("Cost {}, we find {} {}-round distinguishers".format(at2 - at1, distinguisher_count, search_round))
    f.close()
    share_dict[str(process_index)] = distinguisher_count

def search_IBs_process(search_round):
    params = search_params.search_param_bit(search_round)
    process_num = 32
    search_space = params["search_space"]
    partion = len(search_space) // process_num
    tt1 = time.time()
    with Manager() as manager:
        shared_dict = manager.dict()
        processes = []
        for i in range(0, process_num):
            search_space_process = copy.deepcopy(search_space[partion * i : partion * (i + 1)])
            p = Process(target=__search_IBs_process, args=(shared_dict, search_space_process, search_round, i, params["thread_num"]))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        tt2 = time.time()
        total_distinguisher_num = 0
        for i in range(0, process_num):
            total_distinguisher_num += shared_dict[str(i)]
        result = "Results/SKINNY_{}/result.txt".format(search_round)
        f = open(result, "w")
        f.write("Cost {}, find {} {}-round IBs\n".format(tt2 - tt1, total_distinguisher_num, search_round))
        f.close()

if __name__ == "__main__":
    search_IBs_process(7)
