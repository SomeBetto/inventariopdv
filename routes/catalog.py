from flask import Blueprint, request, jsonify
import db_manager

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/')
def get_catalog():
    return jsonify(db_manager.get_catalog_all())

@catalog_bp.route('/search', methods=['POST'])
def search_catalog():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_catalog(query))

@catalog_bp.route('/update', methods=['POST'])
def update_catalog():
    data = request.get_json()
    codigo = data.get('codigo')
    descripcion = data.get('descripcion')
    
    if not codigo or not descripcion:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    success, message = db_manager.update_description(codigo, descripcion)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500
