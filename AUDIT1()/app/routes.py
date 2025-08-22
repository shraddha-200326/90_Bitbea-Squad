from flask import Blueprint

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    return "✅ Flask Audit Tool is running!"
