from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

execution_bp = Blueprint('execution', __name__)

@execution_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_execution_logs(project_id):
    try:
        sprint = request.args.get('sprint')
        supabase = get_supabase()
        query = supabase.table('execution_logs') \
            .select('*, test_cases(title, risk_level)') \
            .eq('project_id', project_id)
        if sprint:
            query = query.eq('sprint', sprint)
        res = query.order('executed_at', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@execution_bp.route('/', methods=['POST'])
@require_auth
def log_execution():
    try:
        body = request.get_json()
        required = ['project_id', 'test_case_id', 'sprint', 'result']
        if not all(body.get(k) for k in required):
            return jsonify({'error': f'{required} are required'}), 400

        supabase = get_supabase()
        res = supabase.table('execution_logs').insert({
            'project_id': body['project_id'],
            'test_case_id': body['test_case_id'],
            'sprint': body['sprint'],
            'result': body['result'],
            'actual_result': body.get('actual_result', ''),
            'notes': body.get('notes', ''),
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500