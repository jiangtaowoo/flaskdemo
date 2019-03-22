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
        html = ""
        title_fmt = u"<h2 class='fiction_title'>{0}</h2>"
        chapter_fmt = u"<h3 class='fiction_chapter'>{0}</h3>"
        paragraph_fmt = u"<p class='fiction_paragraph'>{0}</p>"
        def format_one_line(line):
            fmt = paragraph_fmt
            flags = {"ARITICLE_TITLE:": title_fmt, "CHAPTER_TITLE:":chapter_fmt}
            for flag in flags:
                if flag in line:
                    return flags[flag].format(line.split(flag)[1].strip())
            return fmt.format(line)
        with codecs.open(filepath, "r", encoding="utf-8") as infile:
            content = infile.read()
            content = re.sub(r'(\r\n)+', '\n', content)
            content = re.sub(r'(\n)+', '\n', content)
            content = content.strip().split("\n")
            #title = u"<h4>{0}</h4>".format(content[0])
            content = u"".join([format_one_line(x) for x in content])
            html = content
        return html
    else:
        return ""

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
