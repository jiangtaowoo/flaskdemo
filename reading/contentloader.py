# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import os
import inspect
import codecs
import re
import requests

cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def txtToHtmlReading(filename):
    filepath = os.sep.join([cur_dir, "static", "contents", filename])
    if os.path.exists(filepath):
        html = u""
        with codecs.open(filepath, "r", encoding="utf-8") as infile:
            content = infile.read()
            content = re.sub(r'(\r\n)+', '\n', content)
            content = re.sub(r'(\n)+', '\n', content)
            content = content.strip().split("\n")
            content = u"".join([u"<p class='vreading_content'>{0}</p>".format(x) if u"chapter" not in x.lower() else u"<h4 class='vreading_title'>{0}</h4>".format(x) for x in content])
            html = content
        return html
    else:
        return u""

def urlToHtmlReading(url):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/72.0.3626.121 Chrome/72.0.3626.121 Safari/537.36"}
    sess = requests.session()
    rsp = sess.get(url, headers=headers)
    if rsp.status_code==200:
        rsp = sess.get(url, headers=headers)
        if rsp.status_code==200:
            content = rsp.text
            if "<body" in content:
                m = re.search("<body.*</body>", content, re.I|re.S|re.M)
                if m:
                    content = "<div" + content[m.start():m.end()][5:-5] + "div>"
                    return content
    return ""
