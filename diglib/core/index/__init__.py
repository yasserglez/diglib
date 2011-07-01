# -*- coding: utf-8 -*-


class Index(object):

    def __init__(self, index_dir):
        pass 

    def add(self, document, metadata):
        raise NotImplementedError()
    
    # Check if the document can be retrieved with the available information.
    def is_retrievable(self, hash_md5):
        raise NotImplementedError()
    
    def rename_tag(self, old_name, new_name):
        raise NotImplementedError()    

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    # Get the MD5 hashes of the documents with the given tags that match the query. 
    def search(self, query, tags):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
