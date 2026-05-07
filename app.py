import os
from flask import Flask, render_template, send_from_directory, jsonify, request, session, redirect, url_for
import db_manager


from routes.inventory import inventory_bp
from routes.prices import prices_bp
from routes.catalog import catalog_bp
from routes.sales import sales_bp
from routes.clients import clients_bp

app = Flask(__name__)
app.secret_key = 'inventario_pdv_secret_key_123' # En producción usar os.urandom(24)


# Register Blueprints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(prices_bp, url_prefix='/api/prices')
app.register_blueprint(catalog_bp, url_prefix='/api/catalog')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(clients_bp, url_prefix='/api/clients')

@app.before_request
def protect_api():
    if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
        if 'user_id' not in session:
            return jsonify({"error": "No autorizado"}), 401

@app.route('/api/auth/login', methods=['POST'])
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

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route('/api/auth/check')
def check_auth():
    if 'user_id' in session:
        return jsonify({
            "logged_in": True, 
            "user_name": session.get('user_name'),
            "is_admin": session.get('is_admin', False)
        })
    return jsonify({"logged_in": False}), 401

@app.route('/api/admin/users')
def get_users():
    if not session.get('is_admin'):
        return jsonify({"error": "No autorizado"}), 403
    users = db_manager.get_all_users()
    return jsonify(users)

@app.route('/api/admin/users/save', methods=['POST'])
def save_user():
    if not session.get('is_admin'):
        return jsonify({"error": "No autorizado"}), 403
    data = request.json
    success, message = db_manager.save_user(data)
    if success:
        return jsonify({"status": "success", "message": message})
    return jsonify({"status": "error", "message": message}), 500


@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "api": "active"})

@app.route('/info')
def api_info():
    try:
        with open(os.path.join(app.root_path, 'api_specification.md'), 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, '.'),
                               'logo.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
