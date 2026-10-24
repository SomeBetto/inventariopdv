from flask import Blueprint, request, jsonify, session
import db_manager
from routes.common import get_client_ip, error_response

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('', methods=['GET'])
@catalog_bp.route('/', methods=['GET'])
def get_catalog():
    return jsonify(db_manager.get_catalog_all())

@catalog_bp.route('/search', methods=['POST'])
def search_catalog():
    data = request.get_json(silent=True) or {}
    query = data.get('query') or data.get('codigo')
    if not query:
        return error_response('Parámetro de búsqueda no proporcionado', 400)
    return jsonify(db_manager.search_catalog(query))

@catalog_bp.route('/update', methods=['POST'])
def update_catalog():
    data = request.get_json(silent=True) or {}
    codigo = data.get('codigo')
    descripcion = data.get('descripcion')

    if not codigo or not descripcion or not str(descripcion).strip():
        return error_response('Datos incompletos', 400)

    user = session.get('user_name', 'Directo')
    ip = get_client_ip()
    success, message = db_manager.update_description(codigo, descripcion, user_name=user, ip_address=ip)
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500
