# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import hashlib
import threading

import magic
import ssdeep

from diglib.core import error
from diglib.core.lang import get_lang
from diglib.core.handlers import get_handler


def _synchronized(lock):
    def decorator(f):
        def wrapper(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)
        return wrapper
    return decorator


class Document(object):

    @property
    def document_abspath(self):
        return os.path.join(self._documents_dir, self.document_path)

    @property
    def small_thumbnail_abspath(self):
        return (os.path.join(self._thumbnails_dir, self.small_thumbnail_path)
                if self.small_thumbnail_path else self.small_thumbnail_path)

    @property
    def normal_thumbnail_abspath(self):
        return (os.path.join(self._thumbnails_dir, self.normal_thumbnail_path)
                if self.normal_thumbnail_path else self.normal_thumbnail_path)            

    @property
    def large_thumbnail_abspath(self):
        return (os.path.join(self._thumbnails_dir, self.large_thumbnail_path)
                if self.large_thumbnail_path else self.large_thumbnail_path)

    def __init__(self, hash_md5, hash_ssdeep, mime_type, document_path, 
                 document_size, small_thumbnail_path, normal_thumbnail_path, 
                 large_thumbnail_path, language_code, tags):
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self._documents_dir = None # Set by DigitalLibrary.
        self.document_path = document_path
        self.document_size = document_size
        self._thumbnails_dir = None # Set by DigitalLibrary.
        self.small_thumbnail_path = small_thumbnail_path
        self.normal_thumbnail_path = normal_thumbnail_path
        self.large_thumbnail_path = large_thumbnail_path
        self.language_code = language_code
        self.tags = tags

    def set_documents_dir(self, documents_dir):
        self._documents_dir = documents_dir

    def set_thumbnails_dir(self, thumbnails_dir):
        self._thumbnails_dir = thumbnails_dir


