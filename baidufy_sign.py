# -*- coding: utf-8 -*-
#import re
import struct

#def convert_to_list(srcdata):
#    return srcdata[:] if isinstance(srcdata, list) else list(srcdata)

def shift_data(input_data,ind_str):
    for idx in range(0, len(ind_str)-2, 3):
        op_ind = ind_str[idx+2]
        shift_bits = ord(op_ind)-87 if op_ind>='a' else int(op_ind)
        data_shifted = input_data >> shift_bits if '+'==ind_str[idx+1] else input_data << shift_bits
        input_data = input_data+data_shifted&4294967295 if '+'==ind_str[idx] else input_data^data_shifted
    return input_data

def calc_sign(input_str, window_gtk="320305.131321201"):
    #SURROGATES_PAIR = re.compile(u"[\uD800-\uDBFF][\uDC00-\uDFFF]", re.U)
    #SURROGATES_PAIR = re.compile(u"[\ud800-\udbff][\udc00-\udfff]", re.U)
    #match_result = re.findall(SURROGATES_PAIR,input_str)
    #if match_result is None or len(match_result)==0:
    def get_surrogate_pair(s):
        bs = bytearray(s, "utf-16-be")
        return struct.unpack('>HH', bs)
    if len(input_str)>30:
        mid_start = int(len(input_str)/2)-5
        input_str = '' + input_str[0:10] + input_str[mid_start:mid_start+10] + input_str[-10:]
    """
    else:
        splited_str = re.split(SURROGATES_PAIR, input_str)
        f = []
        for idx in range(0, len(splited_str)):
            if '' != splited_str[idx]:
                #f.extend(convert_to_list(list(splited_str[idx])))
                f.extend(list(splited_str[idx]))
            if idx != len(splited_str)-1:
                f.append(match_result[idx])
        if len(f)>30:
            mid_start = int(len(f)/2)
            input_str = ''.join(f[0:10]) + ''.join(f[mid_start-5:mid_start+5]) + ''.join(f[-10:])
    """
    gtk_s = window_gtk.split('.')
    gtk_h, gtk_l = int(gtk_s[0]), int(gtk_s[1])
    S_codelist = []
    codeidx = 0
    #suridx = -1
    for idx, item_char in enumerate(input_str):
        #if idx<=suridx:
        #    continue
        suridx = idx
        A = ord(item_char)
        if A>=0x10000 and A<=0x10FFFF:
            A, A_pair = get_surrogate_pair(item_char)
        if A<128:
            if codeidx>=len(S_codelist):
                S_codelist.append(None)
            S_codelist[codeidx] = A
            codeidx += 1
        else:
            if A<2048:
                if codeidx>=len(S_codelist):
                    S_codelist.append(None)
                S_codelist[codeidx] = A >> 6 | 192
                codeidx += 1
            else:
                #if 55296==(64512&A) and idx+1<len(input_str) and 56320==(64512&ord(input_str[idx+1])):
                if 55296 == (64512 & A) and idx + 1 < len(input_str) and 56320 == (64512 & A_pair):
                    #suridx = idx + 1
                    #A = 65536 + ((1023 & A) << 10) + (1023 & ord(input_str[suridx]))
                    A = 65536 + ((1023 & A) << 10) + (1023 & A_pair)
                    if codeidx>=len(S_codelist):
                        S_codelist.append(None)
                    S_codelist[codeidx] = A >> 18 | 240
                    codeidx += 1
                    if codeidx>=len(S_codelist):
                        S_codelist.append(None)
                    S_codelist[codeidx] = A >> 12 & 63 | 128
                    codeidx += 1
                else:
                    if codeidx>=len(S_codelist):
                        S_codelist.append(None)
                    S_codelist[codeidx] = A >> 12 | 224
                    codeidx += 1
                if codeidx>=len(S_codelist):
                    S_codelist.append(None)
                S_codelist[codeidx] = A >> 6 & 63 | 128
                codeidx += 1
            if codeidx>=len(S_codelist):
                S_codelist.append(None)
            S_codelist[codeidx] = 63 & A | 128
            codeidx += 1
    shift_ind_F = '+-a^+6'
    shift_ind_D = '+-3^+b+-f'
    sign_code = gtk_h
    for idx, item_code in enumerate(S_codelist):
        sign_code += item_code
        sign_code = shift_data(sign_code, shift_ind_F)
    sign_code = shift_data(sign_code, shift_ind_D)
    sign_code ^= gtk_l
    if sign_code<0:
        sign_code = (2147483647 & sign_code) + 2147483648
    sign_code %= 1000000
    return str(sign_code) + '.' + str(sign_code ^ gtk_h)
