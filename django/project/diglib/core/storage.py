# -*- coding: utf-8 -*-

import os
import hashlib

from diglib.core import handlers


# File extension for MIME types.
_EXTENSIONS = {'text/plain': '.txt',
               'application/pdf': '.pdf'}


# All interaction with the library is done using an instance of this class.
class Storage(object):
    
    @property
    def documents_dir(self):
        return self._documents_dir
    
    @property
    def thumbnails_dir(self):
        return self._thumbnails_dir

    def __init__(self, documents_dir, thumbnails_dir, index, database,
                 thumbnail_width, thumbnail_height):
        self._index = index
        self._database = database
        self._documents_dir = documents_dir
        self._thumbnails_dir = thumbnails_dir
        self._thumbnail_width = thumbnail_width
        self._thumbnail_height = thumbnail_height

    def get(self, hash_md5):
        return self._database.get(hash_md5)

    def add(self, data, metadata, tags):
        hash_md5 = hashlib.md5(data).hexdigest()
        # Create the directories for the document and the thumbnail.
        path = map(lambda i: hash_md5[i-4:i], [4, 8, 12, 16, 20, 24, 28, 32])
        os.makedirs(os.path.join(self._documents_dir, os.path.join(*path[:-1])))
        os.makedirs(os.path.join(self._thumbnails_dir, os.path.join(*path[:-1])))
        # Detect the MIME type.
        mime_type = ''
        # Save the document.
        document_path = os.path.join(*path) + self._EXTENSIONS[mime_type]
        with open(document_path, 'wb') as file:
            file.write(data)
        thumbnail_path = os.path.join(*path) + '.png'
        document_size = os.path.getsize(document_path)

    def update_tags(self, hash_md5, tags):
        self._index.update_tags(hash_md5, tags)
        self._database.update_tags(hash_md5, tags)

    def delete(self, hash_md5):
        pass
