from flask import Blueprint, request, jsonify
import event_logger
from routes.common import success_response, error_response

events_bp = Blueprint('events', __name__)

@events_bp.route('', methods=['GET'])
@events_bp.route('/', methods=['GET'])
def get_events_list():
    """Retorna la lista de eventos con filtros opcionales de categoría, búsqueda y paginación."""
    category = request.args.get('category')
    search = request.args.get('search')
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
    except (ValueError, TypeError):
        limit = 50

    try:
        offset = max(int(request.args.get('offset', 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    data = event_logger.get_events(category=category, search=search, limit=limit, offset=offset)
    return jsonify(data)

@events_bp.route('/summary', methods=['GET'])
def get_events_summary():
    """Retorna estadísticas resumidas de movimientos."""
    summary = event_logger.get_event_summary()
    return jsonify(summary)
