#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@Description: 上传控制层
@Author: Zpp
@Date: 2019-10-14 14:53:05
@LastEditors: Zpp
@LastEditTime: 2019-12-11 16:43:35
'''
from flask import request
from models.base import db
from models.system import Document
from conf.setting import document_dir
from sqlalchemy import text
import uuid
import time
import os


class DocumentModel():
    def QueryDocumentByParamRequest(self, params, page=1, page_size=20, order_by='-id'):
        '''
        文档列表
        '''
        s = db.session()
        try:
            Int = ['type', 'deleted']
            data = {}

            for i in Int:
                if params.has_key(i):
                    data[i] = params[i]

            result = Document.query.filter_by(**data).filter(
                Document.name.like("%" + params['name'] + "%") if params.has_key('name') else text('')
            ).order_by(order_by).paginate(page, page_size, error_out=False)

            data = []
            for value in result.items:
                data.append(value.to_json())

            return {'data': data, 'total': result.total}
        except Exception as e:
            print e
            return str(e.message)

    def file_extension(self, filename):
        ary = filename.split('.')
        count = len(ary)
        return ary[count - 1] if count > 1 else ''

    def allowed_file(self, file):
        ALLOWED_EXTENSIONS = set(['gif', 'jpeg', 'jpg', 'png', 'psd', 'bmp', 'tiff', 'tif',
                                  'swc', 'iff', 'jpc', 'jp2', 'jpx', 'jb2', 'xbm', 'wbmp'])

        return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def CreateDocumentRequest(self, files, params):
        '''
        新建文档
        '''
        s = db.session()
        try:
            data = []
            for file in files:
                # 上传
                file_name = file.filename
                ext = self.file_extension(file_name)
                size = len(file.read())
                file_type = params['type']
                file.seek(0)

                fn = '/' + str(time.strftime('%Y/%m/%d'))
                if not os.path.exists(document_dir + fn):
                    os.makedirs(document_dir + fn)
                path = fn + '/' + str(uuid.uuid1()) + '.' + ext
                file.save(document_dir + path)

                if self.allowed_file(file_name):
                    file_type = 1

                item = Document(
                    document_id=uuid.uuid4(),
                    admin_id=params['admin_id'],
                    name=file_name,
                    type=file_type,
                    ext=ext,
                    path=path,
                    size=size
                )
                s.add(item)
                s.commit()
                data.append({
                    'name': file_name,
                    'size': size,
                    'type': file_type,
                    'src': path
                })

            return data
        except Exception as e:
            s.rollback()
            print e
            return str(e.message)

    def GetDocumentRequest(self, document_id):
        '''
        查询文档
        '''
        s = db.session()
        try:
            document = s.query(Document).filter(Document.document_id == document_id).first()
            if not document:
                return str('文档不存在')

            return document.to_json()
        except Exception as e:
            print e
            return str(e.message)

    def RetrieveDocument(self, document_id):
        '''
        移动文档到回收站
        '''
        s = db.session()
        try:
            s.query(Document).filter(Document.document_id.in_(document_id)).update({Document.deleted: 1}, synchronize_session=False)
            s.commit()
            return True
        except Exception as e:
            print e
            s.rollback()
            return str(e.message)

    def DelDocument(self, document_id):
        '''
        删除文档（包括服务器上文件）
        '''
        s = db.session()
        try:
            res = s.query(Document).filter(Document.document_id.in_(document_id))

            for i in res:
                if(os.path.exists(document_dir + i.path)):
                    os.remove(document_dir + i.path)

            res.delete(synchronize_session=False)
            s.commit()
            return True
        except Exception as e:
            print e
            s.rollback()
            return str(e.message)
