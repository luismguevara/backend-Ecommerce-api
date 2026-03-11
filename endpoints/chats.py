from flask import Flask, jsonify, request, abort, Blueprint
from Modelos import db, Usuario, MensajesChat, Chat, UsuarioChat, Factura
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import timedelta, datetime as date
chats_bp = Blueprint('chats_bp', __name__)

@chats_bp.route('/<int:usuario_id>', methods=['GET'])
def obtener_chats(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)

        if usuario:
            return jsonify(usuario.serialize_with_chats()), 200

        else:
            abort(404, description="Usuario no encontrado")
    except Exception as e:
        print(e)
        abort(500, description="Error interno de servidor")

@chats_bp.route('/msg/<int:chat_id>', methods = ['POST'])
def enviar_mensaje(chat_id):

    datos = request.get_json()
    
    if not datos:
        return jsonify({'message': 'No datos recibidos'}), 400
    print(f"Datos recibidos aqui: {datos}")

    if not all(key in datos for key in ('id_usuario', 'mensaje')):
        print("Datos incompletos o malformados")
        return jsonify({'message': 'Datos incompletos'}), 400

    try:
        id_usuario = int(datos['id_usuario'])
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['id_usuario']}, Type: {type(datos['id_usuario'])}")  # Puedo Añadir un log de error con más detalles.
        return jsonify({'message': 'id_usuario formato incorrecto'}), 400

    mensaje = datos.get('mensaje')
    if not (isinstance(mensaje, str) and len(mensaje) > 0):
            return jsonify({'message': 'mensaje invalido o no puede estar vacio'}), 400

    nuevo_mensaje = MensajesChat()
    nuevo_mensaje.id_chat = chat_id
    nuevo_mensaje.mensaje = mensaje
    nuevo_mensaje.id_usuario = id_usuario

    try:
        db.session.add(nuevo_mensaje)
        db.session.commit()
        return jsonify({'message': 'Mensaje enviado correctamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al enviar el mensaje'}), 405

@chats_bp.route('/addusuario/<int:id_chat>', methods=['POST'])
@jwt_required()
def agregar_usuario_a_chat(id_chat):
    datos = request.get_json()
    id_usuario = datos.get('id_usuario')

    if not id_usuario:
        return jsonify({'message': 'Falta el id del usuario', 'success': False}), 400

    # Buscar el chat y el usuario
    chat = Chat.query.get(id_chat)
    usuario = Usuario.query.get(id_usuario)

    if not chat or not usuario:
        return jsonify({'message': 'Chat o usuario no encontrado', 'success': False}), 404

    # Verificar si el usuario ya está en el chat
    usuario_chat_existente = UsuarioChat.query.filter_by(usuario_id=id_usuario, chat_id=id_chat).first()
    if usuario_chat_existente:
        return jsonify({'message': 'El usuario ya está en el chat', 'success': True}), 200

    # Agregar el usuario al chat
    nuevo_usuario_chat = UsuarioChat(usuario_id=id_usuario, chat_id=id_chat)
    db.session.add(nuevo_usuario_chat)
    db.session.commit()

    return jsonify({'message': 'Usuario agregado al chat con éxito', 'success': True}), 200

@chats_bp.route('/delete/<int:id_chat>', methods=['DELETE'])
@jwt_required()
def eliminar_chat(id_chat):
    try:
        chat = Chat.query.get(id_chat)
        if not chat:
            return jsonify({'message': 'Chat no encontrado', 'success': True}), 208
        
        if chat.factura != 0:
            factura = Factura.query.get(chat.factura)
            if factura and factura.completado == 0:
                return jsonify({'message': 'La factura asociada al chat aun esta activa'}), 206
        
        # # Elimina todos los mensajes asociados al chat
        # MensajesChat.query.filter_by(id_chat=id_chat).delete()
        
        # # Elimina todas las asociaciones de usuario con el chat
        # UsuarioChat.query.filter_by(chat_id=id_chat).delete()
        
        # Elimina el chat
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({'message': 'Chat y todos los datos asociados eliminados con éxito', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al eliminar el chat', 'error': str(e), 'success': False}), 500
    
@chats_bp.route('/nuevo', methods=['POST'])
@jwt_required()
def crear_nuevo_chat():
    try:

        id_usuario = get_jwt_identity()

        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return jsonify({'message': 'Usuario no encontrado'}), 218

        # Crear un nuevo chat
        nuevo_chat = Chat(
            cliente=usuario.nombre, 
            motivo="Asesoria", 
            factura=0, 
            creado_en=date.now()
        )
        db.session.add(nuevo_chat)
        db.session.flush()

        usuarios_a_agregar = [id_usuario]
        usuarios_admin_ventas_tecnico = Usuario.query.filter(Usuario.role.in_([3, 5])).all()

        for usuario in usuarios_admin_ventas_tecnico:
            usuarios_a_agregar.append(usuario.id)

        #Agregar usuarios a chat
        for usuario_id in set(usuarios_a_agregar):  # Uso set para eliminar duplicados
            nuevo_usuario_chat = UsuarioChat(
                usuario_id=usuario_id, 
                chat_id=nuevo_chat.id_chat)
            db.session.add(nuevo_usuario_chat)

        #Mensajes predeterminados en chat
        mensajes_predeterminados = [
            "Buen día! Gracias por comunicarte con el departamento de asesoria tecnica",
            "Como podemos ayudarle?"
            ]

        #Crear y agregar cada mensaje
        for texto in mensajes_predeterminados:
            mensaje = MensajesChat(
                    id_chat=nuevo_chat.id_chat,
                    id_usuario=0,  
                    enviado_en=date.now(),
                    mensaje= texto
            )
            db.session.add(mensaje)


        db.session.commit()
        return jsonify({'message': 'Chat creado con éxito', 'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al crear el chat', 'error': str(e)}), 500