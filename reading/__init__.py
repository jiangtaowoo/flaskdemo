# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from .routes import reading_bp

def init_app(app):
    app.register_blueprint(reading_bp, url_prefix="/reading")
