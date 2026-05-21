from flask import Blueprint, request, jsonify
from app import get_supabase
from app.middleware import require_auth
from app.services import llm

rtm_bp = Blueprint('rtm', __name__)

AUTO_MAP_SYSTEM = """You are an expert QA engineer. Your job is to map requirements to test cases and assess coverage.
Respond ONLY with valid JSON. No explanation, no markdown, no backticks."""

AUTO_MAP_PROMPT = """
Given these requirements and test cases, map each requirement to the relevant test cases.

REQUIREMENTS:
{requirements}

TEST CASES:
{test_cases}

For each requirement, find which test cases cover it (if any).
Assess coverage as:
- "Covered": requirement is fully covered by one or more test cases
- "Partial": requirement is partially covered
- "Not Covered": no test cases cover this requirement

Return a JSON array:
[
  {{
    "requirement": "exact requirement text",
    "mappings": [
      {{
        "test_case_id": "uuid",
        "coverage_status": "Covered|Partial|Not Covered"
      }}
    ],
    "overall_coverage": "Covered|Partial|Not Covered"
  }}
]

If a requirement has no matching test cases, return an empty mappings array with overall_coverage "Not Covered".
"""

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


@rtm_bp.route('/auto-map', methods=['POST'])
@require_auth
def auto_map():
    try:
        body = request.get_json()
        project_id = body.get('project_id')
        requirements_text = body.get('requirements')

        if not project_id or not requirements_text:
            return jsonify({'error': 'project_id and requirements are required'}), 400

        # Parse requirements — one per line
        requirements = [r.strip() for r in requirements_text.strip().split('\n') if r.strip()]
        if not requirements:
            return jsonify({'error': 'No requirements found. Enter one requirement per line.'}), 400

        # Fetch all approved test cases for this project
        supabase = get_supabase()
        tc_res = supabase.table('test_cases') \
            .select('id, title, type, steps, expected_result, testing_approach') \
            .eq('project_id', project_id) \
            .eq('status', 'Approved') \
            .execute()

        test_cases = tc_res.data
        if not test_cases:
            return jsonify({'error': 'No approved test cases found. Approve test cases in Curator first.'}), 400

        # Format test cases for LLM
        tc_text = '\n'.join([
            f"[{tc['id']}] {tc['title']} ({tc['type']}) — {tc.get('testing_approach', '')}"
            for tc in test_cases
        ])

        req_text = '\n'.join([f"{i+1}. {r}" for i, r in enumerate(requirements)])

        prompt = AUTO_MAP_PROMPT.format(
            requirements=req_text,
            test_cases=tc_text
        )

        # Call LLM
        mapped = llm.generate_json(prompt, AUTO_MAP_SYSTEM)

        # Save to rtm_links — clear existing first
        supabase.table('rtm_links') \
            .delete() \
            .eq('project_id', project_id) \
            .execute()

        saved = []
        for item in mapped:
            req = item.get('requirement', '')
            mappings = item.get('mappings', [])
            overall = item.get('overall_coverage', 'Not Covered')

            if not mappings:
                # Not covered — save with a placeholder link
                res = supabase.table('rtm_links').insert({
                    'project_id': project_id,
                    'requirement': req,
                    'test_case_id': test_cases[0]['id'],  # placeholder
                    'coverage_status': 'Not Covered',
                }).execute()
                saved.append(res.data[0] if res.data else {})
            else:
                for mapping in mappings:
                    res = supabase.table('rtm_links').insert({
                        'project_id': project_id,
                        'requirement': req,
                        'test_case_id': mapping['test_case_id'],
                        'coverage_status': mapping['coverage_status'],
                    }).execute()
                    if res.data:
                        saved.append(res.data[0])

        return jsonify({
            'mapped': len(mapped),
            'links_created': len(saved),
            'results': mapped
        }), 201

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


@rtm_bp.route('/<link_id>', methods=['DELETE'])
@require_auth
def delete_rtm_link(link_id):
    try:
        supabase = get_supabase()
        supabase.table('rtm_links').delete().eq('id', link_id).execute()
        return jsonify({'message': 'Link deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500