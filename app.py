from flask import Flask, render_template, request, jsonify
import db_manager

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def get_products():
    products = db_manager.get_all_products()
    return jsonify(products)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    codigo = data.get('codigo')
    if not codigo:
        return jsonify({'error': 'Código no proporcionado'}), 400
    
    product = db_manager.get_product(codigo)
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/update', methods=['POST'])
def update():
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
