from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

rtm_bp = Blueprint('rtm', __name__)

@rtm_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_rtm(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('rtm_links') \
            .select('*, test_cases(title, status, risk_level)') \
            .eq('project_id', project_id) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rtm_bp.route('/', methods=['POST'])
@require_auth
def create_rtm_link():
    try:
        body = request.get_json()
        supabase = get_supabase()
        res = supabase.table('rtm_links').insert({
            'project_id': body['project_id'],
            'requirement': body['requirement'],
            'test_case_id': body['test_case_id'],
            'coverage_status': body.get('coverage_status', 'Covered'),
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500