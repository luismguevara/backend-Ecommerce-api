from flask import Flask, jsonify, request, abort
import os
from Modelos import db, Producto, Usuario, Carrito, ItemCarrito, Chat, MensajesChat, Factura, Pagos
from dotenv import load_dotenv
import datetime
from datetime import datetime as date
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from endpoints.usuario import usuarios_bp
from endpoints.productos import producto_bp
from endpoints.chats import chats_bp
from endpoints.facturas import factura_bp
from endpoints.carrito import carrito_bp
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

@app.route('/login', methods = ['POST'])
def login():
    id = request.json.get('id', None)
    password = request.json.get('password', None)

    user = Usuario.query.filter_by(id = id).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id, expires_delta=datetime.timedelta(hours=24))
        return jsonify(access_token=access_token), 200

    return jsonify({'mensaje': "Mal id o contraseña"}), 401


app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
app.register_blueprint(producto_bp, url_prefix='/productos')
app.register_blueprint(factura_bp, url_prefix='/facturas')
app.register_blueprint(chats_bp, url_prefix='/chats')
app.register_blueprint(carrito_bp, url_prefix='/cart')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, 
    debug=True)
