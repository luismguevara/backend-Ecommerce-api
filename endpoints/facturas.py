from flask import Flask, jsonify, request, abort, Blueprint
from Modelos import db, Usuario, Carrito, Factura, Pagos, ItemFactura, Chat, UsuarioChat, MensajesChat, Calificacion
from datetime import datetime as date
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

factura_bp = Blueprint('factura_bp', __name__)

@factura_bp.route('/nueva/<int:id_usuario>', methods=['POST'])
@jwt_required()
def crear_factura(id_usuario):

    datos = request.get_json()
    entrega = datos.get('entrega')
    usuario = Usuario.query.get_or_404(id_usuario)
    try:
        total = int(datos.get('total'))
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos.get('total')}, Type: {type(datos.get('total'))}")
        return jsonify({'message': 'total Invalido'}), 400
    print(f"Total recibidio: {total}, tipo: {type(total)}")
    
    if entrega is None or total is None:
        return jsonify({'message': 'Datos incompletos'}), 400
    
    try: #Crear nueva factura
        nueva_factura = Factura(
            id_usuario = id_usuario,
            creado_en = date.now(),
            entrega = entrega,
            total = total
        )
        db.session.add(nueva_factura)
        db.session.flush()
        print(nueva_factura.id_factura)
        carrito = Carrito.query.filter_by(id_usuario=id_usuario).first()
        if carrito:
            print(carrito)

            #Crear nuevos ItemFactura
            for item in carrito.items:
                print(item)
                item_factura = ItemFactura(
                    id_factura = nueva_factura.id_factura,
                    id_producto = item.id_producto,
                    cantidad = item.cantidad,
                    precio = item.producto.precio
                )
                print(item_factura)
                db.session.add(item_factura)
            
            for cotizacion in carrito.cotizaciones:
                print(cotizacion)
                item_factura = ItemFactura(
                    id_factura = nueva_factura.id_factura,
                    id_producto = cotizacion.id_producto,
                    cantidad = 1,
                    precio = cotizacion.precio
                )
                print(item_factura)
                db.session.add(item_factura)
            
            #Crear nuevo chat de compras
            nuevo_chat = Chat(
                cliente = usuario.nombre,
                motivo = "Compra",
                factura = nueva_factura.id_factura,
                creado_en = date.now()#date.utcoffset(),
            )
            db.session.add(nuevo_chat)
            db.session.flush()

            #OBtener lista de usuarios
            usuarios_a_agregar = [id_usuario]
            usuarios_admin_y_ventas = Usuario.query.filter(Usuario.role.in_([4, 5])).all()

            for usuario in usuarios_admin_y_ventas:
                usuarios_a_agregar.append(usuario.id)

            #Agregar usuarios a chat
            for usuario_id in set(usuarios_a_agregar):  # Uso set para eliminar duplicados
                nuevo_usuario_chat = UsuarioChat(
                    usuario_id=usuario_id, chat_id=nuevo_chat.id_chat)
                db.session.add(nuevo_usuario_chat)

            #Mensajes predeterminados en chat
            mensajes_predeterminados = [
                "Buen día! Gracias por comunicarte con el departamento de ventas",
                f"Compra de factura #{nueva_factura.id_factura}. Por un monto de {total} con {entrega}",
                "Por favor ingrese su referencia de pago"
            ]

            #Crear y agregar cada mensaje
            for texto in mensajes_predeterminados:
                mensaje = MensajesChat(
                    id_chat=nuevo_chat.id_chat,
                    id_usuario=0,  # Usuario 'sistema' o similar
                    enviado_en=date.now(),
                    mensaje= texto
                )
                db.session.add(mensaje)

            #Vaciar carrito
            for item in carrito.items:
                db.session.delete(item)

            for cotizacion in carrito.cotizaciones:
                db.session.delete(cotizacion)
            db.session.commit()
            
            return jsonify({'message': 'Factura creada con exito', 'success': True, 'id_factura': nueva_factura.id_factura}), 200
        else:
            return jsonify({'message': 'Carrito no encontrado para el usuario'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al crear la factura', 'error': str(e)}), 500


@factura_bp.route('/pagos/<int:id_factura>', methods = ['POST'])
@jwt_required()
def registrar_pago(id_factura):

    datos = request.get_json()
    
    if not datos:
        return jsonify({'message': 'No datos recibidos'}), 400
    print(f"Datos recibidos aqui: {datos}")

    if not all(key in datos for key in ('id_usuario', 'fecha', 'referencia')):
        print("Datos incompletos o malformados")
        return jsonify({'message': 'Datos incompletos'}), 400

    try:
        id_usuario = int(datos['id_usuario'])
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['id_usuario']}, Type: {type(datos['id_usuario'])}")  # Puedo Añadir un log de error con más detalles.
        return jsonify({'message': 'id_usuario formato incorrecto'}), 400

    fecha = datos.get('fecha')
    if not (isinstance(fecha, str) and len(fecha) > 0):
            return jsonify({'message': 'fecha invalida o no puede estar vacia'}), 400

    fecha_real = date.strptime(fecha, '%Y-%m-%d %H:%M:%S')

    try:
        referencia = int(datos['referencia'])
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['referencia']}, Type: {type(datos['referencia'])}")  # Puedo Añadir un log de error con más detalles.
        return jsonify({'message': 'referencia formato incorrecto'}), 400

    nuevo_pago = Pagos(
        referencia = referencia,
        fecha = fecha_real,
        id_usuario = id_usuario,
        id_factura = id_factura
    )
    try:
        db.session.add(nuevo_pago)
        db.session.commit()
        return jsonify({'message': 'Pago registrado con exito', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al registrar el pago', 'error': str(e)}), 405

@factura_bp.route('/review/<int:id_factura>', methods=['POST'])
@jwt_required()
def registrar_review(id_factura):

    datos = request.get_json()
    
    if not datos:
        return jsonify({'message': 'No se recibieron datos'}), 400

    if not all(key in datos for key in ('valor', 'mensaje')):
        return jsonify({'message': 'Datos incompletos o malformados'}), 400

    try:
        calificacion = int(datos['valor'])
        mensaje = str(datos['mensaje'])

        if not 0 < calificacion <= 5:
            raise ValueError("La calificación debe estar entre 1 y 5.")
    except ValueError as e:
        return jsonify({'message': 'Formato de datos incorrecto', 'error': str(e)}), 400

    nueva_calificacion = Calificacion(
        valor=calificacion,
        mensaje=mensaje,
        id_factura=id_factura
    )
    try:
        db.session.add(nueva_calificacion)
        db.session.commit()
        return jsonify({'message': 'Calificacion registrada con éxito', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al registrar la calificacion', 'error': str(e)}), 500

@factura_bp.route('/<int:usuario_id>', methods=['GET'])
def obtener_factura(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)

        if usuario:
            return jsonify(usuario.serialize_facturas()), 200
        
        else:
            abort(404, description="Usuario no encontrado")
        
    except Exception as e:
        print(e)
        abort(500, description = "Error interno de servidor")

@factura_bp.route('/admin', methods=['GET'])
def lista_facturas():
    try:
        facturas = Factura.query.all()
        print(f"Facturas recibidas aqui: {facturas}")
        return jsonify([factura.serialize() for factura in facturas]), 200

    except Exception as e:
        print(e)
        abort(500, description="Error interno del servidor")


@factura_bp.route('/admin/lista/<int:id_factura>', methods=["PATCH"])
@jwt_required()
def terminar_factura(id_factura):
    try:
        factura = Factura.query.get(id_factura)
        if not factura:
            return jsonify({'message': 'Factura no encontrada'}), 404
        
        factura.completado = 1
        db.session.commit()

        return jsonify({'message': 'Factura Completada', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar la factura', 'error': str(e)}), 500
    

@factura_bp.route('/admin/cancelar/<int:id_factura>', methods=["PATCH"])
@jwt_required()
def cancelar_factura(id_factura):
    try:
        factura = Factura.query.get(id_factura)
        if not factura:
            return jsonify({'message': 'Factura no encontrada'}), 404
        
        factura.completado = 2
        db.session.commit()

        return jsonify({'message': 'Factura Cancelada', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar la factura', 'error': str(e)}), 500