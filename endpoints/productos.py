from flask import Flask, jsonify, request, abort, Blueprint
import os
from models import db, Producto, ItemCarrito
from werkzeug.utils import secure_filename
from flask import current_app
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

producto_bp = Blueprint('productos_bp', __name__)

@producto_bp.route('', methods=['GET'])
def obtener_productos():
    try:
        productos = Producto.query.all()
        return jsonify([producto.serialize() for producto in productos]), 200
    except Exception as e:
        
        print(e)
        abort(500, description="Error interno del servidor")


@producto_bp.route('/add', methods=['POST'])
def agregar_producto():
    #Extrae datos de json
    try:

        try:
            nombre = request.form.get('nombre')
        except ValueError as e:
            print(f"Error: {str(e)}, Value: {request.form.get('nombre')}, tipo: {type(request.form.get('nombre'))}")
            return jsonify({'message': 'Nombre invalido o vacio'}), 400

        print(f"Nombre recibidio: {nombre}, tipo: {type(nombre)}")

        try:
            precio = int(request.form.get('precio'))
        except ValueError as e:
            print(f"Error: {str(e)}, Value: {request.form.get('precio')}, Type: {type(request.form.get('precio'))}")  # Añadir un log de error con más detalles.
            return jsonify({'message': 'Precio invalidisimo'}), 400
        print(f"Precio recibidio: {precio}, tipo: {type(precio)}")

        try:
            existencia = int(request.form.get('existencia'))
        except ValueError as e:
            print(f"Error: {str(e)}, Value: {request.form.get('existencia')}, Type: {type(request.form.get('existencia'))}")
            return jsonify({'message': 'Existencia invalidisima'}), 400
        print(f"Existencia recibidia: {existencia}, tipo: {type(existencia)}")

        try:
            departamento = int(request.form.get('departamento'))
        except ValueError as e:
            print(f"Error: {str(e)}, Value: {request.form.get('departamento')}, Type: {type(request.form.get('departamento'))}")
            return jsonify({'message': 'Departamento Invalido'}), 400
        print(f"Nombre recibidio: {departamento}, tipo: {type(departamento)}")

        

        try:
            descripcion = request.form.get('descripcion')
        except ValueError as e:
            print(f"Error: {str(e)}, Value: {request.form.get('descripcion')}, tipo: {type(request.form.get('descripcion'))}")
            return jsonify({'message': 'descripcion invalido o vacio'}), 400

        print(f"descripcion recibidio: {descripcion}, tipo: {type(descripcion)}")


        if not (isinstance(precio, int) and precio >=0):
            return jsonify({'message': 'Precio invalido'}), 400

        if not (isinstance(departamento, int) and departamento >0 and departamento < 6):
            return jsonify({'message': 'Departamento invalido'}), 400

        if not (isinstance(existencia, int) and existencia >=0):
            return jsonify({'message': 'Existencia invalida'}), 400

        if not (isinstance(nombre, str) and len(nombre) > 0):
            return jsonify({'message': 'Nombre invalido'}), 400

        # if not (isinstance(descripcion, str) and len(descripcion) > 0):
        #     return jsonify({'message': 'Descripcion invalida'}), 400

        #Agregar y hacer commit
        try:
            nuevo_producto = Producto(
                nombre = nombre,
                precio = precio,
                existencia = existencia,
                descripcion = descripcion,
                departamento = departamento
            )

            db.session.add(nuevo_producto)
            db.session.commit()
            if 'image' in request.files:
                image = request.files['image']
                if image.filename != '':
                    filename = secure_filename(f"{nuevo_producto.id_producto}.jpg")
                    path = os.path.join(current_app.root_path, 'static/imagenes_productos', filename)
                    image.save(path)
                    return jsonify({'message': 'Producto con imagen agregado exitosamente', 'success': True}), 200
                else: 
                    return jsonify({'message': 'Producto agregado exitosamente', 'success': True}), 200
            else:
                return jsonify({'message': 'Producto agregado exitosamente', 'success': True}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'Ha ocurrido un error al agregar el producto'}), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Ocurrio otro error'}), 505

@producto_bp.route('/edit/<int:id_producto>', methods =['PUT'])
def editar_producto(id_producto):
    
    datos = request.get_json()

    producto = Producto.query.get(id_producto)
    if not producto:
        return jsonify({'message': 'Producto no encontrado'}), 404
    
    try:
        producto.nombre = datos.get('nombre', producto.nombre)
        producto.precio = datos.get('precio', producto.precio)
        producto.descripcion = datos.get('descripcion', producto.descripcion)
        producto.existencia = datos.get('existencia', producto.existencia)
        producto.departamento = datos.get('departamento', producto.departamento)

        db.session.commit()
        return jsonify({'message': 'Producto actualizado exitosamente', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al actualizar el producto', 'error': str(e)}), 500


@producto_bp.route('/upload', methods =['POST'])
def upload_file():

    if 'image' not in request.files:
        return jsonify({'message': 'No imagen part en el quest'}), 400
    
    image = request.files['image']

    if image.filename == '':
        return jsonify ({'message': 'No image selected for uploadin'}), 400

    if image:
        filename = secure_filename(image.filename)
        path = os.path.join(current_app.root_path, 'static/imagenes_productos', filename)
        image.save(path)
        return {'message': 'Imagen subida con exito', 'success': True}
    else:
        return {'message': 'No se encontro la imagen en la peticion'}, 400
    
@producto_bp.route('/admin/cancelar/<int:id_producto>', methods=["PATCH"])
@jwt_required()
def anular_producto(id_producto):
    try:
        producto = Producto.query.get(id_producto)
        if not producto:
            return jsonify({'message': 'Producto no encontrado'}), 404
        
        producto.activo = 0

        ItemCarrito.query.filter_by(id_producto=id_producto).delete()
        db.session.commit()

        return jsonify({'message': 'Producto anulado', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al anular producto', 'error': str(e)}), 500
    

@producto_bp.route('/admin/reactivar/<int:id_producto>', methods=["PATCH"])
@jwt_required()
def activar_producto(id_producto):
    try:
        producto = Producto.query.get(id_producto)
        if not producto:
            return jsonify({'message': 'Producto no encontrado'}), 404
        
        producto.activo = 1
        db.session.commit()

        return jsonify({'message': 'Producto activado', 'success': True}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error al activar producto', 'error': str(e)}), 500