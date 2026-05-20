from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth
from app.services import llm

defects_bp = Blueprint('defects', __name__)

DEFECT_DRAFT_PROMPT = """
A test case failed during QA testing. Draft a professional bug report.

Test Case: {title}
Steps: {steps}
Expected Result: {expected_result}
Actual Result: {actual_result}

Return JSON:
{{
  "title": "clear bug title",
  "description": "detailed description",
  "steps_to_reproduce": "numbered steps",
  "expected_result": "what should happen",
  "actual_result": "what actually happened",
  "severity": "Critical|High|Medium|Low"
}}
"""

# GET defects for project
@defects_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_defects(project_id):
    try:
        supabase = get_supabase()
        query = supabase.table('defects') \
            .select('*') \
            .eq('project_id', project_id)

        status = request.args.get('status')
        severity = request.args.get('severity')
        if status:
            query = query.eq('status', status)
        if severity:
            query = query.eq('severity', severity)

        res = query.order('created_at', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET defect stats
@defects_bp.route('/<project_id>/stats', methods=['GET'])
@require_auth
def get_defect_stats(project_id):
    try:
        supabase = get_supabase()
        res = supabase.table('defects') \
            .select('status, severity') \
            .eq('project_id', project_id) \
            .execute()

        defects = res.data
        total = len(defects)

        by_status = {}
        by_severity = {}
        for d in defects:
            by_status[d['status']] = by_status.get(d['status'], 0) + 1
            by_severity[d['severity']] = by_severity.get(d['severity'], 0) + 1

        open_count = by_status.get('Open', 0) + by_status.get('In Progress', 0)
        open_rate = round((open_count / total * 100), 1) if total > 0 else 0

        return jsonify({
            'total': total,
            'by_status': by_status,
            'by_severity': by_severity,
            'open_rate': open_rate,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST create defect (manual or LLM draft)
@defects_bp.route('/', methods=['POST'])
@require_auth
def create_defect():
    try:
        body = request.get_json()
        use_llm = body.get('use_llm', False)

        if use_llm:
            prompt = DEFECT_DRAFT_PROMPT.format(
                title=body.get('test_case_title', ''),
                steps=body.get('steps', ''),
                expected_result=body.get('expected_result', ''),
                actual_result=body.get('actual_result', ''),
            )
            drafted = llm.generate_json(prompt)
            defect_data = {
                'project_id': body['project_id'],
                'test_case_id': body.get('test_case_id'),
                'execution_id': body.get('execution_id'),
                'is_llm_drafted': True,
                **drafted
            }
        else:
            defect_data = {
                'project_id': body['project_id'],
                'test_case_id': body.get('test_case_id'),
                'execution_id': body.get('execution_id'),
                'title': body['title'],
                'description': body.get('description', ''),
                'steps_to_reproduce': body.get('steps_to_reproduce', ''),
                'expected_result': body.get('expected_result', ''),
                'actual_result': body.get('actual_result', ''),
                'severity': body.get('severity', 'Medium'),
                'is_llm_drafted': False,
            }

        supabase = get_supabase()
        res = supabase.table('defects').insert(defect_data).execute()

        # Log initial status
        supabase.table('defect_status_logs').insert({
            'defect_id': res.data[0]['id'],
            'from_status': None,
            'to_status': 'Open',
            'notes': 'Defect created',
        }).execute()

        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PATCH update defect status
@defects_bp.route('/<defect_id>/status', methods=['PATCH'])
@require_auth
def update_defect_status(defect_id):
    try:
        body = request.get_json()
        new_status = body.get('status')
        valid = ['Open', 'In Progress', 'Fixed', 'Verified', 'Closed']
        if new_status not in valid:
            return jsonify({'error': 'Invalid status'}), 400

        supabase = get_supabase()

        # Get current status
        current = supabase.table('defects') \
            .select('status') \
            .eq('id', defect_id) \
            .single() \
            .execute()

        # Update defect
        supabase.table('defects') \
            .update({'status': new_status}) \
            .eq('id', defect_id) \
            .execute()

        # Log status change
        supabase.table('defect_status_logs').insert({
            'defect_id': defect_id,
            'from_status': current.data['status'],
            'to_status': new_status,
            'notes': body.get('notes', ''),
        }).execute()

        return jsonify({'message': 'Status updated', 'status': new_status}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET defect status timeline
@defects_bp.route('/<defect_id>/timeline', methods=['GET'])
@require_auth
def get_defect_timeline(defect_id):
    try:
        supabase = get_supabase()
        res = supabase.table('defect_status_logs') \
            .select('*') \
            .eq('defect_id', defect_id) \
            .order('changed_at', desc=False) \
            .execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500