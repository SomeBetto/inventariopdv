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
def ensure_session():
    if 'user_id' not in session:
        session['user_id'] = 1
        session['user_name'] = 'Admin'
        session['is_admin'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/desktop')
def desktop():
    import io
    import base64
    import qrcode
    from show_qr import get_local_ip
    
    ip = get_local_ip()
    url = f"http://{ip}:5000"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#030712", back_color="#ffffff")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('desktop.html', server_url=url, qr_b64=qr_b64, ip=ip)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
