from flask import Flask, jsonify, request, abort
import os
from models import db
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from endpoints.usuario import usuarios_bp
from endpoints.productos import producto_bp
from endpoints.chats import chats_bp
from endpoints.facturas import factura_bp
from endpoints.carrito import carrito_bp
from endpoints.login import login_bp

app = Flask(__name__)
load_dotenv()

# Configuración segura: variables de entorno
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')
key = os.environ.get('key')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}?"
    f"ssl_ca=./Key/ca-cert.pem&"
    f"ssl_cert=./Key/server-cert.pem&"
    f"ssl_key=./Key/server-key.pem"
    )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = key
db.init_app(app)
jwt = JWTManager(app)

app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
app.register_blueprint(producto_bp, url_prefix='/productos')
app.register_blueprint(factura_bp, url_prefix='/facturas')
app.register_blueprint(chats_bp, url_prefix='/chats')
app.register_blueprint(carrito_bp, url_prefix='/cart')
app.register_blueprint(login_bp, url_prefix='/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, 
    debug=True)
