import os
import json

from google import genai
from dotenv import load_dotenv

from pydantic import BaseModel
from typing import Literal


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)



class VerbatimEvidence(BaseModel):
    score_evidence: str
    sentiment_evidence: str
    resolution_evidence: str


class EvaluationResponse(BaseModel):
    score: float
    score_justification: str
    sentiment: Literal["Positive", "Neutral", "Negative","positive","negative","neutral"]
    sentiment_justification: str
    summary: str
    improvement_points: str
    is_issue_resolved: bool
    resolution_justification: str
    verbatim_evidence: VerbatimEvidence


def analyze_transcript_with_gemini(
    transcript: str,
    is_concatenated: bool
):
    prompt = f"""
You are an expert Customer Care Quality Assurance Analyst.

Your task is to analyze ONLY the information explicitly present in the transcript.

STRICT RULES:
1. Do NOT assume facts that are not clearly mentioned.
2. Do NOT invent customer emotions, resolutions, or agent actions.
3. If evidence is missing, say "Not Mentioned".
4. Every score or conclusion MUST be supported by transcript evidence.
5. Use only transcript-grounded reasoning.
6. Return STRICT VALID JSON only.
7. Do not add markdown, explanations, or extra text outside JSON.
8. If uncertain, choose the safest neutral interpretation.

Transcript:
{transcript}

Return the response STRICTLY as a JSON object with these exact keys:

{{
  "score": float,
  "score_justification": string,

  "sentiment": string,
  "sentiment_justification": string,

  "summary": string,

  "improvement_points": string,

  "is_issue_resolved": boolean,
  "resolution_justification": string,

  "verbatim_evidence": {{
      "score_evidence": string,
      "sentiment_evidence": string,
      "resolution_evidence": string
  }}
}}

Important:
- "verbatim_evidence" MUST contain exact quotes copied from transcript.
- Do not paraphrase evidence.
- Keep evidence short and relevant.
- If no evidence exists, return "Not Mentioned".
"""

    contents = transcript if is_concatenated else prompt

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config={
                "temperature": 0.2
            }
        )

        raw_json = response.text.strip()

        
        if raw_json.startswith("```json"):
            raw_json = raw_json.replace("```json", "", 1)

        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]

        raw_json = raw_json.strip()

        print(raw_json)

       
        parsed_response = EvaluationResponse.model_validate_json(raw_json)

        return parsed_response.model_dump()

    except Exception as e:
        raise Exception(f"Gemini analysis failed: {str(e)}")