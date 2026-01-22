from flask import jsonify
from app import db
from app.errors import bp  # <--- 刚才报错就是因为缺了这一行！

@bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify({
        'error': 'Not Found', 
        'message': 'The requested URL was not found on the server.'
    }), 404

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error has occurred.'
    }), 500