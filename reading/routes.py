# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from flask import Blueprint, render_template, request, url_for, redirect, session, jsonify
from vocabulary.api import session as transession
from . import contentloader

reading_bp = Blueprint("reading", __name__, template_folder="templates", static_folder="static")
trans_sess = transession()

@reading_bp.route('/', methods=['GET','POST'])
def start_read():
    art_name = request.args.get("artname", "")
    default_f = "pg146.txt"
    if art_name=="prideandprejudice":
        default_f = "pridedemo.txt"
    c = contentloader.txtToHtmlReading(default_f)
    #c = contentloader.urlToHtmlReading("http://www.gutenberg.org/files/146/146-h/146-h.htm")
    return render_template("reading.html", fiction_content=c)
