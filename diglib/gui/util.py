# -*- coding: utf-8 -*-

import os


def get_image(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', name)

def get_glade(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
