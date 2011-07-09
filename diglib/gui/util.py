# -*- coding: utf-8 -*-

import os
import subprocess


def open_file(file_path):
    subprocess.Popen(['xdg-open', file_path])

def open_url(url):
    subprocess.Popen(['xdg-open', url])

def open_email(email):
    subprocess.Popen(['xdg-email', email])

def get_image(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', name)

def get_glade(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
