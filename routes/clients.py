from flask import Blueprint, request, jsonify, session
import db_manager
from routes.common import get_client_ip, error_response

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('', methods=['GET'])
@clients_bp.route('/', methods=['GET'])
def get_clients():
    return jsonify(db_manager.get_clients_all())

@clients_bp.route('/search', methods=['POST'])
def search_clients():
    data = request.get_json(silent=True) or {}
    query = data.get('query')
    if not query:
        return error_response('Parámetro de búsqueda no proporcionado', 400)
    return jsonify(db_manager.search_clients(query))

@clients_bp.route('/update', methods=['POST'])
def update_client():
    data = request.get_json(silent=True) or {}
    numero = data.get('numero')
    nombre = data.get('nombre')
    direccion = data.get('direccion', '')
    telefono = data.get('telefono', '')
    limite_credito = data.get('limite_credito')

    if numero is None:
        return error_response('Número de cliente es requerido', 400)

    try:
        limite_credito = float(limite_credito) if limite_credito is not None else 0.0
    except (ValueError, TypeError):
        limite_credito = 0.0

    user = session.get('user_name', 'Directo')
    ip = get_client_ip()
    success, message = db_manager.update_client(
        numero=numero,
        nombre=nombre,
        direccion=direccion,
        telefono=telefono,
        limite_credito=limite_credito,
        user_name=user,
        ip_address=ip
    )
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500
