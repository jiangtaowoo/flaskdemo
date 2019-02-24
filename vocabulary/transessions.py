
# -*- coding: utf-8 -*-
import os
import inspect
from sys import argv
import re
import json
import copy
import lxml.html
import datetime
import yaml
from collections import deque
import requests
from requests.models import Response as ReqResponse
import baidufy_sign
import sys
from metacls import Singleton

sys.path.insert(1, os.path.join(sys.path[0],'..'))
import ormadaptor
#from .. import ormadaptor


def trans_log(logmsg):
    cur_dir = os.path.dirname(os.path.relpath(__file__))
    log_dir = os.sep.join([cur_dir, 'logs'])
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logfilename = os.sep.join([log_dir,u"trans_{0:%Y-%m-%d}.log".format(datetime.datetime.today())])
    with open(logfilename, 'a+') as outf:
        outf.write(u"{0}:\t{1}\n".format(datetime.datetime.now(),logmsg))


"""
翻译结果渲染
"""
class VCardRenderer(object):
    __metaclass__ = Singleton

    def __init__(self):
        cur_dir = os.path.dirname(os.path.relpath(__file__))
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
    def _basic_render(schema_node, data):
        """
        渲染的情况分为:
        1. 为list数据进行渲染
           a. 方式一: list中的每个元素均采用一个模板渲染(RAW_STYLE)
           b. 方式二: list中的元素内容, 与渲染模板匹配, 根据匹配结果渲染
        2. 为dict数据进行渲染
           a. 方式一: 根据key匹配渲染模板, 将value按模板渲染
           b. 方式二: 根据key匹配渲染模板, 将key, value按模板渲染
        """
        #只支持字符串渲染
        if not (isinstance(data, str) or isinstance(data, unicode)):
            return data
        if isinstance(schema_node, dict):
            #按字典匹配内容渲染
            if data in schema_node['match']:
                return unicode(schema_node['match'][data],"utf-8").format(data)
            return unicode(schema_node['except'],"utf-8").format(data)
        return unicode(schema_node,"utf-8").format(data)

    @staticmethod
    def _iter_render(schema_tree, schema_name, schema_node, data):
        """递归完成渲染
        1. type == raw, 直接 .format(data) 完成渲染
        2. type == style, 调用 basic_render 完成渲染
        3. type == template, 调用 _iter_render 递归完成渲染
        """
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
                            schema_kvc = dict_sc_kv["kvconnector"]
                            rendered_k = VCardRenderer._iter_render(schema_tree, schema_name, schema_k, k)
                            rendered_v = VCardRenderer._iter_render(schema_tree, schema_name, schema_v, data[k])
                            result.append(schema_kvc.format(rendered_k, rendered_v))
                #最后连接
                return delimiter.join(result)
        elif "type" in schema_node:
            if schema_node["type"]=="raw":
                fmt = schema_node["data"]
                if not isinstance(fmt, unicode):
                    fmt = unicode(fmt,"utf-8")
                return fmt.format(data)
            elif schema_node["type"]=="style":
                style_k = schema_node["data"]
                style_node = schema_tree[style_k]
                return VCardRenderer._basic_render(style_node, data)
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
                if not isinstance(inputs, unicode):
                    inputs = unicode(inputs, "utf-8")
                word_pattern = re.compile(theword, re.IGNORECASE)
                highlight_word = VCardRenderer._basic_render(hilight_node, theword)
                return word_pattern.sub(highlight_word, inputs)
        result = data
        if inner_node:
            result = VCardRenderer._iter_render(schema_tree, schema_name, inner_node, data)
        if outer_node:
            result = VCardRenderer._basic_render(outer_node, result)
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
        vocabulary = vcardinst.get_trim_vocabulary()
        if vocabulary:
            word = vcardinst.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            if 'audio' in vocabulary:
                seg = "audio"
                res_dict[seg] = VCardRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, vocabulary['audio'])
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
            dictzhnames = {'oxford': u'牛津词典', 'collins': u'柯林斯词典'}
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
        """
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
        """
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
        keys = ["front", "posp", "tag", "transform", "basic", "mean", "audio", "vocabulary", "oxford", "collins", "enmean"]
        for k in keys:
            if k not in res_dict:
                res_dict[k] = u""
        return res_dict


