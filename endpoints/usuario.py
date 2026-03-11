from flask import Blueprint, jsonify, abort, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Usuario, PreguntaSeguridad
from werkzeug.security import generate_password_hash, check_password_hash

usuarios_bp = Blueprint('usuarios_bp', __name__)


@usuarios_bp.route('/admin', methods=['GET'])
@jwt_required()
def lista_usuarios():
    try:
        identity = get_jwt_identity()
        usuario_activo = Usuario.query.get(identity)

        if usuario_activo and usuario_activo.role == 5:
            usuarios = Usuario.query.all()
            return jsonify([usuario.serialize() for usuario in usuarios]), 200
        else:
            return jsonify({'mensaje': 'Acceso no autoriazado'}), 400
    except Exception as e:
        print(e)
        abort(500, description = "Error interno de servidor")


@usuarios_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def obtener_usuario(id):
    print(f"ID recibidio: {id}, tipo: {type(id)}")
    try:

        identity = get_jwt_identity()
        print(f"identity: {identity}, de tipo {type(identity)}")
        identity_id = int(identity)
        if identity != id:
            return jsonify({"mesage": "Acceso no autorizado"}), 403

        usuario = Usuario.query.get(id)
        if usuario:
            return jsonify(usuario.serialize()), 200
        else:
            abort(404, description="Usuario no encontrado")
    except Exception as e:
        print(e)
        abort(500, description="Error interno de servidor")

@usuarios_bp.route('/add', methods =['POST'])
def agregar_usuario():

    datos = request.get_json()

    if not datos:
        return jsonify({'message': 'No datos recibidos'}), 400
    
    print(datos)

    if not all(key in datos for key in ('id', 'nombre', 'password')):
        return jsonify({'message': 'Datos incompletos'}), 400
    
    try:
        id = int(datos['id'])
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['id']}, Type: {type(datos['id'])}")  
        return jsonify({'message': 'id no valido'}), 400
    
    nombre = datos.get('nombre')
    apellido = datos.get('apellido')

    password_raw = datos.get('password')
    password_hash = generate_password_hash(password_raw, method='pbkdf2:sha256')

    direccion = datos.get('direccion')
    telefono = datos.get('telefono')

    print(f"Nombre recibidio: {nombre}, tipo: {type(nombre)}")
    print(f"password raw recibidio: {password_raw}, tipo: {type(password_raw)}")
    print(f"password has recibidio: {password_hash}, tipo: {type(password_hash)}")
    print(f"direccion recibidio: {direccion}, tipo: {type(direccion)}")
    print(f"id recibidio: {id}, tipo: {type(id)}")
    print(f"Apellido recibidio: {apellido}, tipo: {type(apellido)}")
    print(f"telefono recibidio: {telefono}, tipo: {type(telefono)}")

    nuevo_usuario = Usuario(
        id = id,
        nombre = nombre,
        apellido = apellido,
        password = password_hash,
        direccion = direccion,
        telefono = telefono,
        role = 1,
    )

    try:
        db.session.add(nuevo_usuario)
        db.session.commit()
        return jsonify({'message': 'Usuario registrado correctamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al registrar usuario'}), 405

@usuarios_bp.route('/edit/<int:id>', methods = ['POST'])
@jwt_required()
def editar_usuario(id):
    current_user_id = get_jwt_identity()
    if current_user_id != id:
        return jsonify({'message': 'Acceso no autorizado'}), 200
    
    datos = request.get_json()
    usuario = Usuario.query.get_or_404(id)

    nombre = datos.get('nombre')
    apellido = datos.get('apellido')
    telefono = datos.get('telefono')
    direccion = datos.get('direccion')
    password_actual = datos.get('password')
    nueva_password = datos.get('newpassword')

    try:
        if nombre:
            usuario.nombre = nombre
        
        if apellido:
            usuario.apellido = apellido
        
        if telefono:
            usuario.telefono = telefono
        
        if direccion:
            usuario.direccion = direccion
        
        if password_actual and nueva_password:
            if usuario.check_password(password_actual):
                usuario.password = generate_password_hash(nueva_password, method='pbkdf2:sha256')
            else:
                return jsonify({'message': 'Contraseña actual incorrecta', 'success': False}), 401
        
        db.session.commit()
        return jsonify({'message': 'Perfil actualizado exitosamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar el perfil', 'error': str(e), 'success': False}), 500

@usuarios_bp.route('/pregunta/<int:id>', methods=['POST'])
# @jwt_required()
def establecer_pregunta_seguridad(id):
    datos = request.get_json()
    pregunta = datos.get('pregunta')
    respuesta = datos.get('respuesta')

    if not pregunta or not respuesta:
        return jsonify({'message': 'Pregunta y respuesta son requeridas'}), 400

    try:
        usuario = Usuario.query.get_or_404(id)
        pregunta_seguridad = PreguntaSeguridad.query.filter_by(id_usuario=id).first()
        if not pregunta_seguridad:
            pregunta_seguridad = PreguntaSeguridad(id_usuario=id)
            db.session.add(pregunta_seguridad)
        
        pregunta_seguridad.pregunta = pregunta
        pregunta_seguridad.set_respuesta(respuesta)
        
        db.session.commit()
        return jsonify({'message': 'Pregunta de seguridad guardada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'message': 'Error al guardar la pregunta de seguridad'}), 500


@usuarios_bp.route('/recuperar/<int:id>', methods=['GET'])
def obtener_pregunta_seguridad(id):
    pregunta_seguridad = PreguntaSeguridad.query.filter_by(id_usuario=id).first()
    if pregunta_seguridad:
        return jsonify({'message': pregunta_seguridad.pregunta, 'success': True}), 200
    else:
        return jsonify({'message': 'Pregunta de seguridad no encontrada'}), 404


@usuarios_bp.route('/recuperar/<int:id>', methods=['POST'])
def cambiar_contrasena(id):
    datos = request.get_json()
    respuesta = datos.get('respuesta')
    nueva_contrasena = datos.get('newpassword')

    if not respuesta or not nueva_contrasena:
        return jsonify({'message': 'Respuesta y nueva contraseña son requeridas'}), 400

    pregunta_seguridad = PreguntaSeguridad.query.filter_by(id_usuario=id).first()
    if pregunta_seguridad and pregunta_seguridad.check_respuesta(respuesta):
        usuario = Usuario.query.get_or_404(id)
        usuario.password = generate_password_hash(nueva_contrasena, method='pbkdf2:sha256')
        db.session.commit()
        return jsonify({'message': 'Password actualizado exitosamente', 'success': True}), 200
    else:
        return jsonify({'message': 'Respuesta de seguridad incorrecta', 'success': False}), 401

@usuarios_bp.route('/admin/permisos/<int:id_usuario>', methods=['PUT'])
@jwt_required()
def cambiar_permisos_usuario(id_usuario):
    
    identidad_actual = get_jwt_identity()
    usuario_actual = Usuario.query.get(identidad_actual)

    # Verificar si el usuario actual es un administrador
    if usuario_actual.role != 5:
        return jsonify({'message': 'Acceso no autorizado'}), 403

    datos = request.get_json()
    nuevo_role = datos.get('nuevo_role')
    if nuevo_role is None:
        return jsonify({'message': 'Datos incompletos'}), 400
    
    usuario_a_modificar = Usuario.query.get(id_usuario)
    if not usuario_a_modificar:
        return jsonify({'message': 'Usuario no encontrado'}), 404

    try:
        usuario_a_modificar.role = nuevo_role
        db.session.commit()
        return jsonify({'message': 'Role actualizado exitosamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar el role', 'error': str(e)}), 500