# -*- coding: utf-8 -*-

"""
vocabulary.api
"""

from . import transessions

def session():
    return transessions.BDTranslation()

def translate(word):
    """Constructs and sends a translation request
    :param word: word to be translated.

    Usage::
      >>> import vocabulary
      >>> res = vocabulary.translate('immature')
      <Response json>
    """
    with transessions.BDTranslation() as session:
        return session.translate(word)

def query(pattern):
    """Constructs and sends a vocabulary query
    :param pattern: could be a word (eg. immature) or pattern (eg. con*)

    Usage::
      >>> import vocabulary
      >>> res = vocabulary.query('immature')
      >>> res = vocabulary.query('con*')
      <Response html string>
    """
    with transessions.BDTranslation() as session:
        return session.query(pattern)
