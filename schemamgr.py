# -*- coding: utf-8 -*-
import os
import yaml

"""
加载配置
"""
def load_templates():
    #开始加载配置
    filename = os.sep.join([".","models","calcmodel.yaml"])
    if os.path.exists(filename):
        templs = yaml.load(open(filename))
        return templs
    else:
        return None

def prepare_schema_params(schema_name):
    thetemplates = load_templates()
    theschema = thetemplates["TEMPLATE_L1"][schema_name] if schema_name in thetemplates["TEMPLATE_L1"] else None
    if not theschema:
        return None
    params = dict()
    params["IN_SCHEMA_NAME"] = schema_name
    params["IN_TEMPL_NAMES"] = [k for k in thetemplates["TEMPLATE_L2"]]
    params["CUR_TEMPL_NAME"] = theschema["L2"]
    params["IN_ROW_NUM"] = theschema["TABLE"][0]
    params["IN_COL_NUM"] = theschema["TABLE"][1]
    params["IN_ALLOW_DUPLICATE"] = theschema["ALLOW_DUPLICATE"]
    params["IN_RATIO_CONCATE"] = theschema["RATIO_CONCATE"] if "RATIO_CONCATE" in theschema else ""
    params["IN_POSITION_CONCATE"] = ",".join(map(str,theschema["POSITION_CONCATE"])) if "POSITION_CONCATE" in theschema else ""
    return params

def prepare_template_params(templ_name):
    thetemplates = load_templates()
    themodel = thetemplates["TEMPLATE_L2"][templ_name] if templ_name in thetemplates["TEMPLATE_L2"] else None
    if not themodel:
        return None
    params = dict()
    params["IN_TEMPLATE_NAME"] = templ_name
    params["IN_NUM_MIN"] = themodel["NUM_MIN"]
    params["IN_NUM_MAX"] = themodel["NUM_MAX"]
    params["IN_RES_MIN"] = themodel["RES_MIN"]
    params["IN_RES_MAX"] = themodel["RES_MAX"]
    params["IN_OP_PLUS"] = themodel["RATIO_OP"]["+"]
    params["IN_OP_MINUS"] = themodel["RATIO_OP"]["-"]
    params["IN_OP_MUL"] = themodel["RATIO_OP"]["*"]
    params["IN_OP_DIV"] = themodel["RATIO_OP"]["/"]
    params["IN_ADDIN"] = themodel["RATIO_ADDIN"]
    params["IN_RATIO_NUM"] = themodel["RATIO_NUM"]
    candidate_nums = sorted([n for n in themodel["RATIO_NUM"]])
    params["IN_CANDIDATE_NUMS"] = candidate_nums
    return params

def write_template(templ_name, request):
    try:
        num_min = int(request.form.get("num_min"))
        num_max = int(request.form.get("num_max"))
        res_min = int(request.form.get("res_min"))
        res_max = int(request.form.get("res_max"))
        ratio_op_plus = request.form.get("op_plus")
        ratio_op_minus = request.form.get("op_minus")
        ratio_op_mul = request.form.get("op_mul")
        ratio_op_div = request.form.get("op_div")
        ratio_addin = request.form.get("addin")
        ratio_nums = request.form.get("ratio")
        ratio_nums = [int(n) for n in ratio_nums.split(",")]
        ratio_numd = dict()
        for i in range(num_min, num_max+1):
            ratio_numd[i] = ratio_nums[i-num_min]
        newmodel = {"NUM_MIN": num_min,
                    "NUM_MAX": num_max,
                    "RES_MIN": res_min,
                    "RES_MAX": res_max,
                    "RATIO_ADDIN": float(ratio_addin),
                    "RATIO_OP": {"+": float(ratio_op_plus),
                        "-": float(ratio_op_minus),
                        "*": float(ratio_op_mul),
                        "/": float(ratio_op_div)},
                    "RATIO_NUM": ratio_numd }
        #write data to file
        thetemplates = load_templates()
        thetemplates["TEMPLATE_L2"][templ_name] = newmodel
        filename = os.sep.join([".","models","calcmodel.yaml"])
        with open(filename,"w") as outf:
            yaml.safe_dump(thetemplates, outf, encoding="utf-8", allow_unicode=True)
        return True
    except Exception as e:
        return False

def list_templates():
    thetemplates = load_templates()
    if thetemplates:
        #list all schema
        html = ['<h1 align="center">Schemas</h1>']
        for k in thetemplates["TEMPLATE_L1"]:
            html.append('<h3 align="center"><a href="/schemaeditor?name={0}">{1}</a></h3>'.format(k,k))
        #list all templates
        html.append('<hr><h1 align="center">Templates</h1>')
        for k in thetemplates["TEMPLATE_L2"]:
            html.append('<h3 align="center"><a href="/templateeditor?name={0}">{1}</a></h3>'.format(k,k))
        return ''.join(html)
    else:
        return '<h1 align="center">No Schema or Template Exists!</h1>'