"""
翻译结果结构体
"""
class WordTranslateResult(object):
    __attrs__ = [
        'word', 'wordem', 'ph_am', 'ph_en', 'tags',
        'word_third', 'word_done', 'word_pl', 'word_est', 'word_ing',
        'word_er', 'word_past', 'mean', 'sentence', 'basicmean', 'means', 'enmeans', 'vocabulary'
    ]
    __pk_attrs__ = ['word']
    __iterable_attrs__ = ['basicmean', 'means', 'enmeans', 'vocabulary']
    __exchange_attrs__ = {'word_third': u'第三人称单数', 'word_done': u'过去分词',
                        'word_pl': u'复数', 'word_est': u'EST',
                        'word_ing': u'现在分词', 'word_er': u'ER',
                        'word_past': u'过去式'
    }

    def __init__(self):
        cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.ada = ormadaptor.AdaptorORM(os.sep.join([cur_dir,"models","dictmodel.yaml"]), os.sep.join([cur_dir,"vocabulary.db"]))
        self.vocabulary = {}   #vocabulary网站的解释
        self.word = ""         #单词本身
        self.wordem = ""       #读音分隔, 重音在哪
        self.ph_am = ""        #美式音标
        self.ph_en = ""        #英式音标
        self.tags = ""         #TAGS, 例如CET6等
        self.word_third = ""   #第三人称形态
        self.word_done = ""    #完成时态
        self.word_pl = ""      #pl
        self.word_est = ""     #est
        self.word_ing = ""     #进行时态
        self.word_er = ""      #er
        self.word_past = ""    #过去式
        self.mean = ""         #基本释义
        self.sentence = ""     #上下文句子
        self.basicmean = []    #词性, 词义
        self.means = dict()    #单词释义及例句
        #self.means['oxford'] = [{'en':'','zh':''},{'en':'', 'zh':''}]
        self.enmeans = []      #英文释义
        self.pospkeys = {"adj":"adj", "adv":"adv", "n":"noun", "v":"verb"}
        self.pospstyles = {"adj":"warning", "adv":"info", "noun":"danger", "verb":"success"}
        #[{'noun':[{tr, example, similar_word},{}]}]


    #vocabulary结果, 结果保存在self.vocabulary
    def parse_vocabulary_rsp(self, rsp):
        def _remove_extract_space(s):
            res = re.sub(r'[\r\n\t]',' ',s.strip())
            return re.sub(r'( )+', ' ',res)
        def _stringify_node(node):
            parts = ([x for x in node.itertext()])
            return _remove_extract_space(''.join(filter(None, parts)).strip())
        try:
            if isinstance(rsp, ReqResponse) and rsp.status_code==200:
                #result stored in self.vocabulary
                self.vocabulary = dict()
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
        try:
            self.word = jsondata['trans_result']['data'][0]['src']
            self.mean = jsondata['trans_result']['data'][0]['dst']
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'collins' in jsonx and 'word_emphasize' in jsonx['collins']:
                    self.wordem = jsonx['collins']['word_emphasize'].replace('|','.')
                if 'simple_means' in jsonx:
                    jsonx = jsonx['simple_means']
                    if 'exchange' in jsonx:
                        x = jsonx['exchange']
                        for attr in self.__attrs__:
                            if attr in x and isinstance(x[attr],list) and x[attr]:
                                setattr(self, attr, x[attr][0])
                    if 'tags' in jsonx:
                        self.tags = []
                        self.tags.extend(jsonx['tags']['core'])
                        self.tags.extend(jsonx['tags']['other'])
                        self.tags = ','.join(filter(len,self.tags))
                    if 'symbols' in jsonx:
                        jsonx = jsonx['symbols']
                        if isinstance(jsonx,list) and len(jsonx)>0:
                            jsonx = jsonx[0]
                            self.ph_am = jsonx['ph_am'] if 'ph_am' in jsonx else ""
                            self.ph_en = jsonx['ph_en'] if 'ph_en' in jsonx else ""
                            if 'parts' in jsonx:
                                jsonx = jsonx['parts']
                                for x in jsonx:
                                    if 'part' in x and 'means' in x:
                                        self.basicmean.append({'posp': x['part'],
                                                               'mean':';'.join(x['means'])})
        except:
            pass

    #提取英文释义
    def _extract_endict(self, jsondata):
        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'edict' in jsonx and 'item' in jsonx['edict']:
                    jsonx = jsonx['edict']['item']
                    if jsonx:
                        for posjsonx in jsonx:
                            if 'pos' in posjsonx and 'tr_group' in posjsonx:
                                self.enmeans.append({posjsonx['pos']: posjsonx['tr_group']})
        except:
            pass

    #提取牛津词典释义
    def _extract_oxford(self, jsondata):
        #递归查找每个dict项, 如果其仍然包含data子项, 递归下去
        def _iter_extract_data_ox(data, result):
            #1. 先获取当前范围的数据
            res = None
            if 'enText' in data:
                res = {'en': data['enText']}
            if 'chText' in data and res:
                res['zh'] = data['chText']
            if res:
                result.append(res)
            if 'data' in data and isinstance(data['data'], list) and data['data']:
                for d in data['data']:
                    if isinstance(d, dict):
                        _iter_extract_data_ox(d, result)
        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'oxford' in jsonx and 'entry' in jsonx['oxford']:
                    self.means['oxford'] = []
                    jsonx = jsonx['oxford']['entry']
                    for data in jsonx:
                        if isinstance(data, dict):
                            _iter_extract_data_ox(data, self.means['oxford'])
        except:
            pass

    #提取柯林斯词典释义
    def _extract_collins(self, jsondata):
        try:
            if 'dict_result' in jsondata:
                jsonx = jsondata['dict_result']
                if 'collins' in jsonx and 'entry' in jsonx['collins']:
                    self.means['collins'] = []
                    jsonx = jsonx['collins']['entry']
                    for data in jsonx:
                        if isinstance(data, dict):
                            if 'value' in data:
                                data = data['value']
                                for d in data:
                                    res = None
                                    if 'def' in d:
                                        res = {'en': d['def']}
                                    if 'tran' in d and res:
                                        res['zh'] = d['tran']
                                    if res:
                                        self.means['collins'].append(res)
                                    if 'mean_type' in d:
                                        for dm in d['mean_type']:
                                            if 'example' in dm:
                                                for ex in dm['example']:
                                                    resx = None
                                                    if 'ex' in ex:
                                                        resx = {'en': ex['ex']}
                                                    if 'tran' in ex and resx:
                                                        resx['zh'] = ex['tran']
                                                    if resx:
                                                        self.means['collins'].append(resx)
        except:
            pass

    #从数据库读取信息
    def read_result_from_db(self, word):
        return self.export_db({'word': word})

    #生成SQLite格式的结果数据, 向数据库写数据
    def write_result_to_db(self):
        def encap_data(x):
            if isinstance(x,list) or isinstance(x,dict):
                return json.dumps(x)
            return x
        db_fields_data = dict(
            (attr, encap_data(getattr(self, attr, "")))
            for attr in self.__attrs__)
        db_pk_fields_data = dict(
            (attr, encap_data(getattr(self, attr, "")))
            for attr in self.__pk_attrs__)
        if self.word and self.mean:
            if not self.ada.exists(**db_pk_fields_data):
                self.ada.save(**db_fields_data)
            else:
                #更新已有数据
                self.ada.update(db_pk_fields_data, **db_fields_data)

    #导出满足筛选条件的SQLite数据
    def export_db(self, filters, cboper=None):
        #筛选条件为k,v格式, 例如  tags='%CET4%', 会筛选 tags列包含CET4的数据, 条件为与关系
        def uncap_data(attr, x):
            if attr in self.__iterable_attrs__:
                return json.loads(x)
            return x
        def set_datarow(fieldnames, datarow):
            for idx, field in enumerate(fieldnames):
                if field in self.__attrs__:
                    setattr(self, field, uncap_data(field, datarow[idx]))
        #查询数据库
        (fieldnames, dataset) = self.ada.load(**filters)
        if cboper and isinstance(cboper,list) and dataset:
            cbfunc = cboper[0]
            cbres = []
            for datarow in dataset:
                set_datarow(fieldnames, datarow)
                cbres.append(cbfunc())
            cboper.append(cbres)
            return True
        elif dataset:
            datarow = dataset[0]
            set_datarow(fieldnames, datarow)
            return True
        return False

    def gen_basic_data(self):
        basicd = dict()
        basicd["front"] = self.word
        basicd["posp"] = None
        basicd["basic"] = None
        basicd["transform"] = None
        basicd["tag"] = None
        basicd["mean"] = None
        def _get_std_posp(posp):
            for k in self.pospkeys:
                if k in posp:
                    return self.pospkeys[k]
            return posp
        #posp
        if self.basicmean:
            posp = []
            for bmean in self.basicmean:
                pitem = _get_std_posp(bmean['posp'])
                if pitem not in posp:
                    posp.append(pitem)
            if posp:
                basicd["posp"] = list(posp)
        #basic
        def _create_d_bykeys(keys):
            d = dict()
            for k in keys:
                v = getattr(self, k, None)
                if v:
                    d[k] = v
            return d
        keys = ["wordem", "ph_am", "ph_en", "mean"]
        basicd["basic"] = _create_d_bykeys(keys)
        #transform 词形变换
        keys = [k for k in self.__exchange_attrs__]
        basicd["transform"] = _create_d_bykeys(keys)
        #tags
        if self.tags:
            basicd["tag"] = self.tags.split(",")
        #mean 基本词义, 含词性 basicmean, 每条解释占一行
        if self.basicmean:
            basicd["mean"] = self.basicmean
        return basicd

    #缩减vocabulary中的definition数量
    def get_trim_vocabulary(self):
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

    #生成FlashCard格式的结果数据, 一行数据, 允许使用HTML标识
    def _gen_flashcard_data(self):
        res_dict = {}
        front = self.word
        res_dict['front'] = front
        sepc = '  '    #列分隔符
        sepr = '<br>'  #行分隔符
        html_templ_head = """<html><head><link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet"></head><body><div class="container">"""
        html_templ_tail = """</div></body></html>"""
        html_posp_templ = u'<b class="label label-{0}">{1}</b>'
        html_bootstrap_div = u'<div class="container">{0}</div>'
        html_panel_head = u'<div class="panel panel-info"><div class="panel-heading"><h4 class="panel-title text-center">'
        html_panel_tail = u'</h4></div></div>'
        def _pretty_str_format(inputstr):
            if not isinstance(inputstr, unicode):
                inputstr = unicode(inputstr, "utf-8")
            word_pattern = re.compile(self.word, re.IGNORECASE)
            res = word_pattern.sub('<b>'+self.word+'</b>', inputstr)
            return re.sub(r'[\r\n\t]', ' ', res)
        def _get_std_posp(posp):
            for k in self.pospkeys:
                if k in posp:
                    return self.pospkeys[k]
            return posp
        def _posp_html_format(posp):
            stdp = _get_std_posp(posp)
            if stdp in self.pospstyles:
                return html_posp_templ.format(self.pospstyles[stdp], posp)
            return html_posp_templ.format("default", posp)
        #卡片反面
        back = []
        #第零行, 原文上下文对应的句子
        if self.sentence:
            v = _pretty_str_format(self.sentence)
            back.append(v+'<hr>')
            res_dict['sentence'] = v
        #LINE #1. POSP
        if self.basicmean:
            back_idx = len(back)
            posp = []
            for bmean in self.basicmean:
                stdp = _get_std_posp(bmean['posp'])
                if stdp not in posp:
                    posp.append(stdp)
            if posp:
                back.append(u"{0}".format(sepc.join([_posp_html_format(p) for p in posp])))
                res_dict['posp'] = '\n'.join(back[back_idx:])
        #LINE #2. 读音分隔, 音标, 基本释义
        (wordem, ph_am, ph_en) = ('', '', '')
        if self.wordem:
            wordem = ''.join(['<b style="color:red">', self.wordem, '</b>'])
        if self.ph_am:
            ph_am = ''.join([u'美', ' [', self.ph_am, ']'])
        if self.ph_en:
            ph_en = ''.join([u'英', ' [', self.ph_en, ']'])
        l = filter(len,[wordem, ph_am, ph_en, '<b>'+self.mean+'</b>'])
        v = sepc.join(l)
        back.append(v)
        res_dict['basic'] = v
        #LINE #3. 词形变换
        l = []
        for attr, attrzh in self.__exchange_attrs__.iteritems():
            v = getattr(self, attr, "")
            if v:
                l.append( attrzh + ':' + v)
        v = sepc.join(l)
        back.append(v)
        res_dict['transform'] = v
        #LINE #4. tags
        if self.tags:
            back.append(self.tags.replace(',', sepc))
            res_dict['tag'] = back[-1]
        #LINE #5. 基本词义, 含词性 basicmean, 每条解释占一行
        if self.basicmean:
            back_idx = len(back)
            for bmean in self.basicmean:
                posp = _posp_html_format(bmean['posp'])
                back.append(sepc.join([posp, bmean['mean']]))
            res_dict['mean'] = '\n'.join(back[back_idx:])
        #LINE #6. vocabulary
        if self.vocabulary:
            if 'audio' in self.vocabulary:
                #audio_v = "[sound: {0}]".format(self.vocabulary['audio'])
                #back.append(audio_v + ' <hr>')
                res_dict['audio'] = self.vocabulary['audio']
            k = None
            if 'main' in self.vocabulary:
                k = 'main'
            elif 'definition' in self.vocabulary:
                k = 'definition'
            if k:
                back.append(u'<br>{0}VOCABULARY{1}'.format(html_panel_head,html_panel_tail))
                vocab_v = _pretty_str_format(self.vocabulary[k])
                vocab_v = re.sub(r'(<br>\s*)+', '<br>', vocab_v)
                #back.append('<hr>' + vocab_v + '<hr>')
                back.append(vocab_v)
                res_dict['vocabulary'] = vocab_v
        #第六行, 各词典解释及例句
        if self.means:
            dictname = {'oxford': u'<br>{0}牛津词典{1}'.format(html_panel_head,html_panel_tail),
                        'collins': u'<br>{0}柯林斯词典{1}'.format(html_panel_head,html_panel_tail)}
            dictname_raw = {'oxford': u'{0}牛津词典{1}'.format("<b>","</b><br>"),
                        'collins': u'{0}柯林斯词典{1}'.format("<br><b>","</b><br>")}
            #dictname = {'oxford': u'<br>牛津词典<hr>',
            #            'collins': u'<br>柯林斯词典<hr>'}
            for dname, dmeans in self.means.iteritems():
                if dname in dictname:
                    back_idx = len(back)
                    back.append(dictname[dname])
                    for m in dmeans:
                        if 'en' in m:
                            back.append(m['en'])
                        if 'zh' in m:
                            back.append(m['zh'])
                    dict_mean = [dictname_raw[dname]]
                    dict_mean.extend(back[back_idx+1:])
                    res_dict[dname] = ''.join(dict_mean)
        #第七行, 英文释义
        back_idx = len(back)
        if self.enmeans:
            for dmeans in self.enmeans:
                for posp, enmeanlist in dmeans.iteritems():
                    back.append('<br><b>' + posp + '</b>')
                    for idx, enx in enumerate(enmeanlist):
                        if 'tr' in enx and enx['tr']:
                            x = '; '.join(enx['tr'])
                            back.append( str(idx+1)+'. '+x)
                        if 'example' in enx and enx['example']:
                            for x in enx['example']:
                                back.append('    ' + x)
                        if 'similar_word' in enx and enx['similar_word']:
                            x = '; '.join(enx['similar_word'])
                            back.append('    similar: '+x)
        res_dict['enmean'] = '\n'.join(back[back_idx:])
        #合成卡片内容
        res_dict['back'] = html_templ_head + sepr.join(back) + html_templ_tail
        return res_dict

    #生成HTML卡片结果数据
    def gen_htmlvcard_data(self, filters):
        def _gen_htmlcard_impl():
            return VCardRenderer().render(self, "html_vcard")
        cboper=[_gen_htmlcard_impl]
        res = self.export_db(filters, cboper=cboper)
        if res:
            return cboper[1]
        else:
            return []

    #返回需要制作anki卡片的数据json
    def gen_flashcard_data(self):
        renderer = VCardRenderer()
        schema_name = "anki_card"
        res_dict = renderer.render(self, schema_name)
        html_head = u"<html><head><meta charset='utf-8' /><link href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css' rel='stylesheet'></head><body>"
        html_tail = u"</body></html>"
        back = html_head + \
            res_dict["basic"] + \
            res_dict["posp"] + \
            res_dict["tag"] + \
            res_dict["transform"] + \
            res_dict["mean"] + \
            res_dict["vocabulary"] + \
            res_dict["oxford"] + \
            res_dict["collins"] + \
            res_dict["enmean"] + \
            html_tail
        res_dict["back"] = back
        return res_dict

    #生成flashcard内容
    def make_flashcard(self):
        delimiter=u"\t"
        carddata = self.gen_flashcard_data()
        return carddata['front'] + delimiter + carddata['back']

