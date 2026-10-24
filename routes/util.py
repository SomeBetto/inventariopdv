import os
from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
import db_manager
import config
from routes.common import get_client_ip

util_bp = Blueprint('util', __name__)

@util_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    success, result = db_manager.authenticate_user(username, password)
    if success:
        session['user_id'] = result['id']
        session['user_name'] = result['nombre']
        session['is_admin'] = result['is_admin']
        return jsonify({"status": "success", "user": result})
    else:
        # En modo de acceso abierto, no bloqueamos
        return jsonify({"status": "error", "message": result}), 401

@util_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@util_bp.route('/api/auth/check')
def check_auth():
    # En modo acceso abierto siempre retorna sesión activa con permisos de administración
    return jsonify({
        "logged_in": True,
        "user_name": session.get('user_name', config.DEFAULT_USER_NAME),
        "is_admin": True
    })

@util_bp.route('/api/admin/users')
def get_users():
    users = db_manager.get_all_users()
    return jsonify(users)

@util_bp.route('/api/admin/users/save', methods=['POST'])
def save_user():
    data = request.get_json(silent=True) or {}
    user = session.get('user_name', 'Directo')
    ip = get_client_ip()
    success, message = db_manager.save_user(data, user_name=user, ip_address=ip)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"status": "error", "message": message}), 500

@util_bp.route('/health')
def health_check():
    return jsonify({"status": "ok", "api": "active"})

@util_bp.route('/info')
def api_info():
    try:
        spec_path = os.path.join(current_app.root_path, 'api_specification.md')
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@util_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(current_app.root_path, 'logo.ico', mimetype='image/vnd.microsoft.icon')
