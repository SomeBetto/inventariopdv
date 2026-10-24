from flask import Blueprint, request, jsonify, session
import db_manager
from routes.common import get_client_ip, error_response

prices_bp = Blueprint('prices', __name__)

@prices_bp.route('', methods=['GET'])
@prices_bp.route('/', methods=['GET'])
def get_prices():
    return jsonify(db_manager.get_prices_all())

@prices_bp.route('/search', methods=['POST'])
def search_prices():
    data = request.get_json(silent=True) or {}
    query = data.get('query') or data.get('codigo')
    if not query:
        return error_response('Parámetro de búsqueda no proporcionado', 400)
    return jsonify(db_manager.search_prices(query))

@prices_bp.route('/update', methods=['POST'])
def update_prices():
    data = request.get_json(silent=True) or {}
    codigo = data.get('codigo')
    p_venta = data.get('p_venta')
    p_costo = data.get('p_costo')

    if not codigo or (p_venta is None and p_costo is None):
        return error_response('Datos incompletos', 400)

    try:
        p_venta = float(p_venta) if p_venta is not None else None
    except (ValueError, TypeError):
        return error_response('Precio de venta no válido', 400)

    try:
        p_costo = float(p_costo) if p_costo is not None else None
    except (ValueError, TypeError):
        return error_response('Precio de costo no válido', 400)

    user = session.get('user_name', 'Directo')
    ip = get_client_ip()
    success, message = db_manager.update_prices(codigo, p_venta, p_costo, user_name=user, ip_address=ip)
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500
