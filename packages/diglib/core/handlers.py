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
import subprocess
import codecs
import cStringIO

import cairo
import poppler
import magic
import djvu.decode
import PIL.Image


# File handlers used to extract information from the different document formats
# supported by the library. Each handler is identified by the MIME type of the
# format it supports.

class FileHandler(object):

    mime_type = None

    def __init__(self, file_path):
        self._file_path = file_path

    def get_file_path(self):
        return self._file_path

    # Return the file of the file in an UTF-8 encoded string.
    # If the file is not available it should return ''.
    def get_metadata(self):
        raise NotImplementedError()

    # Return the data of a file for the document in PNG format.
    # The thumbnails should not exceed the given width and height.
    def get_thumbnail(self, width, height):
        raise NotImplementedError()

    # Return the file of the file in an UTF-8 encoded string.
    # If the file is not available it should return ''.
    def get_content(self):
        raise NotImplementedError()

    # Close opened resources. The default implementation does nothing.
    def close(self):
        raise NotImplementedError()


class PlainTextHandler(FileHandler):

    mime_type = 'text/plain'

    def __init__(self, file_path):
        super(PlainTextHandler, self).__init__(file_path)
        self._file = codecs.open(file_path, encoding='utf8', errors='ignore')

    def get_metadata(self):
        return ''

    def get_thumbnail(self, width, height):
        return ''

    def get_content(self):
        self._file.seek(0)
        content = self._file.read()
        return content.strip()

    def close(self):
        self._file.close()


class PDFHandler(FileHandler):
    
    mime_type = 'application/pdf'

    def __init__(self, file_path):
        super(PDFHandler, self).__init__(file_path)
        self._document =  poppler.document_new_from_file('file://%s' % file_path, None)
        self._page = self._document.get_page(0)
        self._page_width, self._page_height = self._page.get_size()

    def get_metadata(self):
        metadata = ''
        for name in ('title', 'keywords'):
            value = self._document.get_property(name)
            if value:
                metadata += value.encode('utf8') + ' '
        return metadata.strip()

    def get_thumbnail(self, width, height):
        scale = (width / float(self._page_width)
                 if self._page_width > self._page_height
                 else height / float(self._page_height))
        image_width = int(scale * self._page_width)
        image_height = int(scale * self._page_height)
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, image_width, image_height)
        context = cairo.Context(surface)
        context.scale(scale, scale)
        context.set_source_rgb(1.0, 1.0, 1.0)
        context.rectangle(0.0, 0.0, self._page_width, self._page_height)
        context.fill()
        self._page.render(context)
        file = cStringIO.StringIO()
        surface.write_to_png(file)
        thumbnail = file.getvalue()
        file.close()
        return thumbnail

    def get_content(self):
        args = ['pdftotext', self._file_path, '-']
        output = codecs.EncodedFile(os.tmpfile(), 'utf8', errors='ignore')
        return_code = subprocess.call(args=args, stdout=output)
        content = ''
        if return_code == 0:
            output.seek(0)
            content = output.read()
            output.close()
        return content.strip()

    def close(self):
        self._document = None
        self._page = None


class DJVUHandler(FileHandler):

    mime_type = 'image/vnd.djvu'

    def __init__(self, file_path):
        super(DJVUHandler, self).__init__(file_path)
        self._pixel_format = djvu.decode.PixelFormatRgb()
        self._pixel_format.rows_top_to_bottom = True
        self._pixel_format.y_top_to_bottom = True  
        self._context = djvu.decode.Context()
        self._document = self._context.new_document(djvu.decode.FileUri(self._file_path))
        self._page_job = self._document.pages[0].decode(wait=True)

    def get_metadata(self):
        return ''

    def get_thumbnail(self, width, height):
        data = self._page_job.render(
            djvu.decode.RENDER_COLOR,
            (0, 0, self._page_job.width, self._page_job.height),
            (0, 0, self._page_job.width, self._page_job.height),
            self._pixel_format)
        page_size = (self._page_job.width, self._page_job.height)
        thumbnail_size = (width, height)
        image = PIL.Image.fromstring('RGB', page_size, data)
        image.thumbnail(thumbnail_size, PIL.Image.ANTIALIAS)
        file = cStringIO.StringIO()
        image.save(file, 'PNG')
        thumbnail = file.getvalue()
        file.close()
        return thumbnail

    def get_content(self):
        args = ['djvutxt', self._file_path]
        output = codecs.EncodedFile(os.tmpfile(), 'utf8', errors='ignore')
        return_code = subprocess.call(args=args, stdout=output)
        content = ''
        if return_code == 0:
            output.seek(0)
            content = output.read()
            output.close()
        return content.strip()

    def close(self):
        self._pixel_format = None
        self._context = None
        self._document = None
        self._page_job = None


class PSHandler(FileHandler):

    mime_type = 'application/postscript'

    def __init__(self, file_path):
        super(PSHandler, self).__init__(file_path)

    def get_metadata(self):
        return ''

    def get_thumbnail(self, width, height):
        args = ['convert', '%s[0]' % self._file_path,
                '-thumbnail', '%sx%s' % (width, height), 'png:-']
        output = os.tmpfile()
        return_code = subprocess.call(args=args, stdout=output)
        thumbnail = ''
        if return_code == 0:
            output.seek(0)
            thumbnail = output.read()
            output.close()
        return thumbnail

    def get_content(self):
        args = ['ps2txt', self._file_path]
        output = codecs.EncodedFile(os.tmpfile(), 'utf8', errors='ignore')
        return_code = subprocess.call(args=args, stdout=output)
        content = ''
        if return_code == 0:
            output.seek(0)
            content = output.read()
            output.close()
        return content.strip()
    
    def close(self):
        pass


_HANDLERS = dict([(handler.mime_type, handler)
                  for handler in FileHandler.__subclasses__()])

# Detect the MIME type of the file and return the appropriate handler.
def get_handler(file_path, mime_type):
    handler_class = _HANDLERS.get(mime_type, None)
    return None if handler_class is None else handler_class(file_path)


# Executing the module as a script for debugging proposes.
if __name__ == '__main__':
    file_path = os.path.abspath(sys.argv[1])
    magic_cookie = magic.open(magic.MAGIC_MIME_TYPE | magic.MAGIC_NO_CHECK_TOKENS)
    magic_cookie.load()
    mime_type = magic_cookie.file(file_path)
    handler = get_handler(file_path, mime_type)
    with codecs.open('mime_type.txt', encoding='utf8', mode='wt') as file:
        file.write(handler.mime_type)
    metadata = handler.get_metadata()
    if metadata:
        with codecs.open('metadata.txt', encoding='utf8', mode='wt') as file:
            file.write(metadata)
    thumbnail = handler.get_thumbnail(512, 512)
    if thumbnail:
        with open('thumbnail.png', mode='wb') as file:
            file.write(thumbnail)
    content = handler.get_content()
    if content:
        with codecs.open('content.txt', encoding='utf8', mode='wt') as file:
            file.write(content)
    handler.close()
