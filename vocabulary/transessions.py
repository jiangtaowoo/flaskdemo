# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import compat
import os
import inspect
import re
import json
import copy
import lxml.html
import datetime
import yaml
from collections import deque
import requests
from requests.models import Response as ReqResponse
import vocabulary.baidufy_sign as baidufy_sign
from metacls import Singleton
from vocabulary.renderer import WordModelRenderer

if compat.is_py2:
    from urllib import unquote
elif compat.is_py3:
    from urllib.parse import unquote

#sys.path.insert(1, os.path.join(sys.path[0],'..'))
import ormadaptor
#from .. import ormadaptor

cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

"""
configuration for different output
default is web_2_anki for iOS shortcut
"""
configuration = dict()
configuration["dbname"] = "vocabulary.db"
configuration["schema"] = "html_card"
configuration["queryweb"] = True
configuration["need_vocabulary"] = True
configuration["need_flashcard"] = True
configuration["log_success"] = True

def config_local_2_raw():
    configuration["schema"] = "database_raw"
    configuration["queryweb"] = False
    configuration["need_vocabulary"] = False
    configuration["need_flashcard"] = True
    configuration["log_success"] = False

def config_local_2_anki():
    configuration["schema"] = "html_card"
    configuration["queryweb"] = False
    configuration["need_vocabulary"] = False
    configuration["need_flashcard"] = True
    configuration["log_success"] = False

def config_local_2_html():
    configuration["schema"] = "html_card"
    configuration["queryweb"] = False
    configuration["need_vocabulary"] = False
    configuration["need_flashcard"] = True
    configuration["log_success"] = False

def config_web_2_raw():
    configuration["schema"] = "database_raw"
    configuration["queryweb"] = True
    configuration["need_vocabulary"] = True
    configuration["need_flashcard"] = True
    configuration["log_success"] = True

def config_web_2_anki():
    configuration["schema"] = "html_card"
    configuration["queryweb"] = True
    configuration["need_vocabulary"] = True
    configuration["need_flashcard"] = True
    configuration["log_success"] = True

def config_web_2_html():
    configuration["schema"] = "html_card"
    configuration["queryweb"] = True
    configuration["need_vocabulary"] = True
    configuration["need_flashcard"] = True
    configuration["log_success"] = True


