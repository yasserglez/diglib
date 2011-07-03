# -*- coding: utf-8 -*-

import os
import hashlib

import magic
import ssdeep

from diglib.core.handlers import get_handler
from diglib.core.lang import get_lang


class DigitalLibraryError(Exception):
    pass


class DocumentError(DigitalLibraryError):
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


class DigitalLibrary(object):
    
    MIME_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf'
    }

    def __init__(self, library_dir, index_class, database_class):
        super(DigitalLibrary, self).__init__()
        if not os.path.isdir(library_dir):
            os.makedirs(library_dir)
        self._index = index_class(os.path.join(library_dir, 'index'))
        self._database = database_class(os.path.join(library_dir, 'database.db'))
        self._documents_dir = os.path.join(library_dir, 'documents')
        self._thumbnails_dir = os.path.join(library_dir, 'thumbnails')
        self._thumbnail_sizes = {'small' : 64, 'normal' : 128, 'large' : 256}
        self._magic = magic.open(magic.MAGIC_MIME_TYPE | magic.MAGIC_NO_CHECK_TOKENS)
        self._magic.load()

    def get(self, hash_md5):
        document = self._database.get(hash_md5)
        if document is None:
            raise DocumentNotFound()
        document_abspath = os.path.join(self._documents_dir, document.document_path)
        document.document_path = document_abspath
        return document

    def add(self, document_path, tags):
        with open(document_path) as file:
            document_data = file.read()
        # Check if the document is already in the library.
        document_size = len(document_data)
        hash_md5 = hashlib.md5(document_data).hexdigest()
        hash_ssdeep = ssdeep.hash(document_data)
        self._check_duplicated(document_size, hash_md5, hash_ssdeep)
        # Copy the document into the library directory.
        path = map(lambda i: hash_md5[i-4:i], [4, 8, 12, 16, 20, 24, 28, 32])
        mime_type = self._magic.buffer(document_data)
        document_path = os.path.join(*path) + self.MIME_TYPES[mime_type]
        document_abspath = os.path.join(self._documents_dir, document_path)
        os.makedirs(os.path.dirname(document_abspath))
        with open(document_abspath, 'wb') as file:
            file.write(document_data)
        # Generate the thumbnails.
        thumbnail_path = None
        handler = get_handler(document_abspath, mime_type)
        for size_name, size in self._thumbnail_sizes.iteritems():
            thumbnail_data = handler.get_thumbnail(size, size)
            if thumbnail_data:
                thumbnail_path = os.path.join(*path) + '.png'
                thumbnail_abspath = os.path.join(self._thumbnails_dir, size_name, thumbnail_path)
                os.makedirs(os.path.dirname(thumbnail_abspath))
                with open(thumbnail_abspath, 'wb') as file:
                    file.write(thumbnail_data)
        # Add the document to the database and the index.
        content = handler.get_content()
        language_code = get_lang(content)
        document = self._database.create(hash_md5, hash_ssdeep, mime_type, content,
                                         document_path, document_size, thumbnail_path,
                                         language_code, tags)
        self._index.add(document, handler.get_metadata())
        # Check if the document can be retrieved with the available information.
        try:
            self._check_retrievable(document)
        except NotRetrievableError:
            self.delete(document.hash_md5)
            raise # Propagate the exception.
        document.document_path = document_abspath 
        return document

    def add_tag(self, tag):
        self._database.add_tag(tag)

    def rename_tag(self, old_name, new_name):
        self._index.rename_tag(old_name, new_name)
        self._database.rename_tag(old_name, new_name)        

    def update_tags(self, hash_md5, tags):
        self._index.update_tags(hash_md5, tags)
        self._database.update_tags(hash_md5, tags)

    def search(self, query, tags):
        return self._index.search(query, tags)

    def delete(self, hash_md5):
        document = self._database.get(hash_md5)
        os.remove(os.path.join(self._documents_dir, document.document_path))
        if document.thumbnail_path:
            for size_name in self._thumbnail_sizes.iterkeys():
                thumbnail_abspath = os.path.join(self._thumbnails_dir, size_name, document.thumbnail_path)
                if os.path.isfile(thumbnail_abspath):
                    os.remove(thumbnail_abspath)
        self._database.delete(hash_md5)
        self._index.delete(hash_md5)

    def close(self):
        self._database.close()
        self._index.close()

    # Check if the document (or a similar document) is already in the database.
    def _check_duplicated(self, document_size, hash_md5, hash_ssdeep):
        if self._database.get(hash_md5) is not None:
            raise ExactDuplicateError()
        eps = max(0.25 * document_size, 102400)
        lower_size = max(0, document_size - eps)
        upper_size = document_size + eps
        documents = self._database.get_similar_documents(lower_size, upper_size)
        for document in documents:
            score = ssdeep.compare(hash_ssdeep, document.hash_ssdeep)
            if score >= 75:
                raise SimilarDuplicateError()

    # Check if the document can be retrieved with the available information.
    def _check_retrievable(self, document):
        if not (self._database.is_retrievable(document.hash_md5) or
                self._index.is_retrievable(document.hash_md5)):
            raise NotRetrievableError()
