from flask import Blueprint, request, jsonify
import db_manager

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/report', methods=['POST'])
def sales_report():
    data = request.get_json()
    time_range = data.get('time_range', 'day')
    group_by = data.get('group_by', 'product')
    department = data.get('department')
    
    report = db_manager.get_sales_report(time_range, group_by, department)
    return jsonify(report)
