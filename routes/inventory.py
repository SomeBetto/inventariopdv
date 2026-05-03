from flask import Blueprint, request, jsonify
import db_manager

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def get_inventory():
    return jsonify(db_manager.get_inventory_all())

@inventory_bp.route('/search', methods=['POST'])
def search_inventory():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_inventory(query))

@inventory_bp.route('/update', methods=['POST'])
def update_inventory():
    data = request.get_json()
    codigo = data.get('codigo')
    nueva_cantidad = data.get('cantidad')
    if not codigo or nueva_cantidad is None:
        return jsonify({'error': 'Datos incompletos'}), 400
    success, message = db_manager.update_inventory(codigo, nueva_cantidad)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500
