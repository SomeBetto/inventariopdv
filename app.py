import os
import io
import base64
import qrcode
from flask import Flask, render_template, session, jsonify
import config
import event_logger
from show_qr import get_local_ip

from routes.inventory import inventory_bp
from routes.prices import prices_bp
from routes.catalog import catalog_bp
from routes.sales import sales_bp
from routes.clients import clients_bp
from routes.events import events_bp
from routes.util import util_bp

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Registro de Blueprints
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(prices_bp, url_prefix='/api/prices')
app.register_blueprint(catalog_bp, url_prefix='/api/catalog')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(util_bp, url_prefix='/')

app_logger = event_logger.get_logger('server')

@app.before_request
def ensure_session():
    """Garantiza acceso directo y abierto al inventario sin bloqueo de login."""
    if 'user_id' not in session:
        session['user_id'] = config.DEFAULT_USER_ID
        session['user_name'] = config.DEFAULT_USER_NAME
        session['is_admin'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/desktop')
def desktop():
    ip = get_local_ip()
    url = f"http://{ip}:{config.APP_PORT}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#030712", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('desktop.html', server_url=url, qr_b64=qr_b64, ip=ip)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    app_logger.error(f"Error 500 no controlado: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    event_logger.log_event('SISTEMA', 'INICIO_SERVIDOR', details=f"Servidor iniciado en puerto {config.APP_PORT}")
    app.run(debug=config.DEBUG, host=config.APP_HOST, port=config.APP_PORT)
