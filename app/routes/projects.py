from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth

projects_bp = Blueprint('projects', __name__)

# GET all projects for current user
@projects_bp.route('/', methods=['GET'])
@require_auth
def get_projects():
    try:
        supabase = get_supabase()
        res = supabase.table('projects') \
            .select('*') \
            .eq('user_id', request.user_id) \
            .order('created_at', desc=True) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET single project
@projects_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('projects') \
            .select('*') \
            .eq('id', project_id) \
            .eq('user_id', request.user_id) \
            .single() \
            .execute()
        if not res.data:
            return jsonify({'error': 'Project not found'}), 404
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST create project
@projects_bp.route('/', methods=['POST'])
@require_auth
def create_project():
    try:
        body = request.get_json()
        if not body.get('name'):
            return jsonify({'error': 'Project name is required'}), 400

        supabase = get_supabase()
        res = supabase.table('projects').insert({
            'user_id': request.user_id,
            'name': body['name'],
            'description': body.get('description', ''),
            'status': 'active'
        }).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PATCH update project
@projects_bp.route('/<project_id>', methods=['PATCH'])
@require_auth
def update_project(project_id):
    try:
        body = request.get_json()
        allowed = ['name', 'description', 'status']
        updates = {k: v for k, v in body.items() if k in allowed}

        supabase = get_supabase()
        res = supabase.table('projects') \
            .update(updates) \
            .eq('id', project_id) \
            .eq('user_id', request.user_id) \
            .execute()
        return jsonify(res.data[0]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE project
@projects_bp.route('/<project_id>', methods=['DELETE'])
@require_auth
def delete_project(project_id):
    try:
        supabase = get_supabase()
        supabase.table('projects') \
            .delete() \
            .eq('id', project_id) \
            .eq('user_id', request.user_id) \
            .execute()
        return jsonify({'message': 'Project deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500