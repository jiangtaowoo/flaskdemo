# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import os
import yaml
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, create_engine, and_
from sqlalchemy.orm import sessionmaker
from collections import OrderedDict
import six
import sys
# Syntax sugar.
_ver = sys.version_info
#: Python 2.x?
is_py2 = (_ver[0] == 2)
#: Python 3.x?
is_py3 = (_ver[0] == 3)

if is_py2:
    def py23_2_unicode(v):
        if isinstance(v, str):
            return v.decode("utf-8")
        else:
            return v
elif is_py3:
    def py23_2_unicode(v):
        if isinstance(v, bytes):
            return v.decode("utf-8")
        else:
            return v


class AdaptorORM(object):
    def __init__(self, modelname, dbname):
        app_base_dir = os.path.dirname(os.path.abspath(__file__))
        self._models_cfg = None
        self._db_name = dbname if os.sep in dbname else os.sep.join([app_base_dir, dbname])
        self._tb_name_exists = []
        self.bTbCreated = False
        self.engine=create_engine("sqlite:///" + self._db_name)
        self.DBSession = sessionmaker(bind=self.engine)
        self.BaseCls = declarative_base()
        self.DBOrmCls = dict()
        self._load_model_config(modelname if os.sep in modelname else os.sep.join([app_base_dir, modelname]))

    def close_database(self):
        pass

    def _create_db_model(self, BaseCls, modelname, modelcfg):
        member_dict = OrderedDict()
        if 'tablename' in modelcfg:
            member_dict['__tablename__'] = modelcfg['tablename']
        if 'PK' in modelcfg:
            for colname in modelcfg['PK']:
                member_dict[colname] = Column(String, primary_key=True)
        if 'cols' in modelcfg:
            for colname, colrequires in six.iteritems(modelcfg['cols']):
                if colname in modelcfg['PK']:
                    continue
                if isinstance(colrequires,list) or int(colrequires)>0:
                    member_dict[colname] = Column(String, nullable=False)
                else:
                    member_dict[colname] = Column(String)
        return type(modelname, (BaseCls,), member_dict)

    def _filter_model_data(self, modelname, modelcfg, **kwargs):
        if modelname in self._models_cfg:
            if 'cols' in modelcfg:
                valid_data = dict()
                for k, v in six.iteritems(kwargs):
                    if k in modelcfg['cols']:
                        valid_data[k] = py23_2_unicode(v)
                return valid_data
        return None

    def _load_model_config(self, model_yaml_config_filepath):
        if os.path.exists(model_yaml_config_filepath):
            model_cfgs = yaml.load(open(model_yaml_config_filepath))
            #define DBORM Class
            self.DBOrmCls = dict()
            for modelname, modelcfg in six.iteritems(model_cfgs):
                self.DBOrmCls[modelname] = self._create_db_model(self.BaseCls, modelname, modelcfg)
            self.BaseCls.metadata.create_all(self.engine)
            self._models_cfg = model_cfgs

    def save_data(self, modelname, modelcfg, **kwargs):
        if modelname in self._models_cfg:
            tbname = self._models_cfg[modelname]['tablename']
            session = self.DBSession()
            valid_data = self._filter_model_data(modelname, modelcfg, **kwargs)
            modelObj = self.DBOrmCls[modelname](**valid_data)
            session.add(modelObj)
            session.commit()
            session.close()

    def update_data(self, modelname, modelcfg, pk_data_d, **kwargs):
        if modelname in self._models_cfg and pk_data_d is not None:
            tbname = self._models_cfg[modelname]['tablename']
            session = self.DBSession()
            modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**pk_data_d).first()
            if modelObj:
                for k, v in six.iteritems(kwargs):
                    if k not in pk_data_d:
                        if hasattr(modelObj, k):
                            setattr(modelObj, k, py23_2_unicode(v))
                session.commit()
            session.close()

    def data_exists(self, modelname, modelcfg, **kwargs):
        session = self.DBSession()
        if modelname in self._models_cfg:
            tbname = self._models_cfg[modelname]['tablename']
            try:
                modelObj = session.query(self.DBOrmCls[modelname]).filter_by(**kwargs).first()
                if modelObj:
                    session.close()
                    return True
            except:
                session.close()
                return False
        session.close()
        return False

    def load_data(self, tablename, fieldslist, **kwargs):
        #parse field list [col1, col2, [col3, col3_as_new_name], col4]
        fieldnames = []
        fieldnameass = []
        if isinstance(fieldslist,list):
            for field_item in fieldslist:
                if isinstance(field_item,list):
                    fname = field_item[0]
                    fnameas = field_item[1]
                    fieldnames.append(fname)
                    fieldnameass.append(fnameas)
                else:
                    fname = field_item
                    fieldnames.append(fname)
                    fieldnameass.append(fname)
        #find dest model
        dst_modelname = ''
        dst_modelcfg = ''
        for modelname, modelcfg in six.iteritems(self._models_cfg):
            if tablename == modelcfg['tablename']:
                dst_modelname = modelname
                dst_modelcfg = modelcfg
                break
        #query data
        session = self.DBSession()
        valid_cond_data = self._filter_model_data( dst_modelname, dst_modelcfg, **kwargs)
        #modelObj_list = session.query(self.DBOrmCls[dst_modelname]).filter_by(**valid_cond_data).all()
        #逐个将kwargs展开, 使用filter函数实现查询, 容纳like类型的查询
        ClsInst = self.DBOrmCls[dst_modelname]
        rule = []
        for k, v in six.iteritems(kwargs):
            if len(v)>2 and '%' in v:
                likefunc = getattr(getattr(ClsInst,k),"like")
                rule.append(likefunc(v))
            else:
                rule.append(getattr(ClsInst,k)==v)
        modelObj_list = session.query(ClsInst).filter(and_(*rule)).all()
        dataset = []
        if modelObj_list and isinstance(modelObj_list, list):
            for modelObj in modelObj_list:
                datarow = [getattr(modelObj,col) for col in fieldnames]
                dataset.append(datarow)
        session.close()
        return fieldnameass, dataset

    """
    API for first model in yaml file
    1. exists
    2. load
    3. save
    4. update
    """
    def exists(self, **kwargs):
        #只处理第一个model
        for modelname, modelcfg in six.iteritems(self._models_cfg):
            return self.data_exists(modelname, modelcfg, **kwargs)

    #根据kwargs里的过滤条件, 找到对应的数据(所有列)返回
    def load(self, **kwargs):
        #只处理第一个model
        for modelname, modelcfg in six.iteritems(self._models_cfg):
            tablename = modelcfg['tablename']
            fieldslist = []
            for k, v in six.iteritems(modelcfg['cols']):
                fieldslist.append(k)
            return self.load_data(tablename, fieldslist, **kwargs)

    def save(self, **kwargs):
        #只处理第一个model
        for modelname, modelcfg in six.iteritems(self._models_cfg):
            self.save_data(modelname, modelcfg, **kwargs)
            break

    """
    pk_data_d:  可以定位唯一一行数据的过滤条件, 如 {pk_col_name = 'the pk value'}
    如果给出的条件可以找到多条记录, 则只更新第一条记录内容
    kwargs: 是更新后的数据, PK主键对应的列不更新
    """
    def update(self, pk_data_d, **kwargs):
        #只处理第一个model
        for modelname, modelcfg in six.iteritems(self._models_cfg):
            self.update_data(modelname, modelcfg, pk_data_d, **kwargs)
