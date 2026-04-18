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
    query = data.get('query') or data.get('codigo')
    print(f"[SEARCH] Consulta recibida: {query}")
    
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    
    product = db_manager.get_product(query)
    if product:
        print(f"[SEARCH] Producto encontrado: {product['descripcion']} (Código: {product['codigo']})")
        return jsonify(product)
    else:
        print(f"[SEARCH] No se encontró ningún producto para: {query}")
        return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/searchall', methods=['POST'])
def search_all():
    data = request.get_json()
    query = data.get('query') or data.get('codigo')
    print(f"[SEARCHALL] Consulta recibida: {query}")
    
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda no proporcionado'}), 400
    
    products = db_manager.search_products(query)
    print(f"[SEARCHALL] Se encontraron {len(products)} coincidencias para: {query}")
    return jsonify(products)

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
