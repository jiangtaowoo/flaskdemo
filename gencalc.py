# -*- coding: utf-8 -*-
import random

def set_weight(maxsum):
    if not (maxsum==10 or maxsum==20):
        return None
    #设置各个数字的概率
    rate = {0:[0,1,20], 2:[2,3,17,18,19], 5:[10,11,12,13,14,15,16], 10:[4,5,6,7,8,9]}
    rate_num = dict()
    rate_sum = [0,0]
    for k, v in rate.items():
        for i in v:
            rate_num[i] = k
            if i<10:
                rate_sum[0] += k
            rate_sum[1] += k
    #计算各个数字的概率
    acc = 0
    weights = []
    rate_s = rate_sum[maxsum/10-1]
    for i in range(0,maxsum):
        acc += rate_num[i]
        weights.append(1.0*acc/rate_s)
    return weights

def choose_num(weights):
    r = random.random()
    for i in range(0,len(weights)):
        if r<weights[i]:
            return i

# 20以内的加减法
## 1.随机生成 3*20 = 60 道 10以内的加减法题目# 10以内的加减法, plusratio为产生加法算式的几率, addinrate为进位的几率, mixrate为混合连加连减几率
def gen_exercise(minsum, maxsum, weights, plusrate=0.9, addinrate=0.8, mixrate=0.3):
    #给定数字a, 选择满足要求的数字b
    def _choose_another(a, op, addr, fixed_pos=False):
        while True:
            b = choose_num(weights)
            if op=="+":
                if a+b>=minsum and a+b<=maxsum:
                    if a<2:
                        break
                    elif not addr or a>=10:
                        break
                    elif a<10 and b<10 and a+b>=10:
                        break
            else:
                ab_exchange = False
                if a<b:
                    if not fixed_pos:
                        a, b = b, a
                        ab_exchange = True
                    else:
                        continue
                elif a>b and a>18:
                    break
                if not addr or a<=10:
                    break
                elif a>10 and b<10 and b>a%10:
                    break
                #not sucess this time, and a,b exchange, need to roll back
                if ab_exchange:
                    a, b = b, a
        return a, b
    def _secure_op(a, op):
        if a>15:
            return "-"
        elif a<6:
            return "+"
        else:
            return op
    #先确定加法或是减法
    op = "+" if random.random()<plusrate else "-"
    addr = True if maxsum>10 and random.random()<addinrate else False
    #是否生成连加连减
    mixr = True if maxsum>10 and random.random()<mixrate else False
    #开始算式选择
    #随机生成第一个数a
    a = choose_num(weights)
    op = _secure_op(a, op)
    a, b = _choose_another(a, op, addr)
    if not mixr:
        return "{0}     {1}     {2} = ".format(a,op,b)
    else:
        c = a+b if op=="+" else a-b
        newop = "+" if random.random()<0.5 else "-"
        newop = _secure_op(c, newop)
        newaddr = True if maxsum>10 and random.random()<addinrate else False
        c, d = _choose_another(c, newop, newaddr, True)
        return "{0} {1} {2} {3} {4} = ".format(a,op,b,newop,d)

def genexpr(minsum, maxsum, weights, delimiter="\t", duplicated=False):
    history = []
    output = []
    for i in range(0,25):
        succ = 0
        while True:
            expr = gen_exercise(minsum, maxsum, weights)
            if duplicated:
                history.append(expr)
                succ += 1
            if expr not in history:
                history.append(expr)
                succ += 1
            if succ>=4:
                break
        #print(history[-4]+delimiter+history[-3]+delimiter+history[-2]+delimiter+history[-1])
        if delimiter:
            output.append(delimiter.join(history[-4:]))
        else:
            output.append(history[-4:])
    return output

weights = [set_weight(10),set_weight(20)]
#genexpr(7,20,weights,"|")
