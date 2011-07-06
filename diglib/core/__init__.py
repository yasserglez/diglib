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


class Document(object):
    
    def __init__(self, hash_md5, hash_ssdeep, mime_type, document_path, 
                 document_size, thumbnail_path, language_code, tags):
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self._documents_dir = None # Set by DigitalLibrary.
        self._document_path = document_path
        self.document_size = document_size
        self._thumbnails_dir = None # Set by DigitalLibrary.
        self._thumbnail_path = thumbnail_path
        self.language_code = language_code
        self.tags = tags

    def set_documents_dir(self, documents_dir):
        self._documents_dir = documents_dir

    def set_thumbnails_dir(self, thumbnails_dir):
        self._thumbnails_dir = thumbnails_dir

    @property
    def document_abspath(self):
        return os.path.join(self._documents_dir, self._document_path)

    @property
    def small_thumbnail_abspath(self):
        if self._thumbnail_path:
            return os.path.join(self._thumbnails_dir, 'small', self._thumbnail_path)
        else:
            return None

    @property
    def normal_thumbnail_abspath(self):
        if self._thumbnail_path:
            return os.path.join(self._thumbnails_dir, 'normal', self._thumbnail_path)
        else:
            return None            

    @property
    def large_thumbnail_abspath(self):
        if self._thumbnail_path:
            return os.path.join(self._thumbnails_dir, 'large', self._thumbnail_path)
        else:
            return None        


class DigitalLibrary(object):
    
    MIME_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf'
    }
    
    SMALL_THUMBNAIL_SIZE = 64
    NORMAL_THUMBNAIL_SIZE = 128
    LARGE_THUMBNAIL_SIZE = 256
    
    def __init__(self, library_dir, index_class, database_class):
        super(DigitalLibrary, self).__init__()
        if not os.path.isdir(library_dir):
            os.makedirs(library_dir)
        self._index = index_class(os.path.join(library_dir, 'index'))
        self._database = database_class(os.path.join(library_dir, 'database.db'))
        self._documents_dir = os.path.join(library_dir, 'documents')
        self._thumbnails_dir = os.path.join(library_dir, 'thumbnails')
        self._magic = magic.open(magic.MAGIC_MIME_TYPE | magic.MAGIC_NO_CHECK_TOKENS)
        self._magic.load()
        
    def get(self, hash_md5):
        document = self._database.get(hash_md5)
        if document:
            document.set_documents_dir(self._documents_dir)
            document.set_thumbnails_dir(self._thumbnails_dir)
            return document
        else:
            raise DocumentNotFound()

    def add(self, document_path, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
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
        for size_name, size in (('small', self.SMALL_THUMBNAIL_SIZE),
                                ('normal', self.NORMAL_THUMBNAIL_SIZE),
                                ('large', self.LARGE_THUMBNAIL_SIZE)):    
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
        document = self._database.create(hash_md5, hash_ssdeep, mime_type, document_path,
                                         document_size, thumbnail_path, language_code, tags)
        document.set_documents_dir(self._documents_dir)
        document.set_thumbnails_dir(self._thumbnails_dir)
        self._index.add(document, content, handler.get_metadata())
        # Check if the document can be retrieved with the available information.
        try:
            self._check_retrievable(document)
        except NotRetrievableError:
            self.delete(document.hash_md5)
            raise # Propagate the exception.
        return document

    def get_tags(self):
        return self._database.get_tags()

    def add_tag(self, tag):
        tag = self._normalize_tag(tag)
        self._database.add_tag(tag)

    def rename_tag(self, old_name, new_name):
        old_name = self._normalize_tag(old_name)
        new_name = self._normalize_tag(new_name)
        self._index.rename_tag(old_name, new_name)
        self._database.rename_tag(old_name, new_name)

    def update_tags(self, hash_md5, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        self._index.update_tags(hash_md5, tags)
        self._database.update_tags(hash_md5, tags)

    def get_tag_frequency(self, tag):
        return self._database.get_tag_frequency(tag)

    def search(self, query, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        return self._index.search(query, tags)

    def delete(self, hash_md5):
        document = self._database.get(hash_md5)
        document.set_documents_dir(self._documents_dir)
        document.set_thumbnails_dir(self._thumbnails_dir)
        os.remove(document.document_abspath)
        if document.small_thumbnail_abspath:
            os.remove(document.small_thumbnail_abspath)
        if document.normal_thumbnail_abspath:
            os.remove(document.normal_thumbnail_abspath)
        if document.large_thumbnail_abspath:
            os.remove(document.large_thumbnail_abspath)
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
    
    def _normalize_tag(self, tag):
        return tag.lower()
