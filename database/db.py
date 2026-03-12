import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def configure_database(app):
    
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
   
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}?"
        f"ssl_ca=./Key/ca-cert.pem&"
        f"ssl_cert=./Key/server-cert.pem&"
        f"ssl_key=./Key/server-key.pem"
        )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)