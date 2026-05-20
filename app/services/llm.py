import json
import re
from groq import Groq
from app.config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

def generate(prompt: str, system: str = None) -> str:
    messages = []
    if system:
        messages.append({'role': 'system', 'content': system})
    messages.append({'role': 'user', 'content': prompt})

    response = client.chat.completions.create(
        model=Config.GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=4000,
    )
    return response.choices[0].message.content

def generate_json(prompt: str, system: str = None) -> dict | list:
    system_prompt = (system or '') + '\nRespond ONLY with valid JSON. No explanation, no markdown, no backticks.'
    raw = generate(prompt, system_prompt)

    # Strip markdown code fences if present
    clean = re.sub(r'```json|```', '', raw).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        raise ValueError(f'Failed to parse LLM JSON output: {clean[:200]}')

def check_connection() -> bool:
    try:
        generate('Say "ok"')
        return True
    except:
        return False