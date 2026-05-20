from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

test_plans_bp = Blueprint('test_plans', __name__)

@test_plans_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_test_plans(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('test_plans') \
            .select('*, test_plan_sections(*)') \
            .eq('project_id', project_id) \
            .order('created_at', desc=True) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@test_plans_bp.route('/', methods=['POST'])
@require_auth
def create_test_plan():
    try:
        body = request.get_json()
        supabase = get_supabase()
        res = supabase.table('test_plans').insert({
            'project_id': body['project_id'],
            'sprint': body.get('sprint'),
            'objectives': body.get('objectives', ''),
            'scope': body.get('scope', ''),
            'testing_approach': body.get('testing_approach', ''),
            'entry_criteria': body.get('entry_criteria', ''),
            'exit_criteria': body.get('exit_criteria', ''),
            'schedule': body.get('schedule', ''),
            'resources': body.get('resources', ''),
            'status': 'Draft',
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@test_plans_bp.route('/<test_plan_id>', methods=['PATCH'])
@require_auth
def update_test_plan(test_plan_id):
    try:
        body = request.get_json()
        allowed = ['sprint', 'objectives', 'scope', 'testing_approach',
                   'entry_criteria', 'exit_criteria', 'schedule', 'resources', 'status']
        updates = {k: v for k, v in body.items() if k in allowed}

        supabase = get_supabase()
        res = supabase.table('test_plans') \
            .update(updates) \
            .eq('id', test_plan_id) \
            .execute()
        return jsonify(res.data[0]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@test_plans_bp.route('/<test_plan_id>/sections', methods=['POST'])
@require_auth
def add_section(test_plan_id):
    try:
        body = request.get_json()
        supabase = get_supabase()
        res = supabase.table('test_plan_sections').insert({
            'test_plan_id': test_plan_id,
            'title': body['title'],
            'content': body.get('content', ''),
            'order_index': body.get('order_index', 0),
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500