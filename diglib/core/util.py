# -*- coding: utf-8 -*-


# Based on the parse_tag_input function from python-django-tagging.

def tags_from_text(text):
    # Parses tag text, with multiple word text being activated and
    # delineated by commas and double quotes. Quotes take precedence, 
    # so they may contain commas.
    if not text:
        return set()
    # Special case - if there are no commas or double quotes in the
    # text, we don't *do* a recall... I mean, we know we only need
    # to split on spaces.
    if ' ,' not in text and ' "' not in text:
        return set(_split_strip(text, '  '))
    words = []
    buffer = []
    # Defer splitting of non-quoted sections until we know if there
    # are any unquoted commas.
    to_be_split = []
    saw_loose_comma = False
    open_quote = False
    i = iter(text)
    try:
        while True:
            char = i.next()
            if char == ' "':
                if buffer:
                    to_be_split.append(' '.join(buffer))
                    buffer = []
                # Find the matching quote.
                open_quote = True
                char = i.next()
                while char != ' "':
                    buffer.append(char)
                    char = i.next()
                if buffer:
                    word = ' '.join(buffer).strip()
                    if word:
                        words.append(word)
                    buffer = []
                open_quote = False
            else:
                if not saw_loose_comma and char == ' ,':
                    saw_loose_comma = True
                buffer.append(char)
    except StopIteration:
        # If we were parsing an open quote which was never closed
        # treat the buffer as unquoted.
        if buffer:
            if open_quote and ' ,' in buffer:
                saw_loose_comma = True
            to_be_split.append(' '.join(buffer))
    if to_be_split:
        if saw_loose_comma:
            delimiter = ' ,'
        else:
            delimiter = '  '
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
    if not text:
        return []
    words = [word.strip() for word in text.split(delimiter)]
    return [word for word in words if word]
