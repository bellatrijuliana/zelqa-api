from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth
from app.services import llm
from app.config import Config

test_cases_bp = Blueprint('test_cases', __name__)

GENERATE_SYSTEM = """You are an expert QA engineer. Generate comprehensive test cases from requirements.
Always respond with valid JSON only."""

GENERATE_PROMPT = """
Feature: {feature_name}

Requirements:
{requirements}

Generate test cases covering Positive, Negative, Boundary, and Edge Cases.
For each test case, assess risk using Probability (1-5) × Impact (1-5).

Return a JSON array with this structure:
[
  {{
    "title": "string",
    "type": "Positive|Negative|Boundary|Edge Case",
    "preconditions": "string",
    "steps": "string",
    "expected_result": "string",
    "probability": 1-5,
    "impact": 1-5,
    "risk_reasoning": "string",
    "testing_approach": "Manual Testing|Automation Testing|Security Testing|Performance Testing"
  }}
]

Generate maximum {max_cases} test cases. Focus on quality over quantity.
"""

# GET test cases for a project
@test_cases_bp.route('/<project_id>', methods=['GET'])
@require_auth
def get_test_cases(project_id):
    try:
        supabase = get_supabase()
        query = supabase.table('test_cases') \
            .select('*, features(name)') \
            .eq('project_id', project_id)

        # Optional filters
        status = request.args.get('status')
        risk_level = request.args.get('risk_level')
        feature_id = request.args.get('feature_id')

        if status:
            query = query.eq('status', status)
        if risk_level:
            query = query.eq('risk_level', risk_level)
        if feature_id:
            query = query.eq('feature_id', feature_id)

        res = query.order('risk_score', desc=True).execute()
        return jsonify(res.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST generate test cases via LLM
@test_cases_bp.route('/generate', methods=['POST'])
@require_auth
def generate_test_cases():
    try:
        body = request.get_json()
        project_id = body.get('project_id')
        feature_id = body.get('feature_id')
        feature_name = body.get('feature_name')
        requirements = body.get('requirements')

        if not all([project_id, feature_id, feature_name, requirements]):
            return jsonify({'error': 'project_id, feature_id, feature_name, and requirements are required'}), 400

        # Generate via LLM
        prompt = GENERATE_PROMPT.format(
            feature_name=feature_name,
            requirements=requirements,
            max_cases=Config.MAX_GENERATED_CASES
        )
        generated = llm.generate_json(prompt, GENERATE_SYSTEM)

        # Compute risk level and save to DB
        supabase = get_supabase()
        saved = []

        for tc in generated:
            prob = tc.get('probability', 3)
            impact = tc.get('impact', 3)
            score = prob * impact

            if score >= Config.RISK_THRESHOLD['critical']:
                risk_level = 'Critical'
            elif score >= Config.RISK_THRESHOLD['high']:
                risk_level = 'High'
            elif score >= Config.RISK_THRESHOLD['medium']:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'

            res = supabase.table('test_cases').insert({
                'project_id': project_id,
                'feature_id': feature_id,
                'title': tc.get('title', ''),
                'type': tc.get('type', 'Positive'),
                'preconditions': tc.get('preconditions', ''),
                'steps': tc.get('steps', ''),
                'expected_result': tc.get('expected_result', ''),
                'status': 'Pending',
                'risk_level': risk_level,
                'risk_score': score,
                'probability': prob,
                'impact': impact,
                'risk_reasoning': tc.get('risk_reasoning', ''),
                'testing_approach': tc.get('testing_approach', 'Manual Testing'),
                'source': 'llm_intake',
            }).execute()
            saved.append(res.data[0])

        return jsonify({'generated': len(saved), 'test_cases': saved}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PATCH approve/reject a test case
@test_cases_bp.route('/<test_case_id>/status', methods=['PATCH'])
@require_auth
def update_status(test_case_id):
    try:
        body = request.get_json()
        status = body.get('status')
        if status not in ['Approved', 'Rejected', 'Pending', 'Retired']:
            return jsonify({'error': 'Invalid status'}), 400

        supabase = get_supabase()
        res = supabase.table('test_cases') \
            .update({'status': status}) \
            .eq('id', test_case_id) \
            .execute()
        return jsonify(res.data[0]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE test case
@test_cases_bp.route('/<test_case_id>', methods=['DELETE'])
@require_auth
def delete_test_case(test_case_id):
    try:
        supabase = get_supabase()
        supabase.table('test_cases').delete().eq('id', test_case_id).execute()
        return jsonify({'message': 'Test case deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500