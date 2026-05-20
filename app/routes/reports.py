from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_reports(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('reports') \
            .select('*') \
            .eq('project_id', project_id) \
            .order('generated_at', desc=True) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/', methods=['POST'])
@require_auth
def create_report():
    try:
        body = request.get_json()
        supabase = get_supabase()
        res = supabase.table('reports').insert({
            'project_id': body['project_id'],
            'file_name': body['file_name'],
            'sprint': body.get('sprint'),
            'format': body.get('format', 'html'),
            'file_url': body.get('file_url'),
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500