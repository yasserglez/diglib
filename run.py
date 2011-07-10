#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import diglib


if __name__ == '__main__':
    # TODO: Parse command line arguments.
    library_dir = os.path.expanduser('~/.diglib/')
    diglib.main(library_dir)
