#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import unittest

from diglib.core import DigitalLibrary
from diglib.core.index import XapianIndex
from diglib.core.database import SQLAlchemyDatabase
from diglib.core import DocumentNotFound, ExactDuplicateError, \
                        SimilarDuplicateError, NotRetrievableError


class TestDigitalLibrary(unittest.TestCase):

    def setUp(self):
        self._test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test')
        self._library_dir = os.path.join(self._test_dir, 'data')
        self._library = DigitalLibrary(self._library_dir, XapianIndex, SQLAlchemyDatabase)

    def tearDown(self):
        self._library.close()
        shutil.rmtree(self._library_dir)

    def test_add_txt(self):
        txt_path = os.path.join(self._test_dir, 'es.txt')
        tags = set(['vine', 'copula', 'veda'])
        document = self._library.add(txt_path, tags)
        self.assertEqual(document.mime_type, 'text/plain')
        self.assertEqual(document.thumbnail_path, None)
        self.assertEqual(document.language_code, 'es')
        self.assertSetEqual(document.tags, tags)
        other_document = self._library.get(document.hash_md5)
        self._assert_documents_equal(document, other_document)
        return document

    def test_add_pdf(self):
        pdf_path = os.path.join(self._test_dir, 'en.pdf')
        tags = set(['veda']) # Only one tag to force to check if this document
                             # can be retrieved using the information in the index.
        document = self._library.add(pdf_path, tags)
        self.assertEqual(document.mime_type, 'application/pdf')
        self.assertNotEquals(document.thumbnail_path, None)
        self.assertEqual(document.language_code, 'en')
        self.assertSetEqual(document.tags, tags)
        other_document = self._library.get(document.hash_md5)
        self._assert_documents_equal(document, other_document)
        return document

    def test_add_various(self):
        txt_document = self.test_add_txt()
        pdf_document = self.test_add_pdf()
        other_txt_document = self._library.get(txt_document.hash_md5)
        other_pdf_document = self._library.get(pdf_document.hash_md5)
        self._assert_documents_equal(txt_document, other_txt_document)
        self._assert_documents_equal(pdf_document, other_pdf_document)

    def test_add_exact_duplicate(self):
        with self.assertRaises(ExactDuplicateError):
            self.test_add_txt()
            self.test_add_txt()

    def test_add_similar_duplicate(self):
        with self.assertRaises(SimilarDuplicateError):
            self.test_add_txt()
            similar_path = os.path.join(self._test_dir, 'similar.txt')
            self._library.add(similar_path, set(['vine', 'copula', 'veda']))

    def test_add_not_retrievable(self):
        with self.assertRaises(NotRetrievableError):
            not_retrievable_path = os.path.join(self._test_dir, 'not-retrievable.txt')
            self._library.add(not_retrievable_path, set(['veda']))

    def test_get_not_found(self):
        with self.assertRaises(DocumentNotFound):
            self._library.get('7d78df0a62e07eeeef6b942abe5bdc7f')

    def test_delete(self):
        pdf_document = self.test_add_pdf()
        self._library.delete(pdf_document.hash_md5)
        with self.assertRaises(DocumentNotFound):
            self._library.get(pdf_document.hash_md5)

    def test_get_tags(self):
        self.assertSetEqual(self._library.get_tags(), set())

    def test_add_tag(self):
        self._library.add_tag('a')
        self.assertSetEqual(self._library.get_tags(), set('a'))
        self._library.add_tag('b')
        self._library.add_tag('c')
        self.assertSetEqual(self._library.get_tags(), set('abc'))

    def test_rename_tag_free(self):
        self._library.add_tag('a')
        self._library.rename_tag('a', 'b')
        self.assertSetEqual(self._library.get_tags(), set('b'))

    def test_rename_tag_assigned(self):
        original = self.test_add_txt()
        self._library.rename_tag('veda', 'a')
        modified = self._library.get(original.hash_md5)
        self.assertSetEqual(modified.tags, set(['vine', 'copula', 'a']))
        self.assertListEqual(self._library.search('', set(['veda'])), [])
        self.assertListEqual(self._library.search('', set(['a'])), [original.hash_md5])

    def test_update_tags(self):
        document = self.test_add_txt()
        self.assertListEqual(self._library.search('', set('abc')), [])
        self._library.update_tags(document.hash_md5, set('abc'))
        self.assertListEqual(self._library.search('', set('abc')), [document.hash_md5])

    def test_search_empty(self):
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set(['veda'])), [])
        self.test_add_txt()
        self.test_add_pdf()
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set(['veda'])), [])

    def test_search_all(self):
        self.assertListEqual(self._library.search('', set()), [])
        txt_document = self.test_add_txt()
        self.assertListEqual(self._library.search('', set()), [txt_document.hash_md5])
        pdf_document = self.test_add_pdf()
        results = self._library.search('', set())
        self.assertSetEqual(set(results), set([txt_document.hash_md5,
                                               pdf_document.hash_md5]))

    def test_search_simple(self):
        txt_document = self.test_add_txt()
        pdf_document = self.test_add_pdf()
        results = self._library.search('+VEDA evolutionary optimization', set())
        self.assertListEqual(results, [pdf_document.hash_md5, txt_document.hash_md5])

    def test_search_filtered(self):
        txt_document = self.test_add_txt()
        pdf_document = self.test_add_pdf()
        results = self._library.search('+VEDA evolutionary optimization', 
                                       set(['vine', 'copula', 'veda']))
        self.assertListEqual(results, [txt_document.hash_md5])

    def _assert_documents_equal(self, x, y):
        self.assertEqual(x.hash_md5, y.hash_md5)
        self.assertEqual(x.hash_ssdeep, y.hash_ssdeep)
        self.assertEqual(x.mime_type, y.mime_type)
        self.assertEqual(x.document_path, y.document_path)
        self.assertEqual(x.document_size, y.document_size)
        self.assertEqual(x.thumbnail_path, y.thumbnail_path)
        self.assertEqual(x.language_code, y.language_code)
        self.assertSetEqual(x.tags, y.tags)


if __name__ == '__main__':
    unittest.main(verbosity=2)
