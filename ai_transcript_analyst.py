import os
from google import genai
import json

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_transcript_with_gemini(transcript: str):
   
    # Updated prompt to match your new database fields
    prompt = f"""
    You are an expert Customer Care Quality Assurance Analyst. 
    Analyze the following call transcript between an agent and a customer.
    
    Transcript:
    {transcript}

    Return the response STRICTLY as a JSON object with these exact keys:
    1. "score": (A float from 1-100 based on helpfulness and professionalism)
    2. "sentiment": (String: "Positive", "Neutral", or "Negative" based on the customer's mood)
    3. "summary": (A concise 2-3 sentence overview of the interaction)
    4. "improvement_points": (Specific, actionable advice for the agent to do better next time in summary form not in points)
    5. "is_issue_resolved": (Boolean: true if the customer's problem was actually fixed, false otherwise)
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    print(response.text)
    raw_json = response.text.strip('` \n').replace('json', '')
    return json.loads(raw_json)