import os
from flask import Flask, render_template, send_from_directory, jsonify, request, session, redirect, url_for
import db_manager


from routes.inventory import inventory_bp
from routes.prices import prices_bp
from routes.catalog import catalog_bp
from routes.sales import sales_bp
from routes.clients import clients_bp
from routes.util import util_bp

app = Flask(__name__)
app.secret_key = 'inventario_pdv_secret_key_123' # En producción usar os.urandom(24)


# Register Blueprints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(prices_bp, url_prefix='/api/prices')
app.register_blueprint(catalog_bp, url_prefix='/api/catalog')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(util_bp, url_prefix='/')

@app.before_request
def protect_api():
    if request.path.startswith('/api/') and not request.path.startswith('/api/auth/'):
        if 'user_id' not in session:
            return jsonify({"error": "No autorizado"}), 401

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
