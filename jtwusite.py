# -*- coding: utf-8 -*-
from flask import Flask, request, session, jsonify, render_template, redirect, url_for
import os
import json
import time
import datetime
import codecs
import schemamgr
import gencalc2
import vocabulary

def create_app():
    app = Flask(__name__)
    app.secret_key = 'welcome to jiangtaowu.com'
    app.config['SESSION_TYPE'] = 'filesystem'
    #app.config.from_object(config_class)
    #app.config.from_object('config')
    #db.init_app(app)
    #migrate.init_app(app, db)
    #app.register_blueprint(vocabulary.bp_vocabulary)
    vocabulary.init_app(app)
    return app

app = create_app()


"""
提供20以内口算练习题自动生成服务
"""
@app.route('/class1')
@app.route('/class1/<schema_name>', methods=['GET','POST'])
def generate_math_exercise(schema_name=""):
    try:
        CALC_TEMPLATES = schemamgr.load_templates()
        schemas = [k for k in CALC_TEMPLATES["TEMPLATE_L1"]]
        if not schema_name:
            schema_name = schemas[2]
        output = gencalc2.gen_exercise(schema_name)
        if request.method=='POST':
            return render_template('grade1expr_block.html', data_contents = output)
        else:
            return render_template('grade1expr.html', CUR_SCHEMA_NAME = schema_name,
                                   IN_SCHEMAS = schemas,
                                   data_contents = output)
    except:
        return ""

"""
提供Markdown写作服务
"""
@app.route('/md', methods=['GET', 'POST'])
def process_md():
    try:
        if request.method=='POST':
            #prepare filepath
            today = datetime.datetime.today()
            today = ['{0}'.format(today.year), '{0}'.format(today.month), '{0}'.format(today.day)]
            post_path = os.sep.join(['.','posts',today[0],today[1],today[2]])
            if not os.path.exists(post_path):
                os.makedirs(post_path)
            #get post data
            md = request.values["md"]
            filename = request.values["filename"]
            articlename = request.values["articlename"]
            tags = request.values["tags"]
            file_md = os.sep.join([post_path, filename+".md"])
            if not os.path.exists(file_md):
                with open(file_md, "w") as outf:
                    outf.write(md.encode("utf-8"))
                try:
                    return url_for("process_mdview", year=today[0],month=today[1],day=today[2],filename=filename)
                except Exception as e:
                    session['error_msg_404'] = e
                    return url_for("process_404")
            else:
                session['error_msg_404'] = "URL DOES NOT EXIST!"
                return url_for("process_404")
        else:
            return render_template('md.html', md_content="#Enjoy markdown editing", md_filename="your_filename")
    except Exception as ee:
        session['error_msg_404'] = ee
        return redirect(url_for("process_404"))

"""
Markdown 内容显示
"""
@app.route('/articles/<year>/<month>/<day>/<filename>')
def process_mdview(year,month,day,filename):
    filepath = os.sep.join(['.','posts',year,month,day,filename+".md"])
    if os.path.exists(filepath):
        f = codecs.open(filepath,"r","utf-8")
        return render_template("mdview.html", md_content=f.read())
    else:
        session['error_msg_404'] = "URL DOES NOT EXIST!"
        return redirect(url_for("process_404"))

"""
错误页面
"""
@app.route('/404')
def process_404():
    errinfo = session.get('error_msg_404',None)
    if errinfo:
        return render_template("404.html", err_msg=errinfo), 404
    return render_template("404.html"), 404

"""
@app.route('/test')
def process_test():
    return render_template('test.html')
"""

@app.route('/schemaeditor', methods=['GET'])
def schema_editor():
    if request.method == "GET":
        schema_name = request.args.get('name', "")
        if not schema_name:
            return render_template("bootstrap_basic.html",
                body_content=schemamgr.list_templates())
        params = schemamgr.prepare_schema_params(schema_name)
        return render_template("schemaeditor.html", **params)
    else:
        session['error_msg_404'] = "ONLY GET METHOD IS SUPPORT!"
        return redirect(url_for("process_404"))

@app.route('/templateeditor', methods=['GET', 'POST'])
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
            session['error_msg_404'] = "Unkown Error!"
            return redirect(url_for("process_404"))
    else:
        session['error_msg_404'] = "Unkown Error!"
        return redirect(url_for("process_404"))


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
