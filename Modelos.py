from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

DIAS = {
    'Monday': 'Lun',
    'Tuesday': 'Mar',
    'Wednesday': 'Mie',
    'Thursday': 'Jue',
    'Friday': 'Vie',
    'Saturday': 'Sab',
    'Sunday': 'Dom'
    }

# ... (Código de modelos ) ...
class Producto(db.Model):
    id_producto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45))
    precio = db.Column(db.Integer)
    existencia = db.Column(db.Integer)
    descripcion = db.Column(db.String(45))
    activo = db.Column(db.Integer)
    departamento = db.Column(db.Integer, db.ForeignKey('departamentos.id_departamentos'), nullable=False)
    items = db.relationship('ItemCarrito', back_populates='producto')
    departamentos = db.relationship('Departamentos', back_populates='producto')

    def get_imagen_url(self):
        base_url = 'https://funny-romantic-deer.ngrok-free.app' #'https://10.0.2.2:8080'
        carpeta = '/static/imagenes_productos'
        image_name = self.id_producto
        extension = 'jpg'
        return f"{base_url}{carpeta}/{image_name}.{extension}"

    def serialize(self):
        return {
            'id_producto': self.id_producto,
            'nombre': self.nombre,
            'precio': self.precio,
            'existencia': self.existencia,
            'descripcion': self.descripcion,
            'activo': self.activo,
            'imagen_url': self.get_imagen_url(),
            'departamento': self.departamentos.serialize() if self.departamento else None
        }
    
    def serialize_factura(self):
        return{
            'id_producto': self.id_producto,
            'nombre': self.nombre,
        }
    
    def serialize_nombre(self):
        return{
            'nombre': self.nombre,
            'imagen_url': self.get_imagen_url()
        }

class Departamentos(db.Model):
    id_departamentos = db.Column(db.Integer, primary_key = True)
    nombre = db.Column(db.String(45))
    producto = db.relationship('Producto', back_populates='departamentos')

    def serialize(self):
        return{
            'id_departamentos': self.id_departamentos,
            'nombre': self.nombre
        }

