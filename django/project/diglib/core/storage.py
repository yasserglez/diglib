# -*- coding: utf-8 -*-

import os
import hashlib

import magic
import ssdeep

from diglib.core.handlers import get_handler
from diglib.core.lang import get_lang


# File extension for MIME types.
_EXTENSIONS = {
    'text/plain': '.txt',
    'application/pdf': '.pdf'
}


# Exceptions raised by the Storage class.

class StorageError(Exception):
    pass


class DocumentError(StorageError):
    pass 


class DocumentNotFound(DocumentError):
    pass


class DuplicateError(DocumentError):
    pass


class ExactDuplicateError(DuplicateError):
    pass


class SimilarDuplicateError(DuplicateError):
    pass


class NotRetrievableError(DocumentError):
    pass


# All interaction with the library is done using an instance of this class.
class Storage(object):
    
    @property
    def documents_dir(self):
        return self._documents_dir
    
    @property
    def thumbnails_dir(self):
        return self._thumbnails_dir

    def __init__(self, index, database, documents_dir, thumbnails_dir,
                 thumbnail_width, thumbnail_height):
        self._index = index
        self._database = database
        self._documents_dir = documents_dir
        self._thumbnails_dir = thumbnails_dir
        self._thumbnail_width = thumbnail_width
        self._thumbnail_height = thumbnail_height
        self._magic = magic.open(magic.MAGIC_MIME_TYPE | magic.MAGIC_NO_CHECK_TOKENS)
        self._magic.load()

    def get(self, hash_md5):
        document = self._database.get(hash_md5)
        if document is None:
            raise DocumentNotFound()
        return document

    def add(self, document_data, initial_metadata, initial_tags):
        document_size = len(document_data)
        hash_md5 = hashlib.md5(document_data).hexdigest()
        hash_ssdeep = ssdeep.hash(document_data)
        self._check_duplicated(document_size, hash_md5, hash_ssdeep)
        path = map(lambda i: hash_md5[i-4:i], [4, 8, 12, 16, 20, 24, 28, 32])
        mime_type = self._magic.buffer(document_data)
        # Save the document.
        document_path = os.path.join(*path) + self._EXTENSIONS[mime_type]
        os.makedirs(os.path.join(self._documents_dir, os.path.join(*path[:-1]))) 
        with open(os.path.join(self.documents_dir, document_path), 'wb') as file:
            file.write(document_data)
        # Save the thumbnail (if any).
        handler = get_handler(document_path, mime_type)
        thumbnail_data = handler.get_thumbnail(self._thumbnail_width, self._thumbnail_height)
        thumbnail_path = os.path.join(*path) + '.png' if thumbnail_data else None
        if thumbnail_path:
            os.makedirs(os.path.join(self._thumbnails_dir, os.path.join(*path[:-1])))
            with open(os.path.join(self.thumbnail_path, thumbnail_path), 'wb') as file:
                file.write(thumbnail_data)
        # Add the document to the database and the index.
        content = handler.get_content()
        language_code = get_lang(content)
        document = self._database.create(hash_md5, hash_ssdeep, mime_type, content, 
                                         document_path, document_size, thumbnail_path, 
                                         language_code, initial_tags)
        self._index.add(document, ' '.join([initial_metadata, handler.get_metadata()]))
        try:
            # Check if the document can be retrieved later.
            self._check_retrievable(document)
        except:
            self.delete(document.hash_md5)
            raise # Re-raise the exception.

    def update_tags(self, hash_md5, tags):
        self._index.update_tags(hash_md5, tags)
        self._database.update_tags(hash_md5, tags)

    def search(self, query, start_index=0, end_index=None):
        return self._index.search(query, start_index, end_index)

    def delete(self, hash_md5):
        document = self._database.get(hash_md5)
        os.remove(os.path.join(self.documents_dir, document.document_path))
        thumbnail_full_path = os.path.join(self.thumbnail_path, document.thumbnail_path)
        if os.path.isfile(thumbnail_full_path):
            os.remove(thumbnail_full_path)
        self._database.delete(hash_md5)
        self._index.delete(hash_md5)

    def close(self):
        self._database.close()
        self._index.close()

    # Check if the document (or a similar document) is already in the database.
    def _check_duplicated(self, document_size, hash_md5, hash_ssdeep):
        if self._database.get(hash_md5) is not None:
            raise ExactDuplicateError()
        eps = max(0.25 * document_size, 1024)
        lower_size = max(0, document_size - eps)
        upper_size = document_size + eps
        documents = self._database.get_similar_documents(lower_size, upper_size)
        for document in documents:
            score = ssdeep.compare(hash_ssdeep, document.hash_ssdeep)
            if score > 75:
                raise SimilarDuplicateError()

    # Check if the document can be retrieved with the available information.
    def _check_retrievable(self, document):
        if not (self._database.is_retrievable(document.hash_md5) or
                self._index.is_retrievable(document.hash_md5)):
            raise NotRetrievableError()
