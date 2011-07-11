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

import xapian

from diglib.core.lang import LANGUAGES, get_stopwords


class Index(object):

    def __init__(self, index_dir):
        pass 

    def add_doc(self, doc, content, metadata):
        raise NotImplementedError()

    # Get the number of terms of a document.
    def get_doc_terms_count(self, hash_md5):
        raise NotImplementedError()
    
    def delete_doc(self, hash_md5):
        raise NotImplementedError()    

    def rename_tag(self, old_name, new_name):
        raise NotImplementedError()

    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()

    def delete_tag(self, tag):
        raise NotImplementedError()
    
    # Get the MD5 hashes of the documents with the given tags that match the query. 
    def search(self, query, tags):
        raise NotImplementedError()    

    def close(self):
        raise NotImplementedError()


# Xapian index.

class XapianIndex(Index):

    # Prefixes of the terms in the index.
    ID_PREFIX = 'I'
    CONTENT_PREFIX = 'C'
    METADATA_PREFIX = 'M'
    TAG_PREFIX = 'T'
    
    def __init__(self, index_dir):
        super(XapianIndex, self).__init__(index_dir)
        self._index = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        self._stoppers = {}
        for lang in LANGUAGES:
            stopper = xapian.SimpleStopper()
            for stopword in get_stopwords(lang):
                stopper.add(stopword)
            self._stoppers[lang] = stopper

    def add_doc(self, doc, content, metadata):
        generator = xapian.TermGenerator()
        generator.index_text_without_positions(metadata, 1, self.METADATA_PREFIX)
        # Index the content of the document.
        generator.set_stemmer(xapian.Stem(doc.language_code))
        generator.set_stopper(self._stoppers[doc.language_code])
        generator.index_text(content, 1, self.CONTENT_PREFIX)
        xapian_doc = generator.get_document()
        for tag in doc.tags:
            xapian_doc.add_boolean_term(self.TAG_PREFIX + tag)
        xapian_doc.add_boolean_term(self.ID_PREFIX + doc.hash_md5)
        xapian_doc.set_data(doc.hash_md5)
        self._index.add_document(xapian_doc)
        self._index.flush()

    def get_doc_terms_count(self, hash_md5):
        xapian_doc = self._get_xapian_doc(hash_md5)
        terms_count = xapian_doc.termlist_count()
        return terms_count
    
    def delete_doc(self, hash_md5):
        self._index.delete_document(self.ID_PREFIX + hash_md5)
        self._index.flush()

    def rename_tag(self, old_name, new_name):
        old_term = self.TAG_PREFIX + old_name
        if self._index.get_termfreq(old_term) > 0:
            new_term = self.TAG_PREFIX + new_name
            enquire = xapian.Enquire(self._index)
            enquire.set_query(xapian.Query(old_term))
            mset = enquire.get_mset(0, self._index.get_doccount())
            for match in mset:
                xapian_doc = match.document
                xapian_doc.remove_term(old_term)
                xapian_doc.add_boolean_term(new_term)
                self._index.replace_document(xapian_doc.get_docid(), xapian_doc)
        self._index.flush()

    def update_tags(self, hash_md5, tags):
        xapian_doc = self._get_xapian_doc(hash_md5)
        for term in xapian_doc:
            if term.term.startswith(self.TAG_PREFIX):
                xapian_doc.remove_term(term.term)
        for tag in tags:
            xapian_doc.add_boolean_term(self.TAG_PREFIX + tag)
        self._index.replace_document(xapian_doc.get_docid(), xapian_doc)
        self._index.flush()

    def delete_tag(self, tag):
        term = self.TAG_PREFIX + tag
        enquire = xapian.Enquire(self._index)
        enquire.set_query(xapian.Query(term))
        mset = enquire.get_mset(0, self._index.get_doccount())
        for match in mset:
            xapian_doc = match.document
            xapian_doc.remove_term(term)
            self._index.replace_document(xapian_doc.get_docid(), xapian_doc)
        self._index.flush()

    def search(self, query, tags):
        docs = []
        enquire = xapian.Enquire(self._index)
        query = self._parse_query(query) if query.strip() else xapian.Query.MatchAll
        if tags:
            filter = xapian.Query(xapian.Query.OP_AND, [self.TAG_PREFIX + tag for tag in tags])
            filter = xapian.Query(xapian.Query.OP_SCALE_WEIGHT, filter, 0)
        else: 
            filter = xapian.Query.MatchAll
        enquire.set_query(xapian.Query(xapian.Query.OP_AND, filter, query))
        mset = enquire.get_mset(0, self._index.get_doccount())
        for match in mset:
            xapian_doc = match.document
            docs.append(xapian_doc.get_data())
        return docs    

    def close(self):
        self._index.flush()

    def _get_xapian_doc(self, hash_md5):
        enquire = xapian.Enquire(self._index)
        enquire.set_query(xapian.Query(self.ID_PREFIX + hash_md5))
        mset = enquire.get_mset(0, 1)
        xapian_doc = self._index.get_document(mset[0].docid)
        return xapian_doc

    def _parse_query(self, query):
        parser = xapian.QueryParser()
        parser.set_database(self._index)
        tag_query = parser.parse_query(query, 0, self.TAG_PREFIX)
        metadata_query = parser.parse_query(query, 0, self.METADATA_PREFIX)
        content_query = parser.parse_query(query, xapian.QueryParser.FLAG_DEFAULT, self.CONTENT_PREFIX)
        for lang in LANGUAGES:
            parser.set_stemmer(xapian.Stem(lang))
            parser.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
            parser.set_stopper(self._stoppers[lang])
            content_query = xapian.Query(xapian.Query.OP_OR, content_query,
                                         parser.parse_query(query, 0, self.CONTENT_PREFIX))
        tag_query = xapian.Query(xapian.Query.OP_SCALE_WEIGHT, tag_query, 15)
        metadata_query = xapian.Query(xapian.Query.OP_SCALE_WEIGHT, metadata_query, 5)
        final_query = xapian.Query(xapian.Query.OP_OR, tag_query, metadata_query)
        final_query = xapian.Query(xapian.Query.OP_OR, final_query, content_query)
        return final_query
