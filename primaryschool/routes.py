# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, url_for, redirect, session, jsonify
import exercisegenerator as exegen
import schemamgr

primaryschool_bp = Blueprint("school", __name__, template_folder="templates")

@primaryschool_bp.route('/schema', methods=['GET'])
def schema_editor():
    if request.method == "GET":
        schema_name = request.args.get('name', "")
        if not schema_name:
            return render_template("bootstrap_basic.html",
                body_content=schemamgr.list_templates())
        params = schemamgr.prepare_schema_params(schema_name)
        return render_template("schemaeditor.html", **params)
    else:
        return jsonify(["ONLY GET METHOD IS SUPPORT!"])

@primaryschool_bp.route('/template', methods=['GET', 'POST'])
def template_editor():
    if request.method == "GET":
        templ_name = request.args.get('name', "")
        if not templ_name:
            return render_template("bootstrap_basic.html",
                body_content=schemamgr.list_templates())
        params = schemamgr.prepare_template_params(templ_name)
        return render_template("templateeditor.html", **params)
    elif request.method == "POST":
        templ_name = request.form.get("name")
        res = schemamgr.write_template(templ_name, request)
        if res:
            return render_template("bootstrap_basic.html",
                body_content=schemamgr.list_templates())
        else:
            return jsonify(["Unkown Error!"])
    else:
        return jsonify(["Unkown Error!"])


"""
提供20以内口算练习题自动生成服务
"""
@primaryschool_bp.route('/')
@primaryschool_bp.route('/<schema_name>', methods=['GET','POST'])
def generate_math_exercise(schema_name=""):
    try:
        CALC_TEMPLATES = schemamgr.load_templates()
        schemas = [k for k in CALC_TEMPLATES["TEMPLATE_L1"]]
        if not schema_name:
            schema_name = schemas[2]
        output = exegen.gen_exercise(schema_name)
        if request.method=='POST':
            return render_template('grade1expr_block.html', data_contents = output)
        else:
            return render_template('grade1expr.html', CUR_SCHEMA_NAME = schema_name,
                                   IN_SCHEMAS = schemas,
                                   data_contents = output)
    except Exception as e:
        return jsonify(["Unknown error!"])
