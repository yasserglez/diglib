# -*- coding: utf-8 -*-

import os

import gtk


class XMLWidget(object):

    def __init__(self, widget_name):
        glade_file = os.path.join(os.path.dirname(__file__), 
                                  '%s.glade' % widget_name.replace('_', ''))
        self._builder = gtk.Builder()
        self._builder.add_from_file(glade_file)
        self._widget = self._builder.get_object(widget_name)
        self._builder.connect_signals(self)

    def __getattr__(self, name):
        return getattr(self._widget, name)
