# -*- coding: utf-8 -*-

# Language detection based on the guess_language PyPi package
# by Kent Johnson (http://code.google.com/p/guess-language).

import os
import re
import sys
import unicodedata
import collections
import bisect
import codecs


SUPPORTED_LANGS = ('en', 'es', 'it', 'fr', 'de')


def get_lang(text):
    if isinstance(text, str):
        text = unicode(text, 'utf-8')
    text = _normalize(text)
    return _check(text, _MODELS.keys())


def get_stopwords(lang):
    return _STOPWORDS[lang]


def _load_stopwords():
    stopwords = {}
    stopwords_dir = os.path.join(os.path.dirname(__file__), 'stopwords')
    for stopword_file in os.listdir(stopwords_dir):
        stopword_path = os.path.join(stopwords_dir, stopword_file)
        if os.path.isfile(stopword_path):
            with codecs.open(stopword_path, encoding='utf8', mode='r') as file:
                stopword = []
                for line in file:
                    stopword.append(line.strip())
            stopwords[stopword_file.lower()] = stopword
    return stopwords

_STOPWORDS = _load_stopwords()


def _load_blocks():
    # Create two parallel lists. One has the start and end points for
    # codepoint ranges, the second has the corresponding block name.
    blocks_path = os.path.join(os.path.dirname(__file__), 'blocks.txt')
    endpoints, names = [], []
    splitter = re.compile(r'^(....)\.\.(....); (.*)$')
    with codecs.open(blocks_path, encoding='utf8', mode='r') as file:
        for line in file:
            line = line.strip()
            if not line.startswith('#'):
                match = splitter.match(line)
                start = int(match.group(1), 16)
                end = int(match.group(2), 16)
                name = match.group(3)
                endpoints.append(start)
                endpoints.append(end)
                names.append(name)
                names.append(name)
    return endpoints, names

_BLOCK_ENDPOINTS, _BLOCK_NAMES = _load_blocks()

def _unicode_block(c):
    # Returns the name of the Unicode block containing the character.
    ix = bisect.bisect_left(_BLOCK_ENDPOINTS, ord(c))
    return _BLOCK_NAMES[ix]


def _make_nonalpha_re():
    nonalpha = [u'[^']
    for i in range(sys.maxunicode):
        c = unichr(i)
        if c.isalpha():
            nonalpha.append(c)
    nonalpha.append(u']')
    nonalpha = u''.join(nonalpha)
    return re.compile(nonalpha)

_NONALPHA_RE = _make_nonalpha_re()
_WHITESPACE_RE = re.compile('\s+', re.UNICODE)
_TRIGRAPH_RE = re.compile(r'(.{3})\s+(.*)')


def _load_models():
    models = {}
    models_dir = os.path.join(os.path.dirname(__file__), 'trigraphs')
    for model_file in os.listdir(models_dir):
        model_path = os.path.join(models_dir, model_file)
        if os.path.isfile(model_path):
            with codecs.open(model_path, encoding='utf8', mode='r') as file:
                model = {}
                for line in file:
                    match = _TRIGRAPH_RE.search(line)
                    if match:
                        model[match.group(1)] = int(match.group(2))
            models[model_file.lower()] = model
    return models

_MODELS = _load_models()


def _normalize(text):
    # Convert to normalized Unicode, remove non-alpha and compress spaces.
    text = unicodedata.normalize('NFC', text)
    text = _NONALPHA_RE.sub(' ', text)
    text = _WHITESPACE_RE.sub(' ', text)
    return text


def _find_runs(text):
    # Count the number of characters in each character block.
    run_types = collections.defaultdict(int)
    total_count = 0
    for c in text:
        if c.isalpha():
            block = _unicode_block(c)
            run_types[block] += 1
            total_count += 1
    # Return run types that used for 40% or more of the string.
    # Always return Basic Latin if found more than 15%.
    relevant_runs = []
    for key, value in run_types.items():
        pct = (value * 100) / total_count
        if pct >= 40:
            relevant_runs.append(key)
        elif key == 'Basic Latin' and pct >= 15:
            relevant_runs.append(key)
    return relevant_runs


def _ordered_model(text):
    # Create a list of trigrams in text sorted by frequency.
    trigrams = collections.defaultdict(int) 
    text = text.lower()
    for i in xrange(0, len(text)-2):
        trigrams[text[i:i+3]] += 1
    return sorted(trigrams.keys(), key=lambda k: (-trigrams[k], k))


def _distance(model, known_model):
    MAX_GRAMS = 300
    distance = 0
    for i, value in enumerate(model[:MAX_GRAMS]):
        if not re.search(r'\s\s', value, re.UNICODE):
            if value in known_model:
                distance += abs(i - known_model[value])
            else:
                distance += MAX_GRAMS
    return distance


def _check(text, langs):
    scores = []
    model = _ordered_model(text)
    for lang in langs:
        lower_lang = lang.lower()
        if lower_lang in _MODELS:
            scores.append((_distance(model, _MODELS[lower_lang]), lang))
    return min(scores)[1]


if __name__ == '__main__':
    file_path = os.path.abspath(sys.argv[1])
    with codecs.open(file_path, encoding='utf8', mode='r') as file:
        text = file.read()
    print get_lang(text)
