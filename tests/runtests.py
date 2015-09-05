#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2013 Yasser González Fernández <ygonzalezfernandez@gmail.com>
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
import sys
import shutil
import unittest

# Allow running this script in source directory.
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
if os.path.isfile(os.path.join(src_dir, 'setup.py')):
    sys.path.insert(0, os.path.normpath(os.path.join(src_dir, 'packages')))

from diglib.core import DigitalLibrary, error
from diglib.core.index import XapianIndex
from diglib.core.database import SQLAlchemyDatabase


class TestDigitalLibrary(unittest.TestCase):

    def setUp(self):
        self._tests_dir = os.path.dirname(os.path.abspath(__file__))
        self._library_dir = os.path.join(self._tests_dir, 'data')
        self._library = DigitalLibrary(self._library_dir, XapianIndex, SQLAlchemyDatabase)

    def tearDown(self):
        self._library.close()
        shutil.rmtree(self._library_dir)
        
    def test_add_doc_ps(self):
        ps_path = os.path.join(self._tests_dir, 'en.ps')
        tags = set('abcd')
        doc = self._library.add_doc(ps_path, tags)
        self.assertEqual(doc.mime_type, 'application/postscript')
        self.assertTrue(os.path.isfile(doc.document_abspath))
        self.assertTrue(os.path.isfile(doc.small_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.normal_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.large_thumbnail_abspath))
        self.assertEqual(doc.language_code, 'en')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_txt(self):
        txt_path = os.path.join(self._tests_dir, 'es.txt')
        tags = set('abc')
        doc = self._library.add_doc(txt_path, tags)
        self.assertEqual(doc.mime_type, 'text/plain')
        self.assertTrue(os.path.isfile(doc.document_abspath))
        self.assertEqual(doc.small_thumbnail_abspath, None)
        self.assertEqual(doc.normal_thumbnail_abspath, None)
        self.assertEqual(doc.large_thumbnail_abspath, None)
        self.assertEqual(doc.language_code, 'es')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_pdf(self):
        pdf_path = os.path.join(self._tests_dir, 'en.pdf')
        tags = set('ab')
        doc = self._library.add_doc(pdf_path, tags)
        self.assertEqual(doc.mime_type, 'application/pdf')
        self.assertTrue(os.path.isfile(doc.document_abspath))
        self.assertTrue(os.path.isfile(doc.small_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.normal_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.large_thumbnail_abspath))
        self.assertEqual(doc.language_code, 'en')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_djvu(self):
        djvu_path = os.path.join(self._tests_dir, 'en.djvu')
        tags = set('a')
        doc = self._library.add_doc(djvu_path, tags)
        self.assertEqual(doc.mime_type, 'image/vnd.djvu')
        self.assertTrue(os.path.isfile(doc.document_abspath))
        self.assertTrue(os.path.isfile(doc.small_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.normal_thumbnail_abspath))
        self.assertTrue(os.path.isfile(doc.large_thumbnail_abspath))
        self.assertEqual(doc.language_code, 'en')
        self.assertSetEqual(doc.tags, tags)
        other_doc = self._library.get_doc(doc.hash_md5)
        self._assert_docs_equal(doc, other_doc)
        return doc

    def test_add_doc_all(self):
        ps_doc = self.test_add_doc_ps()
        txt_doc = self.test_add_doc_txt()
        pdf_doc = self.test_add_doc_pdf()
        djvu_doc = self.test_add_doc_djvu()
        other_ps_doc = self._library.get_doc(ps_doc.hash_md5)
        other_txt_doc = self._library.get_doc(txt_doc.hash_md5)
        other_pdf_doc = self._library.get_doc(pdf_doc.hash_md5)
        other_djvu_doc = self._library.get_doc(djvu_doc.hash_md5)
        self._assert_docs_equal(ps_doc, other_ps_doc)
        self._assert_docs_equal(txt_doc, other_txt_doc)
        self._assert_docs_equal(pdf_doc, other_pdf_doc)
        self._assert_docs_equal(djvu_doc, other_djvu_doc)

    def test_add_doc_exact_duplicate(self):
        with self.assertRaises(error.DocumentDuplicatedExact):
            self.test_add_doc_txt()
            self.test_add_doc_txt()

    def test_add_doc_similar_duplicate(self):
        with self.assertRaises(error.DocumentDuplicatedSimilar):
            self.test_add_doc_txt()
            similar_path = os.path.join(self._tests_dir, 'similar.txt')
            self._library.add_doc(similar_path, set('abc'))

    def test_add_doc_not_retrievable(self):
        with self.assertRaises(error.DocumentNotRetrievable):
            doc_path = os.path.join(self._tests_dir, 'not-retrievable.txt')
            self._library.add_doc(doc_path, set())

    def test_get_doc_not_found(self):
        with self.assertRaises(error.DocumentNotFound):
            self._library.get_doc('7d78df0a62e07eeeef6b942abe5bdc7f')

    def test_delete_doc(self):
        pdf_doc = self.test_add_doc_pdf()
        doc_path = pdf_doc.document_abspath
        small_thumbnail = pdf_doc.small_thumbnail_abspath
        normal_thumbnail = pdf_doc.normal_thumbnail_abspath
        large_thumbnail = pdf_doc.large_thumbnail_abspath
        self._library.delete_doc(pdf_doc.hash_md5)
        self.assertFalse(os.path.exists(doc_path))
        self.assertFalse(os.path.exists(small_thumbnail))
        self.assertFalse(os.path.exists(normal_thumbnail))
        self.assertFalse(os.path.exists(large_thumbnail))
        with self.assertRaises(error.DocumentNotFound):
            self._library.get_doc(pdf_doc.hash_md5)

    def test_add_doc_previously_imported(self):
        pdf_doc = self.test_add_doc_pdf()
        self._library.delete_doc(pdf_doc.hash_md5)
        self.test_add_doc_pdf()

    def test_get_all_tags(self):
        self.assertSetEqual(self._library.get_all_tags(), set())
        self.test_add_doc_txt()
        self.assertSetEqual(self._library.get_all_tags(), set('abc'))

    def test_rename_tag(self):
        original = self.test_add_doc_txt()
        self.assertSetEqual(self._library.get_all_tags(), set('abc'))
        self._library.rename_tag('c', 'z')
        self.assertSetEqual(self._library.get_all_tags(), set('abz'))
        modified = self._library.get_doc(original.hash_md5)
        self.assertSetEqual(modified.tags, set('abz'))
        self.assertListEqual(self._library.search('', set('c')), [])
        self.assertListEqual(self._library.search('', set('z')), [original.hash_md5])
        
    def test_rename_tag_tilde(self):
        original = self.test_add_doc_txt()
        self.assertSetEqual(self._library.get_all_tags(), set('abc'))
        self._library.rename_tag('a', u'á')
        self.assertSetEqual(self._library.get_all_tags(), set(u'ábc'))
        modified = self._library.get_doc(original.hash_md5)
        self.assertSetEqual(modified.tags, set(u'ábc'))
        self.assertListEqual(self._library.search('', set(u'á')), [original.hash_md5])        

    def test_rename_tag_exists(self):
        original = self.test_add_doc_txt()
        self.assertSetEqual(self._library.get_all_tags(), set('abc'))
        self._library.rename_tag('c', 'b')
        self.assertSetEqual(self._library.get_all_tags(), set('ab'))
        modified = self._library.get_doc(original.hash_md5)
        self.assertSetEqual(modified.tags, set('ab'))
        self.assertListEqual(self._library.search('', set('c')), [])
        self.assertListEqual(self._library.search('', set('b')), [original.hash_md5])

    def test_update_tags(self):
        doc = self.test_add_doc_txt()
        self.assertListEqual(self._library.search('', set('xyz')), [])
        self._library.update_tags(doc.hash_md5, set('xyz'))
        self.assertListEqual(self._library.search('', set('xyz')), [doc.hash_md5])
        
    def test_update_tags_tildes(self):
        doc = self.test_add_doc_txt()
        self._library.update_tags(doc.hash_md5, set(u'áéíóóñ'))
        self.assertListEqual(self._library.search('', set(u'áéíóóñ')), [doc.hash_md5])        

    def test_update_tags_not_retrievable(self):
        doc_path = os.path.join(self._tests_dir, 'not-retrievable.txt')
        doc = self._library.add_doc(doc_path, set('abc'))
        with self.assertRaises(error.DocumentNotRetrievable):
            self._library.update_tags(doc.hash_md5, set())
            
    def test_get_doc_count(self):
        self.test_add_doc_ps()
        self.assertEqual(self._library.get_doc_count(), 1)
        self.test_add_doc_txt()
        self.assertEqual(self._library.get_doc_count(), 2)
        self.test_add_doc_pdf()
        self.assertEqual(self._library.get_doc_count(), 3)
        self.test_add_doc_djvu()
        self.assertEqual(self._library.get_doc_count(), 4)
        
    def test_get_tag_count(self):
        self.test_add_doc_ps()
        self.test_add_doc_txt()
        self.test_add_doc_pdf()
        self.test_add_doc_djvu()
        self.assertEqual(self._library.get_tag_count('d'), 1)
        self.assertEqual(self._library.get_tag_count('c'), 2)
        self.assertEqual(self._library.get_tag_count('b'), 3)
        self.assertEqual(self._library.get_tag_count('a'), 4)

    def test_get_tag_freq(self):
        self.test_add_doc_ps()
        self.test_add_doc_txt()
        self.test_add_doc_pdf()
        self.test_add_doc_djvu()
        self.assertEqual(self._library.get_tag_freq('d'), 1.0/4.0)
        self.assertEqual(self._library.get_tag_freq('c'), 2.0/4.0)
        self.assertEqual(self._library.get_tag_freq('b'), 3.0/4.0)
        self.assertEqual(self._library.get_tag_freq('a'), 4.0/4.0)

    def test_search_empty(self):
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set('c')), [])
        self.test_add_doc_txt()
        self.test_add_doc_pdf()
        self.assertListEqual(self._library.search('foo bar', set()), [])
        self.assertListEqual(self._library.search('foo bar', set('c')), [])

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
        results = self._library.search('+VEDA EDA', set())
        self.assertListEqual(results, [pdf_doc.hash_md5, txt_doc.hash_md5])

    def test_search_filtered(self):
        txt_doc = self.test_add_doc_txt()
        self.test_add_doc_pdf()
        results = self._library.search('+VEDA EDA', set('abc'))
        self.assertListEqual(results, [txt_doc.hash_md5])

    def _assert_docs_equal(self, x, y):
        self.assertEqual(x.hash_md5, y.hash_md5)
        self.assertEqual(x.hash_ssdeep, y.hash_ssdeep)
        self.assertEqual(x.mime_type, y.mime_type)
        self.assertEqual(x.document_path, y.document_path)
        self.assertEqual(x.document_abspath, y.document_abspath)
        self.assertEqual(x.document_size, y.document_size)
        self.assertEqual(x.small_thumbnail_abspath, y.small_thumbnail_abspath)
        self.assertEqual(x.normal_thumbnail_abspath, y.normal_thumbnail_abspath)
        self.assertEqual(x.large_thumbnail_abspath, y.large_thumbnail_abspath)
        self.assertEqual(x.language_code, y.language_code)
        self.assertSetEqual(x.tags, y.tags)


if __name__ == '__main__':
    unittest.main(verbosity=2)
