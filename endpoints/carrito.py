from flask import Flask, jsonify, request, abort, Blueprint
from models import db, Usuario, Carrito, ItemCarrito, Cotizacion
from datetime import datetime as date
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
carrito_bp = Blueprint('carrito_bp', __name__)

@carrito_bp.route('/<int:usuario_id>', methods = ['GET'])
def obtener_carrito(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)

        if usuario:
            if usuario.carrito:
                return jsonify(usuario.serialize_cart()), 200
            else:
                now = date.now().strftime("%Y-%m-%d %H:%M:%S")

                new_carrito = Carrito(
                    id_usuario = usuario.id,
                    creado_en = now
                    )

                try:
                    db.session.add(new_carrito)
                    db.session.commit()
                    return jsonify(usuario.serialize_cart()), 201
                except Exception as e:
                    db.session.rollback()
                    return jsonify({'message': 'Error al crear nuevo carrito'}), 500
        else:
            abort(404, description="Usuario no encontrado")
    except Exception as e:
        print(e)
        abort(500, description="Error interno del servidor")




@carrito_bp.route('/add/<int:id_carrito>', methods = ['POST'])
def agregar_item(id_carrito):
    
    datos = request.get_json()

    if not datos:
        return jsonify({'message': 'No datos recibidos'}), 400
    print(f"Datos recibidos aqui: {datos}")

    if not all(key in datos for key in ('cantidad', 'id_producto')):
        print("Datos incompletos o malformados")
        return jsonify({'message': 'Datos incompletos'}), 400

    try:
        cantidad = int(datos['cantidad'])
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['cantidad']}, Type: {type(datos['cantidad'])}")  # Puedo Añadir un log de error con más detalles.
        return jsonify({'message': 'Cantidad recibida incorrecta'}), 400

    if not (isinstance(cantidad, int) and cantidad > 0):
            return jsonify({'message': 'Cantidad rara'}), 400

    try:
        id_producto = datos['id_producto']
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['id_producto']}, Type: {type(datos['id_producto'])}")  # Añadir un log de error con más detalles.
        return jsonify({'message': 'id_producto valor invalido'}), 400

    if not (isinstance(id_producto, int) and id_producto > 0):
            return jsonify({'message': 'id_producto raro'}), 400

    nuevo_item = ItemCarrito()
    nuevo_item.cantidad = cantidad
    nuevo_item.id_carrito = id_carrito
    nuevo_item.id_producto = id_producto

    try:
        db.session.add(nuevo_item)
        db.session.commit()
        return jsonify({'message': 'Item agregado a carrito', 'success':True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al agregar producto a carrito'}), 500

@carrito_bp.route('/item/<int:id_item_carrito>', methods =['PATCH'])
def actualizar_item_carrito(id_item_carrito):
    datos = request.get_json()
     
    try:
        nueva_cantidad = datos['cantidad']
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['cantidad']}, Type: {type(datos['cantidad'])}")  # Añadir un log de error con más detalles.
        return jsonify({'message': 'Cantidad valor invalido'}), 400
    
    if nueva_cantidad is None:
        return jsonify({'message': 'Cantidad faltante'}), 400
    
    try:
        item_carrito = ItemCarrito.query.get(id_item_carrito)
        if not item_carrito:
            return jsonify({'message': 'Item no encontrado en carrito'}), 404
        
        if nueva_cantidad > 0:
            item_carrito.cantidad = nueva_cantidad
            db.session.commit()
            return jsonify({'message': 'Item actualizado', 'success': True})
        else:
            db.session.delete(item_carrito)
            db.session.commit()
            return jsonify({'message': 'Item eliminado de carrito', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar ItemCarrito', 'error': str(e)})

@carrito_bp.route('/cotizacion/eliminar/<int:id_cotizacion>', methods=['DELETE'])
@jwt_required()
def eliminar_cotizacion(id_cotizacion):
    try:
        cotizacion = Cotizacion.query.get(id_cotizacion)
        if cotizacion:
            db.session.delete(cotizacion)
            db.session.commit()
            return jsonify({'message': 'Cotizacion eliminada con exito', 'success': True}), 200
        else:
            return jsonify({'message': 'Cotizacion no encontrada'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al eliminar la cotizacion', 'error': str(e), 'success': False}), 500

@carrito_bp.route('/cotizacion/<int:id_usuario>', methods=['POST'])
def agregar_cotizacion(id_usuario):
    datos = request.get_json()

    descripcion = datos['descripcion']

    try:
        id_producto = datos['id_producto']
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['id_producto']}, Type: {type(datos['id_producto'])}")  # Añadir un log de error con más detalles.
        return jsonify({'message': 'id_producto valor invalido'}), 400

    try:
        precio = datos['precio']
    except ValueError as e:
        print(f"Error: {str(e)}, Value: {datos['precio']}, Type: {type(datos['precio'])}")  # Añadir un log de error con más detalles.
        return jsonify({'message': 'precio valor invalido'}), 400

    carrito = Carrito.query.filter_by(id_usuario=id_usuario).first()
    try:
        if not carrito:
            #No hay carrito, crear uno nuevo
            now = date.now().strftime("%Y-%m-%d %H:%M:%S")
            new_carrito = Carrito(
                id_usuario = id_usuario,
                creado_en = now
                )
            try:
                db.session.add(new_carrito)
                db.session.commit()
                db.session.flush()
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Error al crear nuevo carrito'}), 500
            carrito = new_carrito
        cotizacion = Cotizacion(
            id_carrito = carrito.id_carrito,
            id_producto = id_producto,
            descripcion = descripcion,
            precio = precio
        )
        db.session.add(cotizacion)
        db.session.commit()
        
        return jsonify({'message': 'Cotizacion agregada exitosamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e), 'success': True}), 500
    