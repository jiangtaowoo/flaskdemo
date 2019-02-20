# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, url_for, redirect, session, jsonify
from .api import session as transession

vocabulary_bp = Blueprint("vocabulary", __name__, template_folder="templates")
trans_sess = transession()

@vocabulary_bp.route('/', methods=['GET','POST'])
def lookup_word():
    if request.method=="POST":
        pattern = request.form.get('word')
        if not pattern:
            jcontent = request.json
            if jcontent and 'word' in jcontent:
                pattern = jcontent['word']
        cards = trans_sess.query(pattern.strip())
        #print(url_for("vocabulary.lookup_word"))
        return jsonify(cards)
        #return render_template("card_block.html", card_list=cards)
    else:
        """
        cards = []
        schemas = ["default", "simple", "vocabulary", "oxford", "full"]
        cur_schema= "default"
        """
        #return render_template("testx.html")
        return render_template("vocabulary.html")

@vocabulary_bp.route('/<word>', methods=['GET'])
def trans_word(word):
    try:
        word = word.strip().lower()
        res = trans_sess.translate(word)
        res["status"] = "success"
        return jsonify(res)
    except Exception as e:
        print(e)
        return jsonify({"status": "fail"})