class ItemCarrito(db.Model):
    id_item_carrito = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    id_carrito = db.Column(db.Integer, db.ForeignKey('carrito.id_carrito'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    carrito = db.relationship('Carrito', back_populates='items')
    producto = db.relationship('Producto', back_populates='items')

    def serialize(self):
        return{
            'id_item_carrito': self.id_item_carrito,
            'cantidad': self.cantidad,
            'producto': self.producto.serialize() if self.producto else None
        }

class Cotizacion(db.Model):
    id_cotizacion = db.Column(db.Integer, primary_key=True)
    id_carrito = db.Column(db.Integer, db.ForeignKey('carrito.id_carrito'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable = False)
    descripcion = db.Column(db.String(45), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    carrito = db.relationship('Carrito', backref='cotizaciones')
    producto = db.relationship('Producto', backref='cotizaciones')

    def serialize(self):
        return {
            'id_cotizacion': self.id_cotizacion,
            'servicio': self.producto.serialize_nombre() if self.producto else None,
            'descripcion': self.descripcion,
            'precio': self.precio
        }

class Carrito(db.Model):
    id_carrito = db.Column(db.Integer, primary_key = True)
    creado_en = db.Column(db.DateTime, default= datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable = False)
    items = db.relationship('ItemCarrito', back_populates='carrito')

    def serialize(self):
        return{
            'id_carrito': self.id_carrito,
            'creado_en': self.creado_en,
            'items': [item.serialize() for item in self.items],
            'cotizaciones': [cotizacion.serialize() for cotizacion in self.cotizaciones]
        }

class Role(db.Model):
    id_role = db.Column(db.Integer, primary_key = True)
    nombre = db.Column(db.String(45))
    usuario = db.relationship('Usuario', back_populates='roles')

    def serialize(self):
        return{
            'id': self.id_role,
            'role': self.nombre
        }

class PreguntaSeguridad(db.Model):
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    pregunta = db.Column(db.String(200), nullable=False)
    respuesta = db.Column(db.String(200), nullable=False)

    def set_respuesta(self, respuesta_plana):
        self.respuesta = generate_password_hash(respuesta_plana, method='pbkdf2:sha256')

    def check_respuesta(self, respuesta_plana):
        return check_password_hash(self.respuesta, respuesta_plana)


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nombre = db.Column(db.String(45))
    apellido = db.Column(db.String(45))
    password = db.Column(db.String(120))
    direccion = db.Column(db.String(45))
    telefono = db.Column(db.String(20))
    role = db.Column(db.Integer, db.ForeignKey('role.id_role'), nullable = False)
    carrito = db.relationship('Carrito', backref='usuario', uselist=False)
    chats = db.relationship('UsuarioChat', back_populates='usuario')
    mensajes = db.relationship('MensajesChat', back_populates='usuario')
    roles = db.relationship('Role', back_populates='usuario')

    def check_password(self, password_ingresado):
        return check_password_hash(self.password, password_ingresado)
    
    def serialize(self):
        return{
            'id': self.id,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'roles': self.roles.serialize() if self.role else None
        }
    
    def serialize_nombre(self):
        return{
            'nombre': self.nombre,
            'apellido': self.apellido
        }

    def serialize_with_chats(self):
        return {
            'nombre': self.nombre,
            'chats': [usuario_chat.chat.serialize() for usuario_chat in self.chats] 
        }
    
    def serialize_facturas(self):
        return{
            'facturas': [factura.serialize() for factura in self.facturas]
        }

    def serialize_cart(self):
        return{
            'carrito': self.carrito.serialize() if self.carrito else None
        }

class Chat(db.Model):
    id_chat = db.Column(db.Integer, primary_key = True)
    cliente = db.Column(db.String(45))
    motivo =  db.Column(db.String(45))
    factura = db.Column(db.Integer)
    creado_en = db.Column(db.DateTime, default= datetime.utcnow)
    usuarios = db.relationship('UsuarioChat', back_populates='chat', cascade="all, delete-orphan")
    mensajes = db.relationship('MensajesChat', back_populates='chat', cascade="all, delete-orphan")
    

    def serialize(self):
        dia_semana = DIAS[self.creado_en.strftime('%A')]
        return {
            'id_chat': self.id_chat,
            'cliente': self.cliente,
            'motivo': self.motivo,
            'factura': self.factura,
            'creado_en': f"{dia_semana}, {self.creado_en.strftime('%d %b %Y %H:%M')}" if self.creado_en else None,
            'mensajes': [mensaje.serialize() for mensaje in self.mensajes]
        }

class UsuarioChat(db.Model):
    __tablename__ = 'usuario_chat'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id_chat'), primary_key=True)
    usuario = db.relationship("Usuario", back_populates="chats")
    chat = db.relationship("Chat", back_populates="usuarios")

class MensajesChat(db.Model):
    id_msg = db.Column(db.Integer, primary_key = True)
    id_chat = db.Column(db.Integer, db.ForeignKey('chat.id_chat'), nullable = False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable = False)
    enviado_en = db.Column(db.DateTime, default= datetime.now)
    mensaje = db.Column(db.String(90))
    usuario = db.relationship('Usuario', back_populates= 'mensajes')
    chat = db.relationship('Chat', back_populates = 'mensajes')

    def serialize(self):
        return {
            'id_msg': self.id_msg,
            'mensaje': self.mensaje,
            'id_usuario': self.id_usuario,
            'enviado_en': f"{self.enviado_en.strftime('%H:%M')}" if self.enviado_en else None,
            'usuario': self.usuario.serialize_nombre() if self.id_chat else None
        }


class Factura(db.Model):
    id_factura = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    entrega = db.Column(db.String(45), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    completado = db.Column(db.Integer, default=False)
    usuario = db.relationship('Usuario', backref='facturas')
    items_factura = db.relationship('ItemFactura', backref='factura')
    pagos = db.relationship('Pagos', backref='factura', uselist=False)
    calificacion = db.relationship('Calificacion', backref='factura', uselist=False)

    def serialize(self):
        return {
            'id': self.id_factura,
            'usuario': self.usuario.serialize(),
            'creado_en': self.creado_en.strftime("%Y-%m-%d %H:%M:%S"),
            'entrega': self.entrega,
            'total': self.total,
            'completado': self.completado,
            'pago': self.pagos.serialize() if self.pagos else None,
            'productos': [item.serialize() for item in self.items_factura],
            'calificacion': self.calificacion.serialize() if self.calificacion else None
        }

class ItemFactura(db.Model):
    id_item_factura = db.Column(db.Integer, primary_key=True)
    id_factura = db.Column(db.Integer, db.ForeignKey('factura.id_factura'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    productos = db.relationship('Producto', backref='item_factura')

    def serialize(self):
        return {
            'producto': self.productos.serialize_factura(),
            'cantidad': self.cantidad,
            'precio': self.precio
        }

class Calificacion(db.Model):
    id_calificacion = db.Column(db.Integer, primary_key=True)
    id_factura = db.Column(db.Integer, db.ForeignKey('factura.id_factura'), nullable=False)
    mensaje = db.Column(db.String(45), nullable=False)
    valor = db.Column(db.Integer, nullable=False)
    

    def serialize(self):
        return {
            'valor': self.valor,
            'mensaje': self.mensaje
        }

class Pagos(db.Model):
    id_pago = db.Column(db.Integer, primary_key=True)
    referencia = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    id_factura = db.Column(db.Integer, db.ForeignKey('factura.id_factura'), nullable=False)
    vendedor = db.relationship('Usuario', backref='pagos')

    def serialize(self):
        return {
            'referencia': self.referencia,
            'fecha': self.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            'vendedor': self.vendedor.serialize()
        }