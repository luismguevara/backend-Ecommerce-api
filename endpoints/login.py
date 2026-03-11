from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from models import Usuario
import datetime 
from datetime import datetime as date

login_bp = Blueprint('login_bp', __name__)

@login_bp.route('', methods = ['POST'])
def login():
    id = request.json.get('id', None)
    password = request.json.get('password', None)

    user = Usuario.query.filter_by(id = id).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(hours=24))
        return jsonify(access_token=access_token), 200

    return jsonify({'mensaje': "Mal id o contraseña"}), 401