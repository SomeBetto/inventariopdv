from flask import Blueprint, request, jsonify, session
import db_manager
from routes.common import get_client_ip, error_response

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('', methods=['GET'])
@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    return jsonify(db_manager.get_inventory_all())

@inventory_bp.route('/search', methods=['POST'])
def search_inventory():
    data = request.get_json(silent=True) or {}
    query = data.get('query') or data.get('codigo')
    if not query:
        return error_response('Parámetro de búsqueda no proporcionado', 400)
    return jsonify(db_manager.search_inventory(query))

@inventory_bp.route('/update', methods=['POST'])
def update_inventory():
    data = request.get_json(silent=True) or {}
    codigo = data.get('codigo')
    nueva_cantidad = data.get('cantidad')
    if not codigo or nueva_cantidad is None:
        return error_response('Datos incompletos', 400)

    user = session.get('user_name', 'Directo')
    ip = get_client_ip()
    success, message = db_manager.update_inventory(codigo, nueva_cantidad, user_name=user, ip_address=ip)
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500
