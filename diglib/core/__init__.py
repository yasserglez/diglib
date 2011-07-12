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

import magic
import ssdeep

from diglib.core import error
from diglib.core.lang import get_lang
from diglib.core.handlers import get_handler


class Document(object):

    @property
    def document_abspath(self):
        return os.path.join(self._documents_dir, self.document_path)

    @property
    def small_thumbnail_abspath(self):
        return self._get_thumbnail_abspath('small')

    @property
    def normal_thumbnail_abspath(self):
        return self._get_thumbnail_abspath('normal')            

    @property
    def large_thumbnail_abspath(self):
        return self._get_thumbnail_abspath('large')

    def __init__(self, hash_md5, hash_ssdeep, mime_type, document_path, 
                 document_size, thumbnail_path, language_code, tags):
        self.hash_md5 = hash_md5
        self.hash_ssdeep = hash_ssdeep
        self.mime_type = mime_type
        self._documents_dir = None # Set by DigitalLibrary.
        self.document_path = document_path
        self.document_size = document_size
        self._thumbnails_dir = None # Set by DigitalLibrary.
        self.thumbnail_path = thumbnail_path
        self.language_code = language_code
        self.tags = tags

    def set_documents_dir(self, documents_dir):
        self._documents_dir = documents_dir

    def set_thumbnails_dir(self, thumbnails_dir):
        self._thumbnails_dir = thumbnails_dir

    def _get_thumbnail_abspath(self, size_name):
        return (os.path.join(self._thumbnails_dir, size_name, self.thumbnail_path)
                if self.thumbnail_path else None)


class DigitalLibrary(object):

    # Supported MIME types.
    MIME_TYPES = {
        'text/plain': '.txt',
        'application/pdf': '.pdf'
    }

    # Dimensions of the thumbnails of the documents.
    THUMBNAIL_SIZE_SMALL = 128
    THUMBNAIL_SIZE_NORMAL = 256
    THUMBNAIL_SIZE_LARGE = 512

    # Documents whose similarity is equal or greater
    # than this threshold will be considered equals.
    SSDEEP_THRESHOLD = 75

    # A document should satisfy at least one of the following conditions
    # to be considered retrievable. This should be an invariant for all
    # documents in the database.
    MIN_TAGS = 1
    MIN_TERMS = 100

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
        path = map(lambda i: hash_md5[i-2:i], range(2, 32, 2))
        mime_type = self._magic.buffer(doc_data)
        if mime_type not in self.MIME_TYPES:
            raise error.DocumentNotSupported()
        doc_path = os.path.join(*path) + self.MIME_TYPES[mime_type]
        doc_abspath = os.path.join(self._documents_dir, doc_path)
        if not os.path.exists(os.path.dirname(doc_abspath)):
            os.makedirs(os.path.dirname(doc_abspath))
        with open(doc_abspath, 'wb') as file:
            file.write(doc_data)
        # Generate the thumbnails.
        thumbnail_path = None
        handler = get_handler(doc_abspath, mime_type)
        for size_name, size in (('small', self.THUMBNAIL_SIZE_SMALL),
                                ('normal', self.THUMBNAIL_SIZE_NORMAL),
                                ('large', self.THUMBNAIL_SIZE_LARGE)):
            thumbnail_data = handler.get_thumbnail(size, size)
            if thumbnail_data:
                thumbnail_path = os.path.join(*path) + '.png'
                thumbnail_abspath = \
                    os.path.join(self._thumbnails_dir, size_name, thumbnail_path)
                if not os.path.exists(os.path.dirname(thumbnail_abspath)):
                    os.makedirs(os.path.dirname(thumbnail_abspath))
                with open(thumbnail_abspath, 'wb') as file:
                    file.write(thumbnail_data)
        # Add the document to the database and the index.
        content = handler.get_content()
        metadata = handler.get_metadata()
        language_code = get_lang(content)
        doc = Document(hash_md5, hash_ssdeep, mime_type, doc_path,
                       doc_size, thumbnail_path, language_code, tags)
        self._index.add_doc(doc, content, metadata) # To know the number of terms.
        # Check if the document can be retrieved with the available information.
        if not (len(doc.tags) >= self.MIN_TAGS or
                self._index.get_doc_terms_count(doc.hash_md5) >= self.MIN_TERMS):            
            self._index.delete_doc(hash_md5)
            raise error.DocumentNotRetrievable()
        self._database.add_doc(doc)
        doc.set_documents_dir(self._documents_dir)
        doc.set_thumbnails_dir(self._thumbnails_dir)
        return doc

    def get_doc(self, hash_md5):
        doc = self._database.get_doc(hash_md5)
        if doc:
            doc.set_documents_dir(self._documents_dir)
            doc.set_thumbnails_dir(self._thumbnails_dir)
            return doc
        else:
            raise error.DocumentNotFound()

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

    def add_tag(self, tag):
        tag = self._normalize_tag(tag)
        if tag not in self._database.get_all_tags():
            self._database.add_tag(tag)
        else:
            raise error.TagDuplicated()            

    def get_all_tags(self):
        return self._database.get_all_tags()

    def get_tag_freq(self, tag):
        return self._database.get_tag_freq(tag)    

    def rename_tag(self, old_name, new_name):
        old_name = self._normalize_tag(old_name)
        new_name = self._normalize_tag(new_name)
        if new_name not in self._database.get_all_tags():
            self._database.rename_tag(old_name, new_name)
            self._index.rename_tag(old_name, new_name)
        else:
            raise error.TagDuplicated()

    def update_tags(self, hash_md5, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        if not (len(tags) >= self.MIN_TAGS or
                self._index.get_doc_terms_count(hash_md5) >= self.MIN_TERMS):        
            raise error.DocumentNotRetrievable()
        else:
            self._database.update_tags(hash_md5, tags)
            self._index.update_tags(hash_md5, tags)

    def delete_tag(self, tag):
        tag = self._normalize_tag(tag)
        for hash_md5 in self.search('', set([tag])):
            # Removing the tag results in documents that cannot be retrieved?
            doc = self.get_doc(hash_md5)
            if (len(doc.tags) == self.MIN_TAGS and
                self._index.get_doc_terms_count(doc.hash_md5) < self.MIN_TERMS):
                raise error.DocumentNotRetrievable()
        self._database.delete_tag(tag)
        self._index.delete_tag(tag)

    def search(self, query, tags):
        tags = set([self._normalize_tag(tag) for tag in tags])
        return self._index.search(query, tags)    

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
