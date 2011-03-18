# -*- coding: utf-8 -*-


class Database(object):

    # Should return a subclass of the Document class.
    def create(self, hash_md5, hash_ssdeep, mime_type, content,
               document_path, document_size, thumbnail_path,
               language_code, tags):
        raise NotImplementedError()

    def add(self, document):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    def get(self, hash_md5):
        raise NotImplementedError()

    def get_similar_documents(self, lower_size, upper_size):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
