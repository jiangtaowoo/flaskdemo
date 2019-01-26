# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
import transapi
import json
import gencalc
import time
import datetime

app = Flask(__name__)
trans_obj = transapi.BDTranslation()

@app.route('/vocabulary/<word>')
def process_trans(word):
    try:
        res = trans_obj.single_translate(word)
        res['status'] = 'success'
        return jsonify(res)
    except:
        return jsonify({'status':'fail'})

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
            return render_template('index.html', defaultisten=maxsum==10, data_contents = output)
    except:
        return ""

@app.route('/md', methods=['GET', 'POST'])
def process_md():
    try:
        if request.method=='POST':
            today = datetime.datetime.today()
            post_path = os.sep.join(['.','posts','{0}'.format(today.year), '{0}'.format(today.month), '{0}'.format(today.day)])
            os.makedirs(post_path)
            md = request.args.get('md')
            html = request.args.get('html')
            filename = '{0}'.format(int(time.time()))
            file_md = '.'.join([filename, 'md'])
            file_html = '.'.join([filename, 'html'])
            with open(os.sep.join([post_path, file_md]), 'w') as outf:
                outf.write(md.encode('utf-8'))
            with open(os.sep.join([post_path, file_html]), 'w') as outf:
                outf.write(html.encode('utf-8'))
            try:
                return url_for('/mdview', filename=file_html)
            except:
                return url_for('process_404')
        else:
            return render_template('md.html', md_content="#Title 1\n##Title 2")
    except:
        return redirect(url_for('process_404'))

@app.route('/mdview/<filename>')
def process_mdview(filename):
    today = datetime.datetime.today()
    post_path = os.sep.join(['.','posts','{0}'.format(today.year), '{0}'.format(today.month), '{0}'.format(today.day)])
    filepath = os.sep.join([post_path, filename])
    if os.path.exists(filepath):
        f = open(filepath)
        return render_template('mdview.html', md_content=f.read().encode('utf-8'))
    else:
        return redirect(url_for('process_404'))

@app.route('/notfound')
def process_404():
    return render_template('404.html')

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
