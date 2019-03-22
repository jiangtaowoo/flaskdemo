# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from flask import Blueprint, render_template, request, url_for, redirect, session, jsonify
from vocabulary.api import session as transession
from . import contentloader

reading_bp = Blueprint("reading", __name__, template_folder="templates", static_folder="static")
trans_sess = transession()
contents = {"pride": "pride_and_prejudice.txt", "princess": "little_princess.txt"}

def isMobile(headers):
    mobiles = ["ipad", "iphone", "android"]
    headers = headers.lower()
    for m in mobiles:
        if m in headers:
            return True
    return False

@reading_bp.route('/', methods=['GET','POST'])
def start_read():
    cli_headers = request.headers.get('User-Agent')
    #print(cli_headers)
    art_name = request.args.get("artname", "")
    default_f = "pride_and_prejudice.txt"
    if art_name in contents:
        default_f = contents[art_name]
    c = contentloader.txtToHtmlReading(default_f)
    #c = contentloader.urlToHtmlReading("http://www.gutenberg.org/files/146/146-h/146-h.htm")
    if isMobile(cli_headers):
        return render_template("readingxs.html", fiction_content=c)
    else:
        return render_template("reading.html", fiction_content=c)
