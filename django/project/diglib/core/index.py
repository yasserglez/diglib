# -*- coding: utf-8 -*-


class Index(object):

    def add(self, document, metadata):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    # Execute the query and return a tuple with two elements: the total number
    # of results and a list with the MD5 hash of the documents between the
    # start and end indexes.
    def search(self, query, start_index=0, end_index=None):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
