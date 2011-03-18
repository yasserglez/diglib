# -*- coding: utf-8 -*-

import xapian

from diglib.core.index import Index
from diglib.core.document import Document
from diglib.core.database import Database
from diglib.core.storage import Storage
from diglib.core.lang import SUPPORTED_LANGS, get_stopwords


class DjangoDocument(Document):

    def __init__(self):
        raise NotImplementedError()

    def _get_property(self, name):
        raise NotImplementedError()


class DjangoDatabase(Database):
    
    def __init__(self):
        pass

    def create(self, hash_md5, hash_ssdeep, mime_type, content,
               document_path, document_size, thumbnail_path,
               language_code, tags):
        raise NotImplementedError()

    def is_retrievable(self, hash_md5):
        raise NotImplementedError()
    
    def update_tags(self, hash_md5, tags):
        raise NotImplementedError()
    
    def get(self, hash_md5):
        raise NotImplementedError()

    def get_similar_documents(self, lower_size, upper_size):
        raise NotImplementedError()

    def delete(self, hash_md5):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class XapianIndex(object):
    
    # Prefixes of the terms in the index.
    ID_PREFIX = 'I'
    CONTENT_PREFIX = 'C'
    METADATA_PREFIX = 'M'
    TAG_PREFIX = 'T'
    
    def __init__(self, index_dir):
        self._index = xapian.WritableDatabase(index_dir, xapian.DB_CREATE_OR_OPEN)
        self._stoppers = {}
        for lang in SUPPORTED_LANGS:
            stopper = xapian.SimpleStopper()
            for stopword in get_stopwords(lang):
                stopper.add(stopword)
            self._stoppers[lang] = stopper

    def add(self, document, metadata):
        generator = xapian.TermGenerator()
        generator.index_text_without_positions(metadata, 1, self.METADATA_PREFIX)
        # Index the content of the document.
        generator.set_stemmer(xapian.Stem(document.language_code))
        generator.set_stopper(self._stoppers[document.language_code])
        generator.index_text(document.content, 1, self.CONTENT_PREFIX)
        xapian_document = generator.get_document()
        for tag in document.tags:
            xapian_document.add_boolean_term(self.TAG_PREFIX + tag)
        xapian_document.add_boolean_term(self.ID_PREFIX + document.hash_md5)
        xapian_document.set_data(document.hash_md5)
        self._index.add_document(xapian_document)
        self._index.flush()

    def is_retrievable(self, hash_md5):
        xapian_document = self._get_xapian_document(hash_md5)
        return xapian_document.termlist_count() > 100

    def update_tags(self, hash_md5, tags):
        xapian_document = self._get_xapian_document(hash_md5)
        for term in xapian_document:
            if term.term.startswith(self.TAG_PREFIX):
                xapian_document.remove_term(term.term)
        for tag in tags:
            xapian_document.add_boolean_term(self.TAG_PREFIX + tag)                
        self._index.replace_document(xapian_document.get_docid(), xapian_document)
        self._index.flush()

    def delete(self, hash_md5):
        self._index.delete_document(self.ID_PREFIX + hash_md5)
        self._index.flush()

    def search(self, query, start_index, end_index):
        results = []
        enquire = xapian.Enquire(self._index)
        parsed_query = self._parse_query(query)
        enquire.set_query(parsed_query)
        mset = enquire.get_mset(start_index, (end_index - start_index) + 1, 100)
        for match in mset:
            xapian_document = match.get_document()
            results.append(xapian_document.get_data())
        return (mset.get_matches_estimated(), results)

    def close(self):
        self._index.flush()
        
    def _get_xapian_document(self, hash_md5):
        enquire = xapian.Enquire(self._index)
        enquire.set_query(xapian.Query(self.ID_PREFIX + hash_md5))
        mset = enquire.get_mset(0, 1)
        return self.index.get_document(mset[0].get_docid())
    
    def _parse_query(self, query):
        parser = xapian.QueryParser()
        parser.set_database(self._index)
        tag_query = parser.parse_query(query, 0, self.TAG_PREFIX)
        metadata_query = parser.parse_query(query, 0, self.METADATA_PREFIX)
        content_query = parser.parse_query(query, xapian.QueryParser.FLAG_DEFAULT, self.CONTENT_PREFIX)
        for lang in SUPPORTED_LANGS:
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
