from flask import Blueprint, request, jsonify
import db_manager

prices_bp = Blueprint('prices', __name__)

@prices_bp.route('/')
def get_prices():
    return jsonify(db_manager.get_prices_all())

@prices_bp.route('/search', methods=['POST'])
def search_prices():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_prices(query))

@prices_bp.route('/update', methods=['POST'])
def update_prices():
    data = request.get_json()
    codigo = data.get('codigo')
    p_venta = data.get('p_venta')
    p_costo = data.get('p_costo')
    
    if not codigo or (p_venta is None and p_costo is None):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if p_venta is not None:
        p_venta = float(p_venta)
    if p_costo is not None:
        p_costo = float(p_costo)

    success, message = db_manager.update_prices(codigo, p_venta, p_costo)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500
