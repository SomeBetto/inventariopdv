import os
from flask import Blueprint, request, jsonify, session, send_from_directory, current_app
import db_manager

util_bp = Blueprint('util', __name__)

@util_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    success, result = db_manager.authenticate_user(username, password)
    if success:
        session['user_id'] = result['id']
        session['user_name'] = result['nombre']
        session['is_admin'] = result['is_admin']
        return jsonify({"status": "success", "user": result})
    else:
        return jsonify({"status": "error", "message": result}), 401

@util_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@util_bp.route('/api/auth/check')
def check_auth():
    if 'user_id' in session:
        return jsonify({
            "logged_in": True, 
            "user_name": session.get('user_name'),
            "is_admin": session.get('is_admin', False)
        })
    return jsonify({"logged_in": False}), 401

@util_bp.route('/api/admin/users')
def get_users():
    if not session.get('is_admin'):
        return jsonify({"error": "No autorizado"}), 403
    users = db_manager.get_all_users()
    return jsonify(users)

@util_bp.route('/api/admin/users/save', methods=['POST'])
def save_user():
    if not session.get('is_admin'):
        return jsonify({"error": "No autorizado"}), 403
    data = request.json
    success, message = db_manager.save_user(data)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"status": "error", "message": message}), 500

@util_bp.route('/health')
def health_check():
    return jsonify({"status": "ok", "api": "active"})

@util_bp.route('/info')
def api_info():
    try:
        # Usar current_app.root_path en lugar de app.root_path
        with open(os.path.join(current_app.root_path, 'api_specification.md'), 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@util_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, '.'),
                               'logo.ico', mimetype='image/vnd.microsoft.icon')