def trans_log(logmsg):
    log_dir = os.sep.join([cur_dir, 'logs'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logfilename = os.sep.join([log_dir,u"trans_{0:%Y-%m-%d}.log".format(datetime.datetime.today())])
    with open(logfilename, 'a+') as outf:
        outf.write(u"{0}:\t{1}\n".format(datetime.datetime.now(),logmsg))


"""
翻译结果渲染
class VCardRenderer(object):
    __metaclass__ = Singleton

    def __init__(self):
        schema_filename = os.sep.join([cur_dir, "models", "renderschema.yaml"])
        res = VCardRenderer._build_schema_tree(schema_filename)
        self.schemas, self.schema_tree = res

    @staticmethod
    def _build_schema_tree(schema_file):
        if os.path.exists(schema_file):
            schemas = yaml.load(open(schema_file))
            #生成查询索引
            schema_tree = dict()
            if 'SHARED_STYLE' in schemas:
                style_avaliable = ['MAP_STYLE', 'RAW_STYLE']
                for style_x in style_avaliable:
                    if style_x in schemas['SHARED_STYLE']:
                        style_tree = schemas['SHARED_STYLE'][style_x]
                        for k in style_tree:
                            tree_k = u"SHARED_STYLE.{0}.{1}".format(style_x,k)
                            schema_tree[tree_k] = style_tree[k]
            if 'SCHEMAS' in schemas:
                schemas_cfg = schemas['SCHEMAS']
                for sc in schemas_cfg:
                    schema_tree[sc] = dict()
                    sc_inst = schemas_cfg[sc]
                    if 'TEMPLATES' in sc_inst:
                        sc_templ_inst = sc_inst['TEMPLATES']
                        for templ_name in sc_templ_inst:
                            tree_k = u"TEMPLATES.{0}".format(templ_name)
                            schema_tree[sc][tree_k] = sc_templ_inst[templ_name]
            return schemas, schema_tree
        return None

    @staticmethod
    def _meta_render(schema_node, data):

        渲染的情况分为:
        1. 为list数据进行渲染
           a. 方式一: list中的每个元素均采用一个模板渲染(RAW_STYLE)
           b. 方式二: list中的元素内容, 与渲染模板匹配, 根据匹配结果渲染
        2. 为dict数据进行渲染
           a. 方式一: 根据key匹配渲染模板, 将value按模板渲染
           b. 方式二: 根据key匹配渲染模板, 将key, value按模板渲染

        #只支持字符串渲染
        if not compat.is_str_or_unicode(data):
            return data
        if isinstance(schema_node, dict):
            #按字典匹配内容渲染
            if data in schema_node['match']:
                return compat.py23_2_unicode(schema_node['match'][data]).format(data)
            return compat.py23_2_unicode(schema_node['except']).format(data)
        return compat.py23_2_unicode(schema_node).format(data)

    @staticmethod
    def _iter_render(schema_tree, schema_name, schema_node, data):
        递归完成渲染
        1. type == raw, 直接 .format(data) 完成渲染
        2. type == style, 调用 basic_render 完成渲染
        3. type == template, 调用 _iter_render 递归完成渲染

        if not schema_node:
            return data
        if "delimiter" in schema_node:
            delimiter = schema_node["delimiter"]
            order = schema_node["order"]
            list_sc = schema_node["list_style"]
            dict_sc = schema_node["dict_style"]
            dict_sc_kv = schema_node["dict_style_kv"] if "dict_style_kv" in schema_node else None
            #获取元素
            if isinstance(data, dict):
                _get_item = lambda k, d: d[k].strip()
            elif isinstance(data, list):
                _get_item = lambda k, l: k.strip()
            else:
                _get_item = lambda x: x
            #没有渲染样式
            if not list_sc and not dict_sc and not dict_sc_kv:
                #非list,dict, 不做处理
                if not isinstance(data, list) and not isinstance(data, dict):
                    return data
                #dict 或者 list, 按要求完成连接
                return delimiter.join([_get_item(k,data) for k in data])
            #按列表或字典样式渲染
            if isinstance(data, list) and list_sc:
                result = []
                for item in data:
                    result.append(VCardRenderer._iter_render(schema_tree, schema_name, list_sc, item))
                return delimiter.join(result)
            elif isinstance(data, dict) and (dict_sc or dict_sc_kv):
                newdata = dict()
                #只处理在order列表中的数据, 如果没有order列表, 默认处理所有
                if not order:
                    order = [k for k in data]
                #result 存放结果
                result = []
                if dict_sc:
                    #value only 模式
                    for k in order:
                        if k in data:
                            if k not in dict_sc or not dict_sc[k]:
                                newdata[k] = data[k]
                            else:
                                schema_next_node = dict_sc[k]
                                newdata[k] = VCardRenderer._iter_render(schema_tree, schema_name, schema_next_node, data[k])
                    #再排序
                    for k in order:
                        if k in newdata:
                            result.append(newdata[k])
                elif dict_sc_kv:
                    #kv模式
                    for k in order:
                        if k in data:
                            schema_k = dict_sc_kv["key"]
                            schema_v = dict_sc_kv["value"]
                            schema_kvc = compat.py23_2_unicode(dict_sc_kv["kvconnector"])
                            rendered_k = VCardRenderer._iter_render(schema_tree, schema_name, schema_k, k)
                            rendered_v = VCardRenderer._iter_render(schema_tree, schema_name, schema_v, data[k])
                            result.append(schema_kvc.format(rendered_k, rendered_v))
                #最后连接
                return delimiter.join(result)
        elif "type" in schema_node:
            if schema_node["type"]=="raw":
                fmt = compat.py23_2_unicode(schema_node["data"])
                #if not isinstance(fmt, unicode):
                #    fmt = unicode(fmt,"utf-8")
                return fmt.format(data)
            elif schema_node["type"]=="style":
                style_k = schema_node["data"]
                style_node = schema_tree[style_k]
                return VCardRenderer._meta_render(style_node, data)
            elif schema_node["type"]=="template":
                #找到template对应的schema节点, 递归调用
                schema_next_node = schema_tree[schema_name][schema_node["data"]]
                return VCardRenderer._iter_render(schema_tree, schema_name, schema_next_node, data)

    @staticmethod
    def _render_schema_seg(schema_tree, schema_name, schema_seg, word, data):
        #inputdata is list or dict
        outer_node = schema_tree[schema_seg["outer"]["data"]] if "outer" in schema_seg and schema_seg["outer"] else None
        inner_node = schema_tree[schema_name][schema_seg["inner"]["data"]] if "inner" in schema_seg and schema_seg["inner"] else None
        highlight_node = schema_tree[schema_seg["highlight"]] if "highlight" in schema_seg else None
        #辅助函数
        def _prettify_str(inputs, theword, hilight_node):
            if not hilight_node:
                return inputs
            else:
                #change everything to unicode
                inputs = compat.py23_2_unicode(inputs)
                word_pattern = re.compile(theword, re.IGNORECASE)
                highlight_word = VCardRenderer._meta_render(hilight_node, theword)
                return word_pattern.sub(highlight_word, inputs)
        result = data
        if inner_node:
            result = VCardRenderer._iter_render(schema_tree, schema_name, inner_node, data)
        if outer_node:
            result = VCardRenderer._meta_render(outer_node, result)
        if highlight_node:
            result = _prettify_str(result, word, highlight_node)
        return result

    @staticmethod
    def present_basicpart(schemas, schema_tree, schema_name, vcardinst):
        res_dict = dict()
        word = vcardinst.word
        basicpart = vcardinst.gen_basic_data()
        schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
        #front, tag, transform, posp, basic, mean
        for seg in basicpart:
            if basicpart[seg]:
                res_dict[seg] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, basicpart[seg])
        return res_dict

    @staticmethod
    def present_vocabulary(schemas, schema_tree, schema_name, vcardinst):
        res_dict = dict()
        vocabulary = vcardinst.gen_trim_vocabulary()
        if vocabulary:
            word = vcardinst.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            if 'audio' in vocabulary:
                seg = "audio"
                audio_data = {"audio_{0}".format(word.strip().replace(" ","_")): vocabulary['audio']}
                res_dict[seg] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, audio_data)
            if 'main' in vocabulary and 'definition' in vocabulary:
                vocabulary['definition_brief'] = vocabulary['definition']
                vocabulary.pop('definition')
            seg = "vocabulary"
            dictionary_encap = {"dictname": "VOCABULARY", "dictcontent": vocabulary}
            res_dict[seg] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, dictionary_encap)
        return res_dict

    @staticmethod
    def _present_dictionary(schemas, schema_tree, schema_name, vcardinst, dictname):
        res_dict = dict()
        if vcardinst.means:
            word = vcardinst.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            dictzhnames = {'oxford': u"牛津词典", 'collins': u"柯林斯词典"}
            if dictname in dictzhnames and dictname in vcardinst.means:
                dictionary_encap = {"dictname": dictzhnames[dictname], "dictcontent": vcardinst.means[dictname]}
                res_dict[dictname] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[dictname], word, dictionary_encap)
        return res_dict

    @staticmethod
    def present_oxford(schemas, schema_tree, schema_name, vcardinst):
        dictname = "oxford"
        return VCardRenderer._present_dictionary(schemas, schema_tree, schema_name, vcardinst, dictname)

    @staticmethod
    def present_collins(schemas, schema_tree, schema_name, vcardinst):
        dictname = "collins"
        return VCardRenderer._present_dictionary(schemas, schema_tree, schema_name, vcardinst, dictname)

    @staticmethod
    def present_enmean(schemas, schema_tree, schema_name, vcardinst):
        res_dict = dict()
        if vcardinst.enmeans:
            word = vcardinst.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            dictname = "English Means"
            tag = "enmean"
            dictionary_encap = {"dictname": dictname, "dictcontent": vcardinst.enmeans}
            res_dict[tag] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[tag], word, dictionary_encap)
        return res_dict

    #生成FlashCard格式的结果数据, 一行数据, 允许使用HTML标识
    def render(self, vcardinst, schema_name):

        flashcard data contains the following fields:
        { front:     单词本身(from db)
          posp:      词性(根据已有数据计算得到)
          tag:       标签(from db)
          transform: 词形变换(from db)
          basic:     基本信息, 包括音标,基本词义
          mean:      金山词霸翻译
          audio:     发音对应的url
          vocabulary: Vocabulary.com对单词的解释
          oxford:    牛津词典翻译,例句
          collins:   柯林斯词典翻译,例句
          enmean:    英文翻译,例句
        }

        schemas = self.schemas
        schema_tree = self.schema_tree
        res_dict = {}
        #basic part
        res_tmp = VCardRenderer.present_basicpart(schemas, schema_tree, schema_name, vcardinst)
        res_dict.update(res_tmp)
        #vocabulary
        res_tmp = VCardRenderer.present_vocabulary(schemas, schema_tree, schema_name, vcardinst)
        res_dict.update(res_tmp)
        #oxford
        res_tmp = VCardRenderer.present_oxford(schemas, schema_tree, schema_name, vcardinst)
        res_dict.update(res_tmp)
        #collins
        res_tmp = VCardRenderer.present_collins(schemas, schema_tree, schema_name, vcardinst)
        res_dict.update(res_tmp)
        #enmean
        res_tmp = VCardRenderer.present_enmean(schemas, schema_tree, schema_name, vcardinst)
        res_dict.update(res_tmp)
        #fill blank
        keys = ["front", "posp", "tag", "transform", "basic", "mean", "stat", "audio", "vocabulary", "oxford", "collins", "enmean"]
        for k in keys:
            if k not in res_dict:
                res_dict[k] = u""
        return res_dict
"""

"""
翻译结果结构体
"""
class WordStorageModel(object):
    __pk_attrs__       = ["word"]
    __notnull_attrs__  = ["word", "mean"]
    __attrs__          = ["word", "wordprototype", "wordem", "mean", "pronunciation", "tag",
                          "transform", "posp", "vocabulary", "basicmeans", "oxford",
                          "collins", "longman", "enmeans", "dictmeans", "dictcnstat"]
    __iterable_attrs__ = ["pronunciation","tag","transform","posp",
                          "vocabulary","basicmeans","oxford","collins","longman","enmeans",
                          "dictmeans","dictcnstat"]
    __exchange_attrs__ = {"word_third": u"第三人称单数", "word_done": u"过去分词",
                          "word_pl": u"复数", "word_est": u"最高级",
                          "word_ing": u"现在分词", "word_er": u"ER", "word_past": u"过去式"}

    def __init__(self):
        self.ada = ormadaptor.AdaptorORM(os.sep.join([cur_dir,"models","dictmodel.yaml"]), os.sep.join([cur_dir,configuration["dbname"]]))
        self.word = ""             #单词本身
        self.wordprototype = ""    #单词原型
        self.wordem = ""           #读音分隔, 重音在哪
        self.mean = ""             #基本释义
        self.pronunciation = {}    #发音
        self.tag = {}              #TAG, 例如CET6等
        self.transform = {}        #变形
        self.posp = []             #词性
        self.vocabulary = {}       #vocabulary网站的解释
        self.basicmeans = []       #词性, 词义
        self.oxford = []           #牛津词典
        self.collins = []          #柯林斯词典
        self.longman = []          #朗文词典
        self.enmeans = []          #英文释义
        self.dictmeans = {}        #其他未定义的词典
        self.dictcnstat = {}       #海词词典统计


    #vocabulary结果, 结果保存在self.vocabulary
    def parse_vocabulary_rsp(self, rsp):
        def _remove_extract_space(s):
            res = re.sub(r'[\r\n\t]',' ',s.strip())
            return re.sub(r'( )+', ' ',res)
        def _stringify_node(node):
            parts = ([x for x in node.itertext()])
            return _remove_extract_space(''.join(filter(None, parts)).strip())
        try:
            #result stored in self.vocabulary
            self.vocabulary = dict()
            if isinstance(rsp, ReqResponse) and rsp.status_code==200:
                #parse main definition
                html = lxml.html.fromstring(rsp.text)
                main_divs = html.xpath("//div[@class='section blurb']")
                if main_divs:
                    self.vocabulary['main'] = _stringify_node(main_divs[0])
                #parse definition details
                definition_divs = html.xpath("//div[@class='main']/div[@class='definitions']/div//div[contains(@class,'sense')]")
                if definition_divs:
                    def_list = []
                    for def_div in definition_divs:
                        def_sense_dict = dict()
                        #1. get head info
                        def_heads = def_div.xpath("./h3[@class='definition']")
                        if def_heads:
                            def_head_posp = def_heads[0].xpath("./a/text()")
                            def_head_text = def_heads[0].xpath("./text()")
                            if def_head_posp:
                                def_sense_dict['posp'] = _remove_extract_space("".join(def_head_posp))
                            if def_head_text:
                                def_sense_dict['definition'] = _remove_extract_space("".join(def_head_text))
                        #2. get details
                        def_details = def_div.xpath("./div[@class='defContent']/dl[@class='instances']")
                        if def_details:
                            def_sense_dict['defcontent'] = []
                            for def_dl in def_details:
                                def_dl_dt = u"".join(def_dl.xpath("./dt/text()"))
                                def_dl_dds = def_dl.xpath("./dd")
                                if def_dl_dt and def_dl_dds:
                                    def_dl_dds_txt = []
                                    for def_dl_dd in def_dl_dds:
                                        txt = _remove_extract_space("".join(def_dl_dd.xpath(".//text()")))
                                        def_dl_dds_txt.append(txt)
                                    def_sense_dict['defcontent'].append( {"dt": def_dl_dt, "dd": def_dl_dds_txt} )
                        if def_sense_dict:
                            def_list.append(def_sense_dict)
                    self.vocabulary['definition'] = def_list
                audio_divs = html.xpath("//a[@class='audio']/@data-audio")
                if audio_divs:
                    self.vocabulary['audio'] = u"https://audio.vocab.com/1.0/us/{0}.mp3".format(audio_divs[0])
                return True
            else:
                return None
        except Exception as e:
            trans_log(u"parse vocabulary rsp except {0}".format(e))
            return None

    #提取海词词典频率统计
    def parse_dictcn_rsp(self, rsp):
        def _get_stat(html, eid):
            divs = html.xpath("//div[@id='{0}']".format(eid))
            if divs:
                return json.loads(unquote(divs[0].attrib["data"]))
            return None
        try:
            self.dictcnstat = {}
            if isinstance(rsp, ReqResponse) and rsp.status_code==200:
                html = lxml.html.fromstring(rsp.text)
                stat_basic = _get_stat(html, "dict-chart-basic")
                if stat_basic:
                    self.dictcnstat["basic"] = stat_basic
                stat_posp = _get_stat(html, "dict-chart-examples")
                if stat_posp:
                    self.dictcnstat["posp"] = stat_posp
                return True
            else:
                return False
        except Exception as e:
            trans_log(u"parse vocabulary rsp except {0}".format(e))
            return None

    #从响应结构体中提取翻译结果
    def parse_baidu_rsp(self, rsp):
        if isinstance(rsp, ReqResponse):
            htmlText = rsp.text
        else:
            htmlText = rsp
        try:
            jsondata = json.loads(htmlText)
            self._extract_basic(jsondata)
            self._extract_endict(jsondata)
            self._extract_oxford(jsondata)
            self._extract_collins(jsondata)
            if self.word and self.mean:
                return True
            return None
        except Exception as e:
            trans_log(u"parse baidu rsp except {0}".format(e))
            return None

    #提取基本翻译信息
    def _extract_basic(self, jsondata):
        """
        1. word   单词本身
        2. mean   翻译
        3. wordem 重音标注
        4. wordprototype 单词原型
        5. transform     其他形态
        6. tag           标签(core, other两种)
        7. pronunciation 发音
        8. basicmeans     金山词霸翻译内容 [{posp:xx, means:xx}]
        """
        try:
            self.word = jsondata['trans_result']['data'][0]['src']
            self.mean = jsondata['trans_result']['data'][0]['dst']
            self.wordem = ""
            self.wordprototype = ""
            self.transform = {}
            self.tag = {}
            self.pronunciation = {}
            self.basicmeans = []
            self.posp = []
            stdposp = {"v": "verb", "vi": "verb", "vt": "verb", "vi.": "verb", "vt.": "verb",
                       "vi.&vt.": "verb", "verb": "verb",
                       "n": "noun", "n.": "noun", "noun": "noun",
                       "adj.": "adj", "adj": "adj",
                       "adv.": "adv", "adv": "adv",
                       "prep.": "prep", "prep": "prep",
                       "conj.": "conj", "conj": "conj",
                       "art.": "art", "art": "art",
                       "pron.": "pron", "pron": "pron",
                       "num.": "num", "num": "num"}
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'collins' in jsonx and 'word_emphasize' in jsonx['collins']:
                    self.wordem = jsonx['collins']['word_emphasize'].replace('|','.')
                    self.wordprototype = jsonx['collins']['word_name']
                #将来可能用到的信息
                if "sanyms" in jsonx:
                    self.dictmeans["sanyms"] = jsonx["sanyms"]    #近义词反义词, 备用
                if "synonym" in jsonx:
                    self.dictmeans["synonym"] = jsonx["synonym"]    #同义词辨析
                if "rootsaffixes" in jsonx:
                    self.dictmeans["rootsaffixes"] = jsonx["rootsaffixes"]  #词根词缀
                if 'simple_means' in jsonx:
                    jsonx = jsonx['simple_means']
                    if 'exchange' in jsonx:
                        self.transform = jsonx['exchange']
                    if 'tags' in jsonx:
                        self.tag = jsonx["tags"]
                    if 'symbols' in jsonx:
                        jsonx = jsonx['symbols']
                        if isinstance(jsonx,list) and len(jsonx)>0:
                            jsonx = jsonx[0]
                            for phk in jsonx:
                                if phk!="parts":
                                    if "mp3" in phk and "tts" not in phk:
                                        self.pronunciation[phk] = u"http://res.iciba.com/resource/amp3{0}".format(jsonx[phk])
                                    else:
                                        self.pronunciation[phk] = jsonx[phk]
                            if 'parts' in jsonx:
                                jsonx = jsonx['parts']
                                for x in jsonx:
                                    if 'part' in x and 'means' in x:
                                        #词性
                                        posp = x["part"] if x["part"] not in stdposp else stdposp[x["part"]]
                                        if posp not in self.posp:
                                            self.posp.append(posp)
                                        #词性 + 释义
                                        self.basicmeans.append({'posp': x['part'],
                                                               'means': x['means']})
        except:
            pass

    #提取英文释义
    def _extract_endict(self, jsondata):
        # 1. self.enmeans
        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'edict' in jsonx and 'item' in jsonx['edict']:
                    jsonx = jsonx['edict']['item']
                    if jsonx:
                        for posjsonx in jsonx:
                            if 'pos' in posjsonx and 'tr_group' in posjsonx:
                                self.enmeans.append({"posp": posjsonx['pos'], "trgroups":posjsonx['tr_group']})
                                cur_items = self.enmeans[-1]
                                for tr in posjsonx["tr_group"]:
                                    if "means" not in cur_items:
                                        cur_items["means"] = []
                                    if "examples" not in cur_items:
                                        cur_items["examples"] = []
                                    if "tr" in tr:
                                        for tr_d in tr["tr"]:
                                            cur_items["means"].append(tr_d)
                                    if "example" in tr:
                                        for tr_x in tr["example"]:
                                            cur_items["examples"].append(tr_x)
        except:
            pass

    #提取牛津词典释义
    def _extract_oxford(self, jsondata):
        # 1. self.oxford
        #递归查找每个dict项, 如果其仍然包含data子项, 递归下去
        def _iter_extract_data_ox(data, result):
            #只处理entry, p-g节点的data内容
            if "tag" in data and "data" in data and isinstance(data["data"],list):
                for d in data['data']:
                    if isinstance(d, dict):
                        _iter_extract_data_ox(d, result)
            #词性
            elif "tag" in data and data["tag"]=="p":
                #查看队尾的数据, 如果只有posp参数, 表示是个无效的数据
                if len(result)==0:
                    result.append({})
                else:
                    tail = result[-1]
                    if len(tail)<=1:    #无效数据
                        tail.clear()
                    else:               #有效数据, 需要另起一组新的数据
                        result.append({})
                cur_item = result[-1]
                cur_item["posp"] = data["p_text"]
            #定义
            elif "tag" in data and data["tag"] in ["d","x"]:
                cur_item = result[-1]
                itemkey = "means" if data["tag"]=="d" else "examples"
                if itemkey not in cur_item:
                    cur_item[itemkey] = []
                res = None
                if 'enText' in data:
                    res = {'en': data['enText']}
                if 'chText' in data and res:
                    res['zh'] = data['chText']
                if res:
                    cur_item[itemkey].append(res)

        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'oxford' in jsonx and 'entry' in jsonx['oxford']:
                    self.oxford = []
                    jsonx = jsonx['oxford']['entry']
                    for data in jsonx:
                        if isinstance(data, dict):
                            _iter_extract_data_ox(data, self.oxford)
        except:
            pass

    #提取柯林斯词典释义
    def _extract_collins(self, jsondata):
        # 1. self.collins
        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'collins' in jsonx and 'entry' in jsonx['collins']:
                    self.collins = []
                    jsonx = jsonx['collins']['entry']
                    for data in jsonx:
                        if isinstance(data, dict):
                            if "type" in data and data["type"]=="mean" and "value" in data:
                                self.collins.append({})
                                cur_item = self.collins[-1]
                                datavset = data["value"]
                                for datav in datavset:
                                    if "posp" in datav and datav["posp"]:
                                        cur_item["posp"] = datav["posp"][0]["label"].lower()
                                    if "def" in datav and "tran" in datav:
                                        if "means" not in cur_item:
                                            cur_item["means"] = []
                                        cur_item["means"].append({"en": datav["def"], "zh": datav["tran"]})
                                    if 'mean_type' in datav:
                                        if "examples" not in cur_item:
                                            cur_item["examples"] = []
                                        examplelist = cur_item["examples"]
                                        for dm in datav['mean_type']:
                                            if 'example' in dm:
                                                for ex in dm['example']:
                                                    resx = None
                                                    if 'ex' in ex:
                                                        resx = {'en': ex['ex']}
                                                    if 'tran' in ex and resx:
                                                        resx['zh'] = ex['tran']
                                                    if resx:
                                                        examplelist.append(resx)
        except:
            pass

    #从数据库读取信息, 更新self字段
    def read_result_from_db(self, word):
        return self.export_db({'word': word})

    #生成SQLite格式的结果数据, 向数据库写数据
    def write_result_to_db(self):
        def encap_data(x):
            if isinstance(x,list) or isinstance(x,dict):
                return json.dumps(x)
            return x
        #字段数据
        db_fields_data = dict(
            (attr, encap_data(getattr(self, attr, "")))
            for attr in self.__attrs__)
        #主键数据
        db_pk_fields_data = dict(
            (attr, encap_data(getattr(self, attr, "")))
            for attr in self.__pk_attrs__)
        #不能为空的字段
        data_valid = True
        for attr in self.__notnull_attrs__:
            v = getattr(self, attr, "")
            if not v.strip():
                data_valid = False
                break
        if data_valid:
            if not self.ada.exists(**db_pk_fields_data):
                #如果主键不存在, 则新插入一条记录
                self.ada.save(**db_fields_data)
            else:
                #如果主键已存在, 则更新已有数据
                for k in self.__pk_attrs__:
                    db_fields_data.pop(k, None)
                self.ada.update(db_pk_fields_data, **db_fields_data)

    #导出满足筛选条件的SQLite数据, 如果指定了map函数, 则进行处理并返回列表
    def export_db(self, filters, rec_map_proc=None, rec_map_result=None):
        #筛选条件为k,v格式, 例如  tag='%CET4%', 会筛选 tags列包含CET4的数据, 条件为与关系
        def set_datarow(fieldnames, datarow):
            def uncap_data(attr, x):
                if attr in self.__iterable_attrs__:
                    if x:
                        return json.loads(x)
                    return None
                return x
            for idx, field in enumerate(fieldnames):
                if field in self.__attrs__:
                    setattr(self, field, uncap_data(field, datarow[idx]))
        #查询数据库
        (fieldnames, dataset) = self.ada.load(**filters)
        if dataset:
            if rec_map_proc and isinstance(rec_map_result,list):
                for datarow in dataset:
                    set_datarow(fieldnames, datarow)
                    rec_map_result.append(rec_map_proc(self))
            else:
                datarow = dataset[0]
                set_datarow(fieldnames, datarow)
            return True
        else:
            return False

    def gen_basic_data(self):
        basicd = dict()
        basicd["front"] = self.word
        basicd["posp"] = self.posp
        basicd["basic"] = None
        basicd["transform"] = {k:",".join(self.transform[k]) for k in self.transform if self.transform[k]}
        basicd["tag"] = None
        basicd["mean"] = None
        basicd['stat'] = None
        #basic
        basicd["basic"] = {}
        if self.wordem:
            basicd["basic"]["wordem"] = self.wordem
        if "ph_am" in self.pronunciation:
            basicd["basic"]["ph_am"] = self.pronunciation["ph_am"]
        if "ph_en" in self.pronunciation:
            basicd["basic"]["ph_en"] = self.pronunciation["ph_en"]
        if self.mean:
            basicd["basic"]["mean"] = self.mean
        #tags
        if self.tag:
            basicd["tag"] = []
            if "core" in self.tag:
                l = filter(lambda x: len(x.strip())>0, self.tag["core"])
                if l:
                    basicd["tag"].extend(l)
            if "other" in self.tag:
                l = filter(lambda x: len(x.strip())>0, self.tag["other"])
                if l:
                    basicd["tag"].extend(l)
        #mean 基本词义, 含词性 basicmean, 每条解释占一行
        if self.basicmeans:
            basicd["mean"] = self.basicmeans
        #词频统计
        if self.dictcnstat:
            basicd['stat'] = self.dictcnstat
        return basicd

    #缩减vocabulary中的definition数量
    def gen_trim_vocabulary(self):
        if self.vocabulary:
            if "definition" in self.vocabulary:
                new_voc = copy.deepcopy(self.vocabulary)
                for defitem in new_voc["definition"]:
                    if "defcontent" in defitem:
                        for defcontent_item in defitem["defcontent"]:
                            if "dd" in defcontent_item:
                                defcontent_item["dd"] = defcontent_item["dd"][:3]
                return new_voc
        return self.vocabulary

    #批量生成卡片, 根据filters过滤出数据, 将每行数据按shcemaname渲染, 返回渲染结果列表(list)
    def gen_batchcard_data(self, schemaname, filters):
        def _gen_htmlcard_impl(wordModelObj):
            return WordModelRenderer().render(wordModelObj, schemaname)
        res = []
        self.export_db(filters, rec_map_proc=_gen_htmlcard_impl, rec_map_result=res)
        return res

    #返回需要制作anki卡片的数据json, 包含卡片反面内容
    @staticmethod
    def gen_flashcard_back(wordModelObj, schema_name, orders=["basic","posp","audio","mean","stat","transform","tag","vocabulary","oxford","collins","enmeans"]):
        renderer = WordModelRenderer()
        res_dict = renderer.render(wordModelObj, schema_name)
        def _secure_back(back_html):
            return back_html.replace("?",u"？").replace("&"," ")
        html_head = """
        <html>
            <head>
                <meta charset='utf-8' />
                <meta name='viewport' content='width=device-width, initial-scale=1.0'>
                <link href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css' rel='stylesheet'>
                <link href='https://cdn.bootcss.com/font-awesome/4.7.0/css/font-awesome.min.css' rel='stylesheet'>
                <link href='/vocabulary/static/css/render-theme-default.css' rel='stylesheet'>
                <style>
                    html a.audio {
                        text-decoration: none !important;
                        font-size: 22px;
                        padding: 0 0 0 .75em;
                        cursor: pointer;}
                </style>
            </head>
            <body><div class='container-fluid'><div class='card'>"""
        html_head = html_head.replace("\r\n","").replace("\n","")
        html_tail = u"</div></div></body></html>"
        back = [html_head]
        for k in orders:
            if k in res_dict:
                back.append(res_dict[k])
        back.append(html_tail)
        res_dict["back"] = _secure_back(u"".join(back).replace("\t"," "))
        return res_dict

"""
翻译方法, 调用网络翻译内容, 解析结果
"""
class ENTranslation(object):
    def __init__(self):
        self.sess = requests.session()
        self.req_dict_b = dict()
        self.req_dict_v = dict()
        self.req_dict_s = dict()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sess.close()

    def _init_request(self):
        cookie_dict = {'locale': 'zh', 'BAIDUID': '1A2E4E5A00EF753F3C8B59F9FF000AB5:FG=1'}
        self.sess.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        url = 'https://fanyi.baidu.com'
        headers = {'Host': 'fanyi.baidu.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Connection': 'keep-alive', 'Referer': 'https://fanyi.baidu.com/', 'X-Requested-With': 'XMLHttpRequest'}
        self.req_dict_b = {"url": url, "headers": headers}
        self.req_dict_v = {"url": "https://www.vocabulary.com", "headers": {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0', 'Host':'www.vocabulary.com', 'Referer': 'https://www.vocabulary.com/dictionary/'}}
        self.req_dict_s = {"url": "http://dict.cn", "headers": {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0', 'Host': 'dict.cn', 'Referer': 'http://dict.cn/', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,en-US;q=0.7,en;q=0.3'}}
        try:
            rsp = self.sess.get(**self.req_dict_s)  #统计结果非必选项
            rsp = self.sess.get(**self.req_dict_v)
            if configuration["need_vocabulary"] and rsp.status_code!=200:
                return False
            rsp = self.sess.get(**self.req_dict_b)  #必选项
            if rsp.status_code!=200:
                return False
            return ENTranslation.s_parse_jsvar(rsp)
        except:
            return False

    @staticmethod
    def s_parse_jsvar(rsp):
        if isinstance(rsp, ReqResponse):
            htmlText = rsp.text
        else:
            htmlText = rsp
        try:
            html_ctx = dict()
            idx1 = htmlText.index('window.gtk')
            window_gtk = str(htmlText[idx1:idx1+50].split(';')[0].split('=')[1].strip().replace("'",''))
            idx2 = htmlText.index('token:')
            token = str(htmlText[idx2:idx2+50].split(',')[0].split(':')[1].strip().replace("'",""))
            html_ctx['token'] = str(token)
            html_ctx['gtk'] = str(window_gtk)
            return html_ctx
        except:
            return False

    @staticmethod
    def s_gen_payload(word, html_ctx, srclang):
        token = html_ctx['token']
        window_gtk = html_ctx['gtk']
        sign = baidufy_sign.calc_sign(word, window_gtk)
        payload = dict()
        payload['from'] = srclang
        payload['to'] = 'en' if srclang=='zh' else 'zh'
        payload['query'] = word
        payload['simple_means_flag'] = '3'
        payload['sign'] = sign
        payload['token'] = token
        payload['transtype'] = 'realtime'
        return payload

    @staticmethod
    def s_detect_lang(word):
        if ord(word[0])>122:
            return 'zh'
        return 'en'

    def _translate_request(self, schema_name, word):
        word_obj = WordStorageModel()
        word_in_dict = word_obj.read_result_from_db(word)
        if not word_in_dict:
            if not configuration["queryweb"]:
                return None
            srclang = ENTranslation.s_detect_lang(word)
            #step 1. first visit, to get gtk, token
            html_ctx = self._init_request()
            if not html_ctx:
                return None
            #step 2. visit translate api
            try:
                #vocabulary.com
                self.req_dict_v['url'] = 'https://www.vocabulary.com/dictionary/definition.ajax'
                self.req_dict_v['params'] = {"search": word, "lang": "en"}
                rsp = self.sess.get(**self.req_dict_v)
                res = word_obj.parse_vocabulary_rsp(rsp)
                if configuration["need_vocabulary"] and not res:
                    trans_log(u"get vocabulary failed: {0}".format(word))
                    return None
                #dict.cn
                self.req_dict_s['url'] = 'http://dict.cn/{0}'.format(word)
                rsp = self.sess.get(**self.req_dict_s)
                res = word_obj.parse_dictcn_rsp(rsp)
                #fanyi.baidu
                self.req_dict_b['url'] = 'https://fanyi.baidu.com/v2transapi'
                self.req_dict_b['data'] = ENTranslation.s_gen_payload(word, html_ctx, srclang)
                rsp = self.sess.post(**self.req_dict_b)
                res = word_obj.parse_baidu_rsp(rsp)
                if res:
                    word_obj.write_result_to_db()
                    if configuration["need_flashcard"]:
                        return WordStorageModel.gen_flashcard_back(word_obj, schema_name)
                    else:
                        return True
                else:
                    trans_log(u"get baidu failed: {0}".format(word))
                    return None
            except Exception as e:
                trans_log(u"translate_req {0} except {1}".format(word, e))
                return None
        else:
            if configuration["need_flashcard"]:
                return WordStorageModel.gen_flashcard_back(word_obj, schema_name)
            else:
                return True

    """
    API
    """
    def translate(self, format_type, word):
        if format_type=="anki":
            schema_name = "html_card"
        elif format_type=="html":
            schema_name = "html_card"
        else:
            schema_name = "database_raw"
        result = self._translate_request(schema_name, word)
        if result:
            if configuration["log_success"]:
                trans_log(u"{0} OK!".format(word))
            return result
        else:
            trans_log(u"{0} fail ...".format(word))
            return {}

    def query(self, format_type, pattern):
        pattern = pattern.replace('*','%')
        word_obj = WordStorageModel()
        if format_type=="anki":
            schema_name = "html_card"
        elif format_type=="html":
            schema_name = "html_card"
        else:
            schema_name = "database_raw"
        if "%" not in pattern and " " not in pattern.strip():
            res = [self._translate_request(schema_name, pattern.strip())]
        else:
            res = word_obj.gen_batchcard_data(schema_name, {"word":pattern})
        return res
