import os
from flask import Flask, render_template, send_from_directory, jsonify

from routes.inventory import inventory_bp
from routes.prices import prices_bp
from routes.catalog import catalog_bp
from routes.sales import sales_bp
from routes.clients import clients_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(prices_bp, url_prefix='/api/prices')
app.register_blueprint(catalog_bp, url_prefix='/api/catalog')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(clients_bp, url_prefix='/api/clients')

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
