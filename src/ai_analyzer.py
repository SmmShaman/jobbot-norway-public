"""AI analysis for job relevance using Azure OpenAI."""
import os
import json
import re
from openai import AzureOpenAI

def clean_json_response(response: str) -> str:
    """Clean markdown formatting from JSON response."""
    # Remove markdown code blocks
    response = re.sub(r'```json\n?', '', response)
    response = re.sub(r'```\n?', '', response)
    response = response.strip()
    return response

def analyze_job_relevance(job_title: str, job_description: str, user_skills: str) -> dict:
    """Analyze if job is relevant for the user."""
    client = AzureOpenAI(
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_key=os.getenv("OPENAI_KEY"),
        api_version="2024-05-01-preview"
    )
    
    prompt = f"""
    Analyze this job posting for relevance to a candidate with these skills: {user_skills}
    Job Title: {job_title}
    Job Description: {job_description[:2000]}
    
    Respond with ONLY valid JSON, no markdown formatting:
    {{
        "relevance_score": 85,
        "is_relevant": true,
        "match_reasons": ["reason1", "reason2"],
        "concerns": ["concern1"],
        "recommendation": "APPLY"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        raw_response = response.choices[0].message.content
        cleaned_response = clean_json_response(raw_response)
        
        result = json.loads(cleaned_response)
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {raw_response[:200]}...")
        return {"relevance_score": 0, "is_relevant": False, "recommendation": "SKIP"}
    except Exception as e:
        print(f"AI analysis error: {e}")
        return {"relevance_score": 0, "is_relevant": False, "recommendation": "SKIP"}

if __name__ == "__main__":
    # Test with sample data
    result = analyze_job_relevance(
        "Python Developer",
        "We need a Python developer with FastAPI experience",
        "Python, FastAPI, SQL, Docker"
    )
    print(json.dumps(result, indent=2))


def get_azure_client():
    """Get Azure OpenAI client."""
    from openai import AzureOpenAI
    import os
    
    return AzureOpenAI(
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_key=os.getenv("OPENAI_KEY"),
        api_version="2024-05-01-preview"
    )
