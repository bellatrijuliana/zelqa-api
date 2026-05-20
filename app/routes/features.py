from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

features_bp = Blueprint('features', __name__)

@features_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_features(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('features') \
            .select('*') \
            .eq('project_id', project_id) \
            .order('created_at', desc=False) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@features_bp.route('/', methods=['POST'])
@require_auth
def create_feature():
    try:
        body = request.get_json()
        if not body.get('name') or not body.get('project_id'):
            return jsonify({'error': 'name and project_id are required'}), 400

        supabase = get_supabase()
        res = supabase.table('features').insert({
            'project_id': body['project_id'],
            'name': body['name'],
            'description': body.get('description', ''),
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@features_bp.route('/<feature_id>', methods=['DELETE'])
@require_auth
def delete_feature(feature_id):
    try:
        supabase = get_supabase()
        supabase.table('features').delete().eq('id', feature_id).execute()
        return jsonify({'message': 'Feature deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500