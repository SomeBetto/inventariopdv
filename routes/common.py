from flask import jsonify, request

def get_client_ip():
    """Obtiene la dirección IP del cliente considerando posibles proxies."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

def success_response(data=None, message=None, status_code=200):
    """Genera una respuesta JSON exitosa estandarizada."""
    response = {}
    if message is not None:
        response['message'] = message
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            return jsonify(data), status_code
    return jsonify(response), status_code

def error_response(message="Ha ocurrido un error", status_code=400):
    """Genera una respuesta JSON de error estandarizada."""
    return jsonify({'error': message}), status_code
