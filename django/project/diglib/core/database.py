# -*- coding: utf-8 -*-


class Database(object):

    # Add the document to the database and return a subclass of the Document class.
    def create(self, hash_md5, hash_ssdeep, mime_type, content,
               document_path, document_size, thumbnail_path,
               language_code, tags):
        raise NotImplementedError()

    # Check if the document can be retrieved with the available information.
    def is_retrievable(self, hash_md5):
        raise NotImplementedError()
    
    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()
    
    # Return None if there is not a document identified by the given hash.
    def get(self, hash_md5):
        raise NotImplementedError()

    # Get documents which size is between the given values.
    def get_similar_documents(self, lower_size, upper_size):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()
