# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import codecs
import cStringIO

import cairo
import poppler


# File handlers used to extract information from the different document formats
# supported by the library. Each handler is identified by the MIME type of the
# format it handles.
class FileHandler(object):

    mime_type = None
    
    @property
    def file_path(self):
        return self._file_path

    def __init__(self, file_path):
        self._file_path = file_path
        
    # Return an in-memory file object with the metadata of the file in UTF-8
    # encoded plain text. If no metadata is available it should return None.
    # The file should be closed by the caller.
    def get_metadata(self):
        raise NotImplementedError()

    # Return an in-memory file object with a thumbnail for the document in PNG
    # format. The thumbnails should not exceed the given width and height.
    # The file should be closed by the caller.
    def get_thumbnail(self, width, height):
        raise NotImplementedError()

    # Return an in-memory file object with the content of the file in UTF-8
    # encoded plain text. If no metadata is available it should return None.
    # The file should be closed by the caller.
    def get_content(self):
        raise NotImplementedError()

    # Close opened resources. The default implementation does nothing.
    # Operations after this method is called should be considered errors.
    def close(self):
        raise NotImplementedError()


class PlainTextHandler(FileHandler):
    
    mime_type = 'text/plain'
    
    def __init__(self, file_path):
        super(PlainTextHandler, self).__init__(file_path)
        self._file = codecs.open(file_path, encoding='utf8', errors='ignore')

    def get_metadata(self):
        return None

    def get_thumbnail(self, width, height):
        return None

    def get_content(self):
        self._file.seek(0)
        content = cStringIO.StringIO()
        shutil.copyfileobj(self._file, content)
        content.seek(0)
        return content

    def close(self):
        self._file.close()


class PDFHandler(FileHandler):
    
    mime_type = 'application/pdf'

    def __init__(self, file_path):
        super(PDFHandler, self).__init__(file_path)
        self._document = \
          poppler.document_new_from_file('file://' + file_path, None)

    def get_metadata(self):
        metadata = None
        for name in ('title', 'keywords'):
            value = self._document.get_property(name)
            if value:
                if metadata is None:
                    metadata = cStringIO.StringIO()
                metadata.write(value.encode('utf8') + ' ')
        if metadata is not None:
            metadata.seek(0)
        return metadata

    def get_thumbnail(self, width, height):
        thumbnail = None
        if self._document.get_n_pages() > 0:
            page = self._document.get_page(0)
            page_width, page_height = page.get_size() 
            if page_width > page_height:
                scale = width / page_width
            else:
                scale = height / page_height
            image_width = int(scale * page_width)
            image_height = int(scale * page_height)
            surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 
                                         image_width, image_height)
            context = cairo.Context(surface)
            context.scale(scale, scale)
            context.set_source_rgb(1.0, 1.0, 1.0)
            context.rectangle(0.0, 0.0, page_width, page_height)
            context.fill()
            page.render(context)
            thumbnail = cStringIO.StringIO()
            surface.write_to_png(thumbnail)
            thumbnail.seek(0)
        return thumbnail

    def get_content(self):
        content = None
        args = ['/usr/bin/pdftotext', self._file_path, '-']
        output = codecs.EncodedFile(os.tmpfile(), 'utf8', errors='ignore')
        return_code = subprocess.call(args=args, stdout=output)
        if return_code == 0:
            output.seek(0)
            content = cStringIO.StringIO()
            shutil.copyfileobj(output, content)
            output.close()
            content.seek(0)
        return content

    def close(self):
        pass


_HANDLERS = dict([(h.mime_type, h) for h in FileHandler.__subclasses__()])

# Detect the MIME type of the file and return the appropiate handler.
def get_handler(file_path, mime_type):
    handler_class = _HANDLERS.get(mime_type, None)
    return None if handler_class is None else handler_class(file_path)


# Executing the module as a script for debugging proposes.
if __name__ == '__main__':
    file_path = os.path.abspath(sys.argv[1])
    handler = get_handler(file_path, 'application/pdf')
    with codecs.open('mime_type.txt', encoding='utf8', mode='wt') as file:
        file.write(handler.mime_type)
    metadata = handler.get_metadata()
    if metadata:
        with codecs.open('metadata.txt', encoding='utf8', mode='wt') as file:
            file.write(metadata.getvalue())
    thumbnail = handler.get_thumbnail(256, 256)
    if thumbnail:
        with open('thumbnail.png', mode='wb') as file:
            shutil.copyfileobj(thumbnail, file)
    content = handler.get_content()
    if content:
        with codecs.open('content.txt', encoding='utf8', mode='wt') as file:
            file.write(content.getvalue())
    handler.close()
