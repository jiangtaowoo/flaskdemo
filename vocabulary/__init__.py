# -*- coding: utf-8 -*-
from .routes import vocabulary_bp

def init_app(app):
    app.register_blueprint(vocabulary_bp, url_prefix="/vocabulary")
