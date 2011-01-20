# -*- coding: utf-8 -*-

import os

from django.conf import settings

from diglib.core.index import Index
from diglib.core.database import Database
from diglib.core.storage import Storage


class DjangoDocument(object):

    def __init__(self):
        raise NotImplementedError()

    def _get_property(self, name):
        raise NotImplementedError()


class DjangoDatabase(object):
    
    def __init__(self):
        raise NotImplementedError()    

    def add(self, hash_md5, hash_ssdeep, mime_type, document_path,
            document_size, thumbnail_path, language_code, tags):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()
    
    def get(self, hash_md5):
        raise NotImplementedError()    

    def delete(self, hash_md5):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class XapianIndex(object):
    
    def __init__(self, index_dir):
        raise NotImplementedError()    

    def add(self, document, metadata):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    def search(self, query, start_index=0, end_index=None):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()



STORAGE = Storage(documents_dir=os.path.join(settings.MEDIA_ROOT, 'diglib', 'documents'),
                  thumbnails_dir=os.path.join(settings.MEDIA_ROOT, 'diglib', 'thumbnails'),
                  index=XapianIndex(os.path.join(settings.MEDIA_ROOT, 'diglib', 'index')),
                  database=DjangoDatabase(),
                  thumbnail_width=256, thumbnail_height=256)
