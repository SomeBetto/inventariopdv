from flask import Flask, render_template, request, jsonify
import db_manager

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/inventory')
def get_inventory():
    return jsonify(db_manager.get_inventory_all())

@app.route('/api/inventory/search', methods=['POST'])
def search_inventory():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_inventory(query))

@app.route('/api/inventory/update', methods=['POST'])
def update_inventory():
    data = request.get_json()
    codigo = data.get('codigo')
    nueva_cantidad = data.get('cantidad')
    if not codigo or nueva_cantidad is None:
        return jsonify({'error': 'Datos incompletos'}), 400
    success, message = db_manager.update_inventory(codigo, nueva_cantidad)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500

@app.route('/api/prices')
def get_prices():
    return jsonify(db_manager.get_prices_all())

@app.route('/api/prices/search', methods=['POST'])
def search_prices():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    return jsonify(db_manager.search_prices(query))

@app.route('/api/prices/update', methods=['POST'])
def update_prices():
    data = request.get_json()
    codigo = data.get('codigo')
    p_venta = data.get('p_venta')
    p_costo = data.get('p_costo')
    
    if not codigo or (p_venta is None and p_costo is None):
        return jsonify({'error': 'Datos incompletos'}), 400
    
    if p_venta is not None:
        p_venta = float(p_venta)
    if p_costo is not None:
        p_costo = float(p_costo)

    success, message = db_manager.update_prices(codigo, p_venta, p_costo)
    if success:
        return jsonify({'message': message})
    else:
        return jsonify({'error': message}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
