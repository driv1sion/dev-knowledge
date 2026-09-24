import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def summarize_project(docs_content: str) -> Dict[str, Any]:
    """
    Summarizes the project documentation using the Gemini API.
    Returns a dictionary containing:
      - description: str
      - architecture_rationale: str
      - features: list of str
      - impact: dict with keys (situation, task, action, result)
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {}

    try:
        from google import genai
        from google.genai import types
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        
        client = genai.Client(api_key=api_key)
        
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True
        )
        def _call_llm(client, prompt, system_instruction):
            return client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "description": {"type": "STRING", "description": "A concise, direct project description paragraph."},
                            "architecture_rationale": {"type": "STRING", "description": "A concise rationale of the architecture and technical decisions."},
                            "features": {
                                "type": "ARRAY", 
                                "items": {"type": "STRING"},
                                "description": "A list of 3-5 core technical features."
                            },
                            "impact": {
                                "type": "OBJECT",
                                "properties": {
                                    "situation": {"type": "STRING"},
                                    "task": {"type": "STRING"},
                                    "action": {"type": "STRING"},
                                    "result": {"type": "STRING", "description": "The quantifiable outcome or impact achieved (metrics, percent increases, efficiency gains)."}
                                }
                            }
                        },
                        "required": ["description", "architecture_rationale", "features", "impact"]
                    }
                )
            )

        
        system_instruction = (
            "You are an expert technical resume writer. Your job is to extract and format project information "
            "from the provided documentation for an ATS-optimized SWE/MLE/AI resume/portfolio. "
            "RULES:\n"
            "1. Output MUST be direct, cohesive, and highly professional.\n"
            "2. DO NOT use verbose, buzzword-heavy, or typical 'AI-generated' marketing language.\n"
            "3. Rely strictly on the provided documentation.\n"
            "4. Impact/Result MUST prioritize quantifiable metrics, percentages, and efficiency gains if available.\n"
        )
        
        prompt = (
            "Given the following repository documentation, extract the project details into the requested JSON format.\n"
            f"Documentation:\n\n{docs_content}\n\n"
        )
        
        response = _call_llm(client, prompt, system_instruction)
        
        return json.loads(response.text)
        
    except Exception as e:
        logger.error(f"Failed to generate LLM summary: {e}")
        return {}
