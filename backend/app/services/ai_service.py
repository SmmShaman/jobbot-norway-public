"""AI analysis service for job relevance using Azure OpenAI."""
import json
import re
from typing import Dict, Optional
from openai import AzureOpenAI
from ..config import settings


class AIAnalyzer:
    """Service for AI-powered job analysis using Azure OpenAI."""

    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    @staticmethod
    def clean_json_response(response: str) -> str:
        """Clean markdown formatting from JSON response.

        Args:
            response: Raw response string from OpenAI

        Returns:
            Cleaned JSON string
        """
        # Remove markdown code blocks
        response = re.sub(r'```json\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        response = response.strip()
        return response

    def analyze_job_relevance(
        self,
        job_title: str,
        job_description: str,
        user_skills: str,
        user_preferences: Optional[str] = None
    ) -> Dict:
        """Analyze if a job posting is relevant for a user.

        Args:
            job_title: The job title
            job_description: Full job description text
            user_skills: User's skills as comma-separated string
            user_preferences: Optional user preferences for job search

        Returns:
            Dictionary with analysis results:
            {
                "relevance_score": int (0-100),
                "is_relevant": bool,
                "match_reasons": list[str],
                "concerns": list[str],
                "recommendation": str ("APPLY" | "SKIP" | "REVIEW")
            }
        """
        # Limit description to prevent token overflow
        description_text = job_description[:2000]

        prompt = f"""
Analyze this job posting for relevance to a candidate.

Candidate Skills: {user_skills}
{f"Candidate Preferences: {user_preferences}" if user_preferences else ""}

Job Title: {job_title}
Job Description: {description_text}

Respond with ONLY valid JSON, no markdown formatting:
{{
    "relevance_score": 85,
    "is_relevant": true,
    "match_reasons": ["reason1", "reason2"],
    "concerns": ["concern1"],
    "recommendation": "APPLY"
}}

Relevance score should be 0-100.
Recommendation should be one of: APPLY, SKIP, REVIEW
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            raw_response = response.choices[0].message.content
            cleaned_response = self.clean_json_response(raw_response)

            result = json.loads(cleaned_response)

            # Validate response structure
            required_keys = ["relevance_score", "is_relevant", "recommendation"]
            if not all(key in result for key in required_keys):
                raise ValueError(f"Missing required keys in response: {result}")

            return result

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {
                "relevance_score": 0,
                "is_relevant": False,
                "match_reasons": [],
                "concerns": ["Failed to parse AI response"],
                "recommendation": "SKIP",
                "error": f"JSON parse error: {str(e)}"
            }
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {
                "relevance_score": 0,
                "is_relevant": False,
                "match_reasons": [],
                "concerns": [f"Analysis failed: {str(e)}"],
                "recommendation": "SKIP",
                "error": str(e)
            }

    def analyze_batch(
        self,
        jobs: list[Dict],
        user_skills: str,
        user_preferences: Optional[str] = None
    ) -> list[Dict]:
        """Analyze multiple job postings.

        Args:
            jobs: List of job dictionaries with 'title' and 'description'
            user_skills: User's skills
            user_preferences: Optional user preferences

        Returns:
            List of analysis results
        """
        results = []
        for job in jobs:
            analysis = self.analyze_job_relevance(
                job_title=job.get("title", ""),
                job_description=job.get("description", ""),
                user_skills=user_skills,
                user_preferences=user_preferences
            )
            results.append({
                **job,
                "analysis": analysis
            })
        return results
