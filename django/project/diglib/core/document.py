# -*- coding: utf-8 -*-


class Document(object):
    
    properties = ('hash_md5', 'hash_ssdeep', 'mime_type', 
                  'content', 'document_path', 'document_size', 
                  'thumbnail_path', 'language_code', 'tags')

    def __getattr__(self, name):
        if name in self.properties:
            return self._get_property(name)
        else:
            raise AttributeError()

    def _get_property(self, name):
        raise NotImplementedError()
