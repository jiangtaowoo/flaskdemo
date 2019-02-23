# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, url_for, redirect, session, jsonify
from .api import session as transession

vocabulary_bp = Blueprint("vocabulary", __name__, template_folder="templates", static_folder="static")
trans_sess = transession()

@vocabulary_bp.route('/', methods=['GET','POST'])
def lookup_word():
    if request.method=="POST":
        pattern = request.form.get('word')
        if not pattern and request.json and 'word' in request.json:
            pattern = request.json['word']
        if pattern:
            cards = trans_sess.query(pattern.strip())
            return jsonify(cards)
        else:
            return jsonify([])
    else:
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
