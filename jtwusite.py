# -*- coding: utf-8 -*-
from flask import Flask, request, session, jsonify, render_template, redirect, url_for
import os
import transapi
import json
import gencalc
import time
import datetime
import codecs

app = Flask(__name__)
app.secret_key = 'welcome to jiangtaowu.com'
app.config['SESSION_TYPE'] = 'filesystem'
trans_obj = transapi.BDTranslation()

"""
提供英文单词翻译服务
"""
@app.route('/vocabulary/<word>')
def process_trans(word):
    try:
        res = trans_obj.single_translate(word)
        res['status'] = 'success'
        return jsonify(res)
    except:
        return jsonify({'status':'fail'})

"""
提供20以内口算练习题自动生成服务
"""
@app.route('/class1')
@app.route('/class1/<maxsum>', methods=['GET','POST'])
def generate_math_exercise(maxsum=20):
    try:
        duplicated = False
        if int(maxsum)==10:
            minsum, maxsum = 5, 10
            duplicated = True
        else:
            minsum, maxsum = 7, 20
        output = gencalc.genexpr(minsum,maxsum,gencalc.weights[maxsum/10-1],None,duplicated)
        if request.method=='POST':
            return render_template('exprblk.html', data_contents = output)
        else:
            return render_template('calc.html', defaultisten=maxsum==10, data_contents = output)
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
                except Exception, e:
                    session['error_msg_404'] = e
                    return url_for("process_404")
            else:
                session['error_msg_404'] = "URL DOES NOT EXIST!"
                return url_for("process_404")
        else:
            return render_template('md.html', md_content="#Enjoy markdown editing", md_filename="your_filename")
    except Exception, ee:
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

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080, debug=True)