class DigitalLibrary(object):

    # Supported MIME types.
    MIME_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf',
        'image/vnd.djvu': '.djvu',
        'application/postscript': '.ps',
    }

    # Dimensions of the thumbnails of the documents.
    THUMBNAIL_SIZE_SMALL = 128
    THUMBNAIL_SIZE_NORMAL = 256
    THUMBNAIL_SIZE_LARGE = 512

    # Documents whose similarity is equal or greater
    # than this threshold will be considered equals.
    SSDEEP_THRESHOLD = 80

    # A document should satisfy at least one of the following conditions
    # to be considered retrievable. This should be an invariant for all
    # documents in the database.
    MIN_TERMS = 100

    LOCK = threading.RLock() # Shared by all instances of this class!

    def __init__(self, library_dir, index_class, database_class):
        super(DigitalLibrary, self).__init__()
        if not os.path.isdir(library_dir):
            os.makedirs(library_dir)
        self._index = index_class(os.path.join(library_dir, 'index'))
        self._database = database_class(os.path.join(library_dir, 'database.db'))
        self._dir_levels = 3
        self._documents_dir = os.path.join(library_dir, 'documents')
        self._thumbnails_dir = os.path.join(library_dir, 'thumbnails')
        self._magic = magic.open(magic.MAGIC_MIME_TYPE | magic.MAGIC_NO_CHECK_TOKENS)
        self._magic.load()

    @_synchronized(LOCK)
    def add_doc(self, doc_path, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        with open(doc_path) as file:
            doc_data = file.read()
        # Check if the document is already in the library.
        doc_size = len(doc_data)
        hash_md5 = hashlib.md5(doc_data).hexdigest()
        hash_ssdeep = ssdeep.hash(doc_data)
        self._check_duplicated(hash_md5, hash_ssdeep, doc_size)
        # Copy the document to the library.
        path = ''
        for i in xrange(self._dir_levels):
            path = os.path.join(path, hash_md5[:i + 1])
        path = os.path.join(path, hash_md5)
        mime_type = self._magic.buffer(doc_data)
        if mime_type not in self.MIME_TYPES:
            raise error.DocumentNotSupported()
        doc_path = path + self.MIME_TYPES[mime_type]
        doc_abspath = os.path.join(self._documents_dir, doc_path)
        if not os.path.exists(os.path.dirname(doc_abspath)):
            os.makedirs(os.path.dirname(doc_abspath))
        with open(doc_abspath, 'wb') as file:
            file.write(doc_data)
        handler = get_handler(doc_abspath, mime_type)
        # Generate the thumbnails.
        small_thumbnail_path = None
        normal_thumbnail_path = None
        large_thumbnail_path = None
        for size_name, size in (('small', self.THUMBNAIL_SIZE_SMALL), 
                                ('normal', self.THUMBNAIL_SIZE_NORMAL), 
                                ('large', self.THUMBNAIL_SIZE_LARGE)):
            thumbnail_data = handler.get_thumbnail(size, size)
            if thumbnail_data:
                thumbnail_path = os.path.join(size_name, path + '.png')
                thumbnail_abspath = os.path.join(self._thumbnails_dir, thumbnail_path)
                if not os.path.exists(os.path.dirname(thumbnail_abspath)):
                    os.makedirs(os.path.dirname(thumbnail_abspath))
                with open(thumbnail_abspath, 'wb') as file:
                    file.write(thumbnail_data)
                if size_name == 'small':
                    small_thumbnail_path = thumbnail_path
                elif size_name == 'normal':
                    normal_thumbnail_path = thumbnail_path
                elif size_name == 'large':
                    large_thumbnail_path = thumbnail_path
        # Add the document to the database and the index.
        content = handler.get_content()
        metadata = handler.get_metadata()
        language_code = get_lang(content)
        doc = Document(hash_md5, hash_ssdeep, mime_type, doc_path, 
                       doc_size, small_thumbnail_path, normal_thumbnail_path, 
                       large_thumbnail_path, language_code, tags)
        self._index.add_doc(doc, content, metadata) # To know the number of terms.
        # Check if the document can be retrieved with the available information.
        if not doc.tags and self._index.get_doc_terms_count(doc.hash_md5) < self.MIN_TERMS:
            self._index.delete_doc(hash_md5)
            raise error.DocumentNotRetrievable()
        self._database.add_doc(doc)
        doc.set_documents_dir(self._documents_dir)
        doc.set_thumbnails_dir(self._thumbnails_dir)
        return doc

    @_synchronized(LOCK)
    def get_doc(self, hash_md5):
        doc = self._database.get_doc(hash_md5)
        if doc:
            doc.set_documents_dir(self._documents_dir)
            doc.set_thumbnails_dir(self._thumbnails_dir)
            return doc
        else:
            raise error.DocumentNotFound()

    @_synchronized(LOCK)
    def delete_doc(self, hash_md5):
        doc = self._database.get_doc(hash_md5)
        doc.set_documents_dir(self._documents_dir)
        doc.set_thumbnails_dir(self._thumbnails_dir)
        os.remove(doc.document_abspath)
        if doc.small_thumbnail_abspath:
            os.remove(doc.small_thumbnail_abspath)
        if doc.normal_thumbnail_abspath:
            os.remove(doc.normal_thumbnail_abspath)
        if doc.large_thumbnail_abspath:
            os.remove(doc.large_thumbnail_abspath)
        self._database.delete_doc(hash_md5)
        self._index.delete_doc(hash_md5)

    @_synchronized(LOCK)
    def get_all_tags(self):
        return self._database.get_all_tags()

    @_synchronized(LOCK)
    def get_tag_freq(self, tag):
        return self._database.get_tag_freq(tag)    

    @_synchronized(LOCK)
    def rename_tag(self, old_tag, new_tag):
        old_tag = self._normalize_tag(old_tag)
        new_tag = self._normalize_tag(new_tag)
        self._database.rename_tag(old_tag, new_tag)
        self._index.rename_tag(old_tag, new_tag)

    @_synchronized(LOCK)
    def update_tags(self, hash_md5, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        if not tags and self._index.get_doc_terms_count(hash_md5) < self.MIN_TERMS:
            raise error.DocumentNotRetrievable()
        else:
            self._database.update_tags(hash_md5, tags)
            self._index.update_tags(hash_md5, tags)

    @_synchronized(LOCK)
    def search(self, query, tags, start=None, count=None):
        tags = set([self._normalize_tag(tag) for tag in tags])
        return self._index.search(query, tags, start, count)

    @_synchronized(LOCK)
    def close(self):
        self._database.close()
        self._index.close()

    # Check if the document (or a similar document) is already in the database.
    def _check_duplicated(self, hash_md5, hash_ssdeep, doc_size):
        if self._database.get_doc(hash_md5):
            raise error.DocumentDuplicatedExact()
        eps = max(0.25 * doc_size, 102400)
        lower_size = max(0, doc_size - eps)
        upper_size = doc_size + eps
        docs = self._database.get_similar_docs(lower_size, upper_size)
        for doc in docs:
            score = ssdeep.compare(hash_ssdeep, doc.hash_ssdeep)
            if score >= self.SSDEEP_THRESHOLD:
                raise error.DocumentDuplicatedSimilar()

    def _normalize_tag(self, tag):
        return tag.strip().lower()
