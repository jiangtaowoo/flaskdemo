# -*- coding: utf-8 -*-

"""
vocabulary.api
"""

from . import transessions

def session():
    return transessions.ENTranslation()

def translate(format_type, word):
    """Constructs and sends a translation request
    :param word: word to be translated.

    Usage::
      >>> import vocabulary
      >>> res = vocabulary.translate('immature')
      <Response json>
    """
    with transessions.ENTranslation() as session:
        return session.translate(format_type, word)

def query(format_type, pattern):
    """Constructs and sends a vocabulary query
    :param pattern: could be a word (eg. immature) or pattern (eg. con*)

    Usage::
      >>> import vocabulary
      >>> res = vocabulary.query('immature')
      >>> res = vocabulary.query('con*')
      <Response html string>
    """
    with transessions.ENTranslation() as session:
        return session.query(format_type, pattern)
