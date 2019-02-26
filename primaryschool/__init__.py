# -*- coding: utf-8 -*-
from .routes import primaryschool_bp

def init_app(app):
    app.register_blueprint(primaryschool_bp, url_prefix="/school")
