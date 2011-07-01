# -*- coding: utf-8 -*-


class Document(object):

    def __init__(self, hash_md5, hash_ssdeep, mime_type, content, document_path, 
                 document_size, thumbnail_path, language_code, tags):
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self.content = content
        self.document_path = document_path
        self.document_size = document_size
        self.thumbnail_path = thumbnail_path
        self.language_code = language_code
        self.tags = tags


class Database(object):

    def __init__(self, database_file):
        raise NotImplementedError()

    # Add the document to the database and return an instance of the Document class.
    def create(self, hash_md5, hash_ssdeep, mime_type, content, document_path, 
               document_size, thumbnail_path, language_code, tags):
        raise NotImplementedError()

    def get(self, hash_md5):
        raise NotImplementedError()

    # Check if the document can be retrieved with the available information.
    def is_retrievable(self, hash_md5):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()
    
    def add_tag(self, tag):
        raise NotImplementedError()

    def rename_tag(self, old_name, new_name):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    # Get documents which size is between the given values.
    def get_similar_documents(self, lower_size, upper_size):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
