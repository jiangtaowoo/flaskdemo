# -*- coding: utf-8 -*-
import transapi
import json
import gencalc
from flask import Flask, request, jsonify, render_template
app = Flask(__name__)
trans_obj = transapi.BDTranslation()

@app.route('/vocabulary/<word>')
def process_trans(word):
    try:
        res = trans_obj.single_translate(word)
        res['result'] = 'success'
        return jsonify(res)
    except:
        return jsonify({'result':'fail'})

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
    except Exception,why:
        print(why)
        return ""

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8080)
