# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
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

# Based on the parse_tag_input function from python-django-tagging.

def tags_from_text(text):
    # Parses tag text, with multiple word text being activated and
    # delineated by commas and double quotes. Quotes take precedence, 
    # so they may contain commas.
    if not text:
        return set()
    # If there are no commas or double quotes in the input,
    # we only need to split on spaces.
    if ',' not in text and '"' not in text:
        words = _split_strip(text, ' ')
        return set(words)
    words, buffer = [], []
    # Defer splitting of non-quoted sections until we know 
    # if there are any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(text)
    try:
        while True:
            c = i.next()
            if c == '"':
                if buffer:
                    to_be_split.append(''.join(buffer))
                    buffer = []
                # Find the matching quote.
                open_quote = True
                c = i.next()
                while c != '"':
                    buffer.append(c)
                    c = i.next()
                if buffer:
                    word = ''.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and c == ',':
                    saw_loose_comma = True
                buffer.append(c)
    except StopIteration:
        # If we were parsing an open quote which was never closed 
        # treat the buffer as unquoted.
        if buffer:
            if open_quote and ',' in buffer:
                saw_loose_comma = True
            to_be_split.append(''.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = ','
        else:
            delimiter = ' '
        for chunk in to_be_split:
            words.extend(_split_strip(chunk, delimiter))
    return set(words)


# Based on the edit_string_for_tags function from python-django-tagging.

def text_from_tags(tags):
    # Given list of tags, creates a string representation of
    # the list suitable for editing by the user, such that submitting the
    # given string representation back without changing it will give the
    # same list of tags.
    #
    # Tag names which contain commas will be double quoted.
    #
    # If any tag which isn't being quoted contains whitespace, the
    # resulting string of tag names will be comma-delimited, otherwise
    # it will be space-delimited.
    names = []
    use_commas = False
    for tag in tags:
        if ',' in tag:
            names.append('"%s"' % tag)
            continue
        elif ' ' in tag:
            if not use_commas:
                use_commas = True
        names.append(tag)
    if use_commas:
        glue = ', '
    else:
        glue = ' '
    return glue.join(names)


# Function from python-django-tagging.

def _split_strip(text, delimiter=','):
    # Splits text on delimiter, stripping each resulting string
    # and returning a list of non-empty strings.
    words = []
    for word in text.split(delimiter):
        word = word.strip()
        if word:
            words.append(word)
    return words
