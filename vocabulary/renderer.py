# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import compat
import os
import inspect
import re
import yaml
from metacls import Singleton

"""
翻译结果渲染
"""
class WordModelRenderer(object):
    __metaclass__ = Singleton

    def __init__(self):
        cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        schema_filename = os.sep.join([cur_dir, "models", "renderschema.yaml"])
        res = WordModelRenderer._build_schema_tree(schema_filename)
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
        """
        渲染的情况分为:
        1. 为list数据进行渲染
           a. 方式一: list中的每个元素均采用一个模板渲染(RAW_STYLE)
           b. 方式二: list中的元素内容, 与渲染模板匹配, 根据匹配结果渲染
        2. 为dict数据进行渲染
           a. 方式一: 根据key匹配渲染模板, 将value按模板渲染
           b. 方式二: 根据key匹配渲染模板, 将key, value按模板渲染
        """
        #只支持字符串渲染或数字
        if isinstance(data,list) or isinstance(data,dict) or isinstance(data,tuple): #not compat.is_str_or_unicode(data):
            return data
        if isinstance(schema_node, dict):
            #按字典匹配内容渲染
            if data in schema_node['match']:
                return compat.py23_2_unicode(schema_node['match'][data]).format(data)
            return compat.py23_2_unicode(schema_node['except']).format(data)
        return compat.py23_2_unicode(schema_node).format(data)

    @staticmethod
    def _iter_render(schema_tree, schema_name, schema_node, data):
        """递归完成渲染
        1. type == raw, 直接 .format(data) 完成渲染
        2. type == style, 调用 meta_render 完成渲染
        3. type == template, 调用 _iter_render 递归完成渲染
        """
        def get_style_node(stylefmt):
            #{"type": "style", "data": "SHARED_STYLE.MAP_STYLE.POSP"}
            #{"type": "raw", "data": "<b>{0}</b>"}
            #{"type": "template", "data": "TEMPLATES.T_STAT_LB0"}
            #返回一个指向实际style的next_node, 如果是raw类型, 则返回format本身的字符串
            if not isinstance(stylefmt, dict):
                return None
            fmttype = stylefmt["type"]
            fmtdata = stylefmt["data"]
            if fmttype=="raw":
                return compat.py23_2_unicode(fmtdata)
            elif fmttype=="inline":
                fmtres = {}
                for k in fmtdata:
                    fmtres[k] = get_style_node(fmtdata[k])
                return fmtres
            elif fmttype=="style":
                return schema_tree[fmtdata]
            elif fmttype=="template":
                #找到template对应的schema节点, 递归调用
                schema_next_node = schema_tree[schema_name][fmtdata]
                return schema_next_node
            return None
        #1. 如果没有对应的node, data不做处理直接返回
        if not schema_node:
            return data
        #2. 解析schema_node节点, 开始数据渲染
        if isinstance(schema_node, dict) and "bracket" in schema_node:                  #处理template
            bracket = schema_node["bracket"]
            datatype = schema_node["datatype"]
            styled = schema_node["style"]
            delimiter = styled.get("delimiter","")
            kvconnector = styled.get("kvconnector","")
            korder = styled.get("order")
            whatuse = styled.get("use")
            stylefmt = styled.get("format")
            #if not isinstance(stylefmt, dict):
            #    return data
            next_schema_node = get_style_node(stylefmt)
            if datatype=="list" and isinstance(data, list):
                result = []
                for item in data:
                    result.append(WordModelRenderer._iter_render(schema_tree, schema_name, next_schema_node, item))
                result = delimiter.join(result)
                return compat.py23_2_unicode(bracket).format(result) if bracket else result
            elif datatype=="dict" and isinstance(data, dict):
                if korder is None:
                    korder = [k for k in data]
                result = []
                if whatuse=="v":
                    for k in korder:
                        if k in data and k in next_schema_node and next_schema_node[k]:
                            result.append(WordModelRenderer._iter_render(schema_tree, schema_name, next_schema_node[k], data[k]))
                    result = delimiter.join(result)
                elif whatuse=="kv":
                    for k in korder:
                        if k in data:
                            if isinstance(next_schema_node, dict) and "key" in next_schema_node:
                                rendered_k = WordModelRenderer._iter_render(schema_tree, schema_name, next_schema_node["key"], k)
                            else:
                                rendered_k = k
                            if isinstance(next_schema_node, dict) and "value" in next_schema_node:
                                rendered_v = WordModelRenderer._iter_render(schema_tree, schema_name, next_schema_node["value"], data[k])
                            else:
                                rendered_v = data[k]
                            result.append(compat.py23_2_unicode(kvconnector).format(rendered_k, rendered_v))
                    result = delimiter.join(result)
                return compat.py23_2_unicode(bracket).format(result) if bracket else result
            return data
        else:
            return WordModelRenderer._meta_render(schema_node, data)

    @staticmethod
    def _render_schema_seg(schema_tree, schema_name, schema_seg, word, data):
        #inputdata is list or dict
        template_node = None
        if "template" in schema_seg and "type" in schema_seg["template"]:
            if schema_seg["template"]["type"]=="style":
                template_node = schema_tree[schema_seg["template"]["data"]]
            elif schema_seg["template"]["type"]=="template":
                template_node = schema_tree[schema_name][schema_seg["template"]["data"]]
        highlight_node = schema_tree[schema_seg["highlight"]] if "highlight" in schema_seg and schema_seg["highlight"] else None
        #辅助函数
        def _highlight_keyword(inputs, theword, hilight_node):
            if not hilight_node:
                return inputs
            else:
                #change everything to unicode
                inputs = compat.py23_2_unicode(inputs)
                word_pattern = re.compile(theword, re.IGNORECASE)
                highlight_word = WordModelRenderer._meta_render(hilight_node, theword)
                return word_pattern.sub(highlight_word, inputs)
        result = data
        if template_node:
            result = WordModelRenderer._iter_render(schema_tree, schema_name, template_node, data)
        if highlight_node:
            result = _highlight_keyword(result, word, highlight_node)
        return result

    @staticmethod
    def prepare_audio(wordModelObj):
        if wordModelObj.vocabulary and "audio" in wordModelObj.vocabulary:
            return {u"audio_{0}".format(wordModelObj.word.strip().replace(" ","_")): wordModelObj.vocabulary['audio']}
        return None

    @staticmethod
    def present_basicpart(schemas, schema_tree, schema_name, wordModelObj):
        res_dict = dict()
        word = wordModelObj.word
        basicpart = wordModelObj.gen_basic_data()
        #add audio to basic
        audio_data = WordModelRenderer.prepare_audio(wordModelObj)
        if audio_data:
            basicpart["basic"]["audio"] = audio_data
        schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
        #front, tag, transform, posp, basic, mean
        for seg in basicpart:
            if basicpart[seg]:
                res_dict[seg] = WordModelRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, basicpart[seg])
        return res_dict

    @staticmethod
    def present_vocabulary(schemas, schema_tree, schema_name, wordModelObj):
        res_dict = dict()
        vocabulary = wordModelObj.gen_trim_vocabulary()
        if vocabulary:
            word = wordModelObj.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            #为每个单词分配不同的audio_id {audio_id: audio_mp3_url}
            if 'audio' in vocabulary:
                seg = "audio"
                audio_data = WordModelRenderer.prepare_audio(wordModelObj) #{u"audio_{0}".format(word.strip().replace(" ","_")): vocabulary['audio']}
                res_dict[seg] = WordModelRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, audio_data)
            if 'main' in vocabulary and 'definition' in vocabulary:
                vocabulary['definition_brief'] = vocabulary['definition']
                vocabulary.pop('definition')
            seg = "vocabulary"
            dictionary_encap = {"dictname": "VOCABULARY", "dictcontent": vocabulary}
            res_dict[seg] = WordModelRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[seg], word, dictionary_encap)
        return res_dict

    @staticmethod
    def _present_dictionary(schemas, schema_tree, schema_name, wordModelObj, dictname):
        res_dict = dict()
        if getattr(wordModelObj, dictname, None):
            word = wordModelObj.word
            schema_segs = schemas["SCHEMAS"][schema_name]["SEGMENTS"]
            dictzhnames = {'oxford': u"牛津词典", 'collins': u"柯林斯词典", 'enmeans': u"英文释义"}
            if dictname in dictzhnames and hasattr(wordModelObj, dictname):
                dictionary_encap = {"dictname": dictzhnames[dictname], "dictcontent": getattr(wordModelObj,dictname,None)}
                res_dict[dictname] = WordModelRenderer._render_schema_seg(schema_tree, schema_name, schema_segs[dictname], word, dictionary_encap)
        return res_dict

    @staticmethod
    def present_oxford(schemas, schema_tree, schema_name, wordModelObj):
        dictname = "oxford"
        return WordModelRenderer._present_dictionary(schemas, schema_tree, schema_name, wordModelObj, dictname)

    @staticmethod
    def present_collins(schemas, schema_tree, schema_name, wordModelObj):
        dictname = "collins"
        return WordModelRenderer._present_dictionary(schemas, schema_tree, schema_name, wordModelObj, dictname)

    @staticmethod
    def present_enmeans(schemas, schema_tree, schema_name, wordModelObj):
        dictname = "enmeans"
        return WordModelRenderer._present_dictionary(schemas, schema_tree, schema_name, wordModelObj, dictname)

    #生成FlashCard格式的结果数据, 一行数据, 允许使用HTML标识
    def render(self, wordModelObj, schema_name):
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
          enmeans:    英文翻译,例句
        }
        """
        schemas = self.schemas
        schema_tree = self.schema_tree
        res_dict = {}
        #basic part
        res_tmp = WordModelRenderer.present_basicpart(schemas, schema_tree, schema_name, wordModelObj)
        res_dict.update(res_tmp)
        #vocabulary
        res_tmp = WordModelRenderer.present_vocabulary(schemas, schema_tree, schema_name, wordModelObj)
        res_dict.update(res_tmp)
        #oxford
        res_tmp = WordModelRenderer.present_oxford(schemas, schema_tree, schema_name, wordModelObj)
        res_dict.update(res_tmp)
        #collins
        res_tmp = WordModelRenderer.present_collins(schemas, schema_tree, schema_name, wordModelObj)
        res_dict.update(res_tmp)
        #enmeans
        res_tmp = WordModelRenderer.present_enmeans(schemas, schema_tree, schema_name, wordModelObj)
        res_dict.update(res_tmp)
        #fill blank
        keys = ["front", "basic", "posp", "audio", "mean", "transform", "tag", "stat", "vocabulary", "oxford", "collins", "enmeans"]
        for k in keys:
            if k not in res_dict:
                res_dict[k] = u""
        return res_dict
