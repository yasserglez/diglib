#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import unittest

from diglib.core import DigitalLibrary, error
from diglib.core.index import XapianIndex
from diglib.core.database import SQLAlchemyDatabase


class TestDigitalLibrary(unittest.TestCase):

    def setUp(self):
        self._test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test')
        self._library_dir = os.path.join(self._test_dir, 'data')
        self._library = DigitalLibrary(self._library_dir, XapianIndex, SQLAlchemyDatabase)

    def tearDown(self):
        self._library.close()
        shutil.rmtree(self._library_dir)

    def test_add_doc_txt(self):
        txt_path = os.path.join(self._test_dir, 'es.txt')
        tags = set(['vine', 'copula', 'veda'])
        doc = self._library.add_doc(txt_path, tags)
        self.assertEqual(doc.mime_type, 'text/plain')
        self.assertEqual(doc.small_thumbnail_abspath, None)
        self.assertEqual(doc.normal_thumbnail_abspath, None)
        self.assertEqual(doc.large_thumbnail_abspath, None)
        self.assertEqual(doc.language_code, 'es')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_pdf(self):
        pdf_path = os.path.join(self._test_dir, 'en.pdf')
        tags = set(['veda']) # Only one tag to force to check if this doc
                             # can be retrieved using the information in the index.
        doc = self._library.add_doc(pdf_path, tags)
        self.assertEqual(doc.mime_type, 'application/pdf')
        self.assertNotEqual(doc.small_thumbnail_abspath, None)
        self.assertNotEqual(doc.normal_thumbnail_abspath, None)
        self.assertNotEqual(doc.large_thumbnail_abspath, None)
        self.assertEqual(doc.language_code, 'en')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_all(self):
        txt_doc = self.test_add_doc_txt()
        pdf_doc = self.test_add_doc_pdf()
        other_txt_doc = self._library.get_doc(txt_doc.hash_md5)
        other_pdf_doc = self._library.get_doc(pdf_doc.hash_md5)
        self._assert_docs_equal(txt_doc, other_txt_doc)
        self._assert_docs_equal(pdf_doc, other_pdf_doc)

    def test_add_doc_exact_duplicate(self):
        with self.assertRaises(error.ExactDuplicateError):
            self.test_add_doc_txt()
            self.test_add_doc_txt()

    def test_add_doc_similar_duplicate(self):
        with self.assertRaises(error.SimilarDuplicateError):
            self.test_add_doc_txt()
            similar_path = os.path.join(self._test_dir, 'similar.txt')
            self._library.add_doc(similar_path, set(['vine', 'copula', 'veda']))

    def test_add_doc_not_retrievable(self):
        with self.assertRaises(error.NotRetrievableError):
            doc_path = os.path.join(self._test_dir, 'not-retrievable.txt')
            self._library.add_doc(doc_path, set(['veda']))

    def test_get_doc_not_found(self):
        with self.assertRaises(error.DocumentNotFound):
            self._library.get_doc('7d78df0a62e07eeeef6b942abe5bdc7f')

    def test_delete_doc(self):
        pdf_doc = self.test_add_doc_pdf()
        self._library.delete_doc(pdf_doc.hash_md5)
        with self.assertRaises(error.DocumentNotFound):
            self._library.get_doc(pdf_doc.hash_md5)

    def test_get_all_tags(self):
        self.assertSetEqual(self._library.get_all_tags(), set())

    def test_add_tag(self):
        self._library.add_tag('a')
        self.assertSetEqual(self._library.get_all_tags(), set('a'))
        self._library.add_tag('b')
        self._library.add_tag('c')
        self.assertSetEqual(self._library.get_all_tags(), set('abc'))
        
    def test_delete_tag_free(self):
        self._library.add_tag('a')
        self._library.delete_tag('a')
        self.assertSetEqual(self._library.get_all_tags(), set())
        
    def test_delete_tag_assigned(self):
        original = self.test_add_doc_txt()
        self._library.delete_tag('veda')
        modified = self._library.get_doc(original.hash_md5)
        self.assertSetEqual(modified.tags, set(['vine', 'copula']))
        self.assertListEqual(self._library.search('', set(['veda'])), [])

    def test_delete_tag_not_retrievable(self):
        doc_path = os.path.join(self._test_dir, 'not-retrievable.txt')
        self._library.add_doc(doc_path, set('abc'))
        with self.assertRaises(error.NotRetrievableError):
            self._library.delete_tag('a')

    def test_rename_tag_free(self):
        self._library.add_tag('a')
        self._library.rename_tag('a', 'b')
        self.assertSetEqual(self._library.get_all_tags(), set('b'))

    def test_rename_tag_assigned(self):
        original = self.test_add_doc_txt()
        self._library.rename_tag('veda', 'a')
        modified = self._library.get_doc(original.hash_md5)
        self.assertSetEqual(modified.tags, set(['vine', 'copula', 'a']))
        self.assertListEqual(self._library.search('', set(['veda'])), [])
        self.assertListEqual(self._library.search('', set(['a'])), [original.hash_md5])

    def test_update_tags(self):
        doc = self.test_add_doc_txt()
        self.assertListEqual(self._library.search('', set('abc')), [])
        self._library.update_tags(doc.hash_md5, set('abc'))
        self.assertListEqual(self._library.search('', set('abc')), [doc.hash_md5])

    def test_tag_freq(self):
        self.test_add_doc_txt()
        self.test_add_doc_pdf()
        self._library.add_tag('a')
        self.assertEqual(self._library.get_tag_freq('a'), 0.0)
        self.assertEqual(self._library.get_tag_freq('vine'), 0.5)
        self.assertEqual(self._library.get_tag_freq('copula'), 0.5)
        self.assertEqual(self._library.get_tag_freq('veda'), 1.0)

    def test_search_empty(self):
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set(['veda'])), [])
        self.test_add_doc_txt()
        self.test_add_doc_pdf()
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set(['veda'])), [])

    def test_search_all(self):
        self.assertListEqual(self._library.search('', set()), [])
        txt_doc = self.test_add_doc_txt()
        self.assertListEqual(self._library.search('', set()), [txt_doc.hash_md5])
        pdf_doc = self.test_add_doc_pdf()
        results = self._library.search('', set())
        self.assertSetEqual(set(results), set([txt_doc.hash_md5, pdf_doc.hash_md5]))

    def test_search_simple(self):
        txt_doc = self.test_add_doc_txt()
        pdf_doc = self.test_add_doc_pdf()
        results = self._library.search('+VEDA evolutionary optimization', set())
        self.assertListEqual(results, [pdf_doc.hash_md5, txt_doc.hash_md5])

    def test_search_filtered(self):
        txt_doc = self.test_add_doc_txt()
        self.test_add_doc_pdf()
        results = self._library.search('+VEDA evolutionary optimization', set(['vine', 'copula', 'veda']))
        self.assertListEqual(results, [txt_doc.hash_md5])

    def _assert_docs_equal(self, x, y):
        self.assertEqual(x.hash_md5, y.hash_md5)
        self.assertEqual(x.hash_ssdeep, y.hash_ssdeep)
        self.assertEqual(x.mime_type, y.mime_type)
        self.assertEqual(x.document_path, y.document_path)
        self.assertEqual(x.document_abspath, y.document_abspath)
        self.assertEqual(x.document_size, y.document_size)
        self.assertEqual(x.thumbnail_path, y.thumbnail_path)
        self.assertEqual(x.small_thumbnail_abspath, y.small_thumbnail_abspath)
        self.assertEqual(x.normal_thumbnail_abspath, y.normal_thumbnail_abspath)
        self.assertEqual(x.large_thumbnail_abspath, y.large_thumbnail_abspath)
        self.assertEqual(x.language_code, y.language_code)
        self.assertSetEqual(x.tags, y.tags)


if __name__ == '__main__':
    unittest.main(verbosity=2)
