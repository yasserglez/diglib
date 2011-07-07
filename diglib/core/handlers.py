# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import codecs
import cStringIO

import cairo
import poppler
import magic


# File handlers used to extract information from the different document formats
# supported by the library. Each handler is identified by the MIME type of the
# format it handles.
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
        pass


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
        file = cStringIO.StringIO()
        shutil.copyfileobj(self._file, file)
        data = file.getvalue()
        file.close()
        return data

    def close(self):
        self._file.close()


class PDFHandler(FileHandler):
    
    mime_type = 'application/pdf'

    def __init__(self, file_path):
        super(PDFHandler, self).__init__(file_path)
        self._document = \
            poppler.document_new_from_file('file://' + file_path, None)

    def get_metadata(self):
        file = None
        for name in ('title', 'keywords'):
            value = self._document.get_property(name)
            if value:
                if file is None:
                    file = cStringIO.StringIO()
                file.write(value.encode('utf8') + ' ')
        if file:
            metadata = file.getvalue()
            file.close()
            return metadata
        else:
            return ''

    def get_thumbnail(self, width, height):
        file = None
        if self._document.get_n_pages() > 0:
            page = self._document.get_page(0)
            page_width, page_height = page.get_size() 
            if page_width > page_height:
                scale = width / page_width
            else:
                scale = height / page_height
            image_width = int(scale * page_width)
            image_height = int(scale * page_height)
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, image_width, image_height)
            context = cairo.Context(surface)
            context.scale(scale, scale)
            context.set_source_rgb(1.0, 1.0, 1.0)
            context.rectangle(0.0, 0.0, page_width, page_height)
            context.fill()
            page.render(context)
            file = cStringIO.StringIO()
            surface.write_to_png(file)
        if file:
            thumbnail = file.getvalue()
            file.close()
            return thumbnail
        else:
            return ''

    def get_content(self):
        file = None
        args = ['/usr/bin/pdftotext', self._file_path, '-']
        output = codecs.EncodedFile(os.tmpfile(), 'utf8', errors='ignore')
        return_code = subprocess.call(args=args, stdout=output)
        if return_code == 0:
            output.seek(0)
            file = cStringIO.StringIO()
            shutil.copyfileobj(output, file)
            output.close()
        if file:
            content = file.getvalue()
            file.close()
            return content
        else:
            return ''


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
    file = handler.get_metadata()
    if file:
        with codecs.open('file.txt', encoding='utf8', mode='wt') as file:
            file.write(file.getvalue())
    file = handler.get_thumbnail(256, 256)
    if file:
        with open('file.png', mode='wb') as file:
            shutil.copyfileobj(file, file)
    file = handler.get_content()
    if file:
        with codecs.open('file.txt', encoding='utf8', mode='wt') as file:
            file.write(file.getvalue())
    handler.close()
