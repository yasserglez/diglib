# -*- coding: utf-8 -*-

import os


def get_icon(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon', name)

def get_glade(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glade', name)
