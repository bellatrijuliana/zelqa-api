from functools import wraps
from flask import request, jsonify
from app import get_supabase

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401

        token = auth_header.split(' ')[1]

        try:
            supabase = get_supabase()
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                return jsonify({'error': 'Invalid token'}), 401
            request.user_id = user.user.id
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401

        return f(*args, **kwargs)
    return decorated