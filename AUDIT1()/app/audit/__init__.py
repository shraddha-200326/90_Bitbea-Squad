from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from .routes import audit_bp
    app.register_blueprint(audit_bp)

    return app
