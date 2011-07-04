# -*- coding: utf-8 -*-

import subprocess


def open_file(file_path):
    subprocess.Popen(['xdg-open', file_path])

def open_url(url):
    subprocess.Popen(['xdg-open', url])

def open_email(email):
    subprocess.Popen(['xdg-email', email])
