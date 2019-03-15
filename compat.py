# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function, unicode_literals)
import sys

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

if is_py2:
    def is_str_or_unicode(inputs):
        return isinstance(inputs, str) or isinstance(inputs, unicode)

    def is_unicode(inputs):
        return isinstance(inputs, unicode)

    def py23_2_unicode(v):
        if isinstance(v, str):
            return v.decode("utf-8")
        elif isinstance(v, unicode):
            return v
        else:
            return unicode(v)
elif is_py3:
    def is_str_or_unicode(inputs):
        return isinstance(inputs, str)

    def is_unicode(inputs):
        return isinstance(inputs, str)

    def py23_2_unicode(v):
        if isinstance(v, bytes):
            return v.decode("utf-8")
        elif isinstance(v, str):
            return v
        else:
            return str(v)