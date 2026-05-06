from flask import Blueprint, request, jsonify
import db_manager

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
def get_clients():
    return jsonify(db_manager.get_clients_all())

@clients_bp.route('/search', methods=['POST'])
def search_clients():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_clients(query))

@clients_bp.route('/update', methods=['POST'])
def update_client():
    data = request.get_json()
    numero = data.get('numero')
    nombre = data.get('nombre')
    direccion = data.get('direccion')
    telefono = data.get('telefono')
    limite_credito = data.get('limite_credito')
    
    if numero is None:
        return jsonify({'error': 'Número de cliente es requerido'}), 400
    
    try:
        limite_credito = float(limite_credito) if limite_credito is not None else 0.0
    except ValueError:
        limite_credito = 0.0

    success, message = db_manager.update_client(numero, nombre, direccion, telefono, limite_credito)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500
