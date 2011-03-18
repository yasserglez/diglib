# -*- coding: utf-8 -*-

from django.conf import settings


if not hasattr(settings, 'DIGLIB_STORAGE'):
    from diglib.core.storage import Storage
    from diglib.wrappers import DjangoDatabase, XapianIndex

    settings.DIGLIB_STORAGE = \
        Storage(index=XapianIndex(settings.DIGLIB_INDEX_DIR),
                 database=DjangoDatabase(),                  
                 documents_dir=settings.DIGLIB_DOCUMENTS_DIR,
                 thumbnails_dir=settings.DIGLIB_THUMBNAILS_DIR,
                 thumbnail_width=settings.DIGLIB_THUMBNAILS_WIDTH, 
                 thumbnail_height=settings.DIGLIB_THUMBNAILS_HEIGHT)
