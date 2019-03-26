# -*- coding: utf-8 -*-
import random
import os
import yaml
import primaryschool.schemamgr as schemamgr

CLAC_OPERATIONS = {"+": lambda x, y: x+y,
    "-": lambda x,y: x-y,
    "*": lambda x,y: x*y,
    "/": lambda x,y: x/y}
"""
根据数字权重, 生成可能的候选列表
"""
def gen_default_candidates(ratios):
    return [k for k in ratios if ratios[k]>0]

"""
轮盘赌选择
ratio: {2: 2, 3: 2, 4: 5, 5: 5}
ratio: {"+":0.8, "-":0.2, "*":0, "/":0}
"""
def round_robbin_choose(ratio_dict):
    cand_ratios = [(k,ratio_dict[k]) for k in ratio_dict if ratio_dict[k]>0]
    sum_ratios = [sum([x[1] for x in cand_ratios[:i+1]]) for i in range(len(cand_ratios))]
    sum_ratios = [1.0*r/sum_ratios[-1] for r in sum_ratios]
    #轮盘赌
    r = random.random()
    for i in range(len(sum_ratios)):
        if r<sum_ratios[i]:
            return cand_ratios[i][0]
    return None

"""
根据给定权重, 在candidates中选择一个数字
"""
def choose_from_candidate(ratios, candidates):
    #计算各数字的概率, 无权重的数字排除
    cand_ratios = {k:ratios[k] for k in ratios if k in candidates and ratios[k]>0}
    if cand_ratios:
        return round_robbin_choose(cand_ratios)
    return None

"""
根据当前算式, 计算应该排除的后续扩充算式
当前  12 - 3
后续应该排除   - 12  以及 + 3
"""
def gen_exclude_dict(op, a, b):
    d = {}
    if op=="+":
        d["-"] = [a, b]
    elif op=="-":
        d["-"] = [a]
        d["+"] = [b]
    elif op=="*":
        d["/"] = [a, b]
    elif op=="/":
        d["/"] = [a]
        d["*"] = [b]
    return d

def choose_another_number(CALC_TEMPLATES, templ_name, a, exclude_dict):
    if templ_name not in CALC_TEMPLATES["TEMPLATE_L2"]:
        return None
    thetempl = CALC_TEMPLATES["TEMPLATE_L2"][templ_name]
    #运算结果是否在指定范围
    def _is_res_inrange(op, a, b):
        res_min = thetempl["RES_MIN"]
        res_max = thetempl["RES_MAX"]
        if op in CLAC_OPERATIONS:
            res = CLAC_OPERATIONS[op](a,b)
            if res>=res_min and res<=res_max:
                return True
        return False
    #是否产生了进位
    def _is_res_addin(op, a, b):
        if op=="+":
            return True if a%10 + b%10 >= 10 else False
        elif op=="-":
            return True if a%10 < b%10 else False
        else:
            return True
    #开始选择满足要求的数字
    #当所有candidates都消耗完之后, 返回None, 本次数字选择失败
    op_ratio = thetempl["RATIO_OP"]
    op_candidates = gen_default_candidates(op_ratio)
    num_ratio = thetempl["RATIO_NUM"]
    num_candidates = gen_default_candidates(num_ratio)
    need_addin = True if random.random()<thetempl["RATIO_ADDIN"] else False
    while True:
        #候选消耗完毕, 失败
        if not op_candidates or not num_candidates:
            return None
        op = choose_from_candidate(op_ratio, op_candidates)
        b = choose_from_candidate(num_ratio, num_candidates)
        #如果选择的数字在排除列表以内, 本轮失败
        if exclude_dict and op in exclude_dict and b in exclude_dict[op]:
            num_candidates.remove(b)
            continue
        #是否在结果范围内
        if not _is_res_inrange(op, a, b):
            num_candidates.remove(b)
            continue
        #是否满足进位要求
        if (need_addin and not _is_res_addin(op,a,b)) or (_is_res_addin(op,a,b) and not need_addin):
            num_candidates.remove(b)
            continue
        break
    return (op, a, b)

def gen_single_expr(CALC_TEMPLATES, templ_name):
    if templ_name not in CALC_TEMPLATES["TEMPLATE_L2"]:
        return None
    thetempl = CALC_TEMPLATES["TEMPLATE_L2"][templ_name]
    num_ratio = thetempl["RATIO_NUM"]
    num_candidates = gen_default_candidates(num_ratio)
    a = choose_from_candidate(num_ratio, num_candidates)
    res = choose_another_number(CALC_TEMPLATES, templ_name, a, None)
    if res:
        op, a, b = res
        return "{0} {1} {2} =".format(a, op, b)
    return None

def gen_concat_expr(CALC_TEMPLATES, templ_name):
    if templ_name not in CALC_TEMPLATES["TEMPLATE_L2"]:
        return None
    thetempl = CALC_TEMPLATES["TEMPLATE_L2"][templ_name]
    num_ratio = thetempl["RATIO_NUM"]
    num_candidates = gen_default_candidates(num_ratio)
    a = choose_from_candidate(num_ratio, num_candidates)
    res = choose_another_number(CALC_TEMPLATES, templ_name, a, None)
    if res:
        op, a, b = res
        exclude_dict = gen_exclude_dict(op, a, b)
        if op in CLAC_OPERATIONS:
            newa = CLAC_OPERATIONS[op](a, b)
            newres = choose_another_number(CALC_TEMPLATES, templ_name, newa, exclude_dict)
            if newres:
                newop, c, d = newres
                return "{0} {1} {2} {3} {4} =".format(a, op, b, newop, d)
        return None
    return None

def gen_exercise(schema_name):
    CALC_TEMPLATES = schemamgr.load_templates()
    if schema_name not in CALC_TEMPLATES["TEMPLATE_L1"]:
        return None
    theschema = CALC_TEMPLATES["TEMPLATE_L1"][schema_name]
    templ_name = theschema["L2"]
    table_size = theschema["TABLE"]
    allow_duplicate = theschema["ALLOW_DUPLICATE"]
    row, col = table_size[0], table_size[1]
    concat_type = 0
    if "POSITION_CONCATE" in theschema:
        concat_pos = theschema["POSITION_CONCATE"]
        concat_type = 1
    elif "RATIO_CONCATE" in theschema:
        concat_ratio = theschema["RATIO_CONCATE"]
        if concat_ratio>0:
            concat_type = 2
    #start
    history = []
    final_list = []
    for i in range(row):
        row_list = []
        for j in range(col):
            while True:
                if concat_type==0:
                    res = gen_single_expr(CALC_TEMPLATES, templ_name)
                elif concat_type==1:
                    pos = i*4+j
                    if pos in concat_pos:
                        res = gen_concat_expr(CALC_TEMPLATES, templ_name)
                    else:
                        res = gen_single_expr(CALC_TEMPLATES, templ_name)
                elif concat_type==2:
                    if random.random()<concat_ratio:
                        res = gen_concat_expr(CALC_TEMPLATES, templ_name)
                    else:
                        res = gen_single_expr(CALC_TEMPLATES, templ_name)
                #本次是否成功
                if not res:
                    continue
                if not allow_duplicate and res in history:
                    continue
                history.append(res)
                row_list.append(res)
                break
        final_list.append(row_list)
    return final_list