"""
翻译方法, 调用网络翻译内容, 解析结果
"""
class BDTranslation(object):
    def __init__(self):
        self.sess = requests.session()
        self.req_dict = dict()
        self.req_dict_v = dict()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sess.close()

    def _init_request(self):
        cookie_dict = {'locale': 'zh', 'BAIDUID': '1A2E4E5A00EF753F3C8B59F9FF000AB5:FG=1'}
        self.sess.cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        url = 'https://fanyi.baidu.com'
        headers = {'Host': 'fanyi.baidu.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36', 'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8','Connection': 'keep-alive', 'Referer': 'https://fanyi.baidu.com/', 'X-Requested-With': 'XMLHttpRequest'}
        self.req_dict = {"url": url, "headers": headers}
        self.req_dict_v = {"url": "https://www.vocabulary.com", "headers": {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0', 'Host':'www.vocabulary.com', 'Referer': 'https://www.vocabulary.com/dictionary/'}}
        try:
            rsp = self.sess.get(**self.req_dict_v)
            if rsp.status_code!=200:
                return False
            rsp = self.sess.get(**self.req_dict)
            if rsp.status_code!=200:
                return False
            return BDTranslation.s_parse_jsvar(rsp)
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

    @staticmethod
    def _log_translate_result(result_info):
        trans_log(result_info)

    def _translate_request(self, word):
        word_obj = WordTranslateResult()
        word_in_dict = word_obj.read_result_from_db(word)
        if not word_in_dict:
            srclang = BDTranslation.s_detect_lang(word)
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
                if not res:
                    return None
                #fanyi.baidu
                self.req_dict['url'] = 'https://fanyi.baidu.com/v2transapi'
                self.req_dict['data'] = BDTranslation.s_gen_payload(word, html_ctx, srclang)
                rsp = self.sess.post(**self.req_dict)
                res = word_obj.parse_baidu_rsp(rsp)
                if res:
                    word_obj.write_result_to_db()
                    return word_obj.gen_flashcard_data()
                else:
                    return None
            except Exception as e:
                trans_log(u"translate_req {0} except {1}".format(word, e))
                return None
        else:
            return word_obj.gen_flashcard_data()

    """
    API
    """
    def translate(self, word):
        result = self._translate_request(word)
        if result:
            BDTranslation._log_translate_result(u"{0} OK!".format(word))
            return result
        else:
            BDTranslation._log_translate_result(u"{0} fail ...".format(word))
            return {}

    def query(self, pattern):
        pattern = pattern.replace('*','%')
        word_obj = WordTranslateResult()
        res = word_obj.gen_htmlvcard_data({"word":pattern})
        return res
