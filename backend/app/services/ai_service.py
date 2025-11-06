"""AI service for job analysis using Azure OpenAI"""
import json
import re
from typing import Dict, Any
from openai import AzureOpenAI
from app.config import settings


class AIService:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT

    def clean_json_response(self, response: str) -> str:
        """Clean markdown formatting from JSON response."""
        # Remove markdown code blocks
        response = re.sub(r'```json\n?', '', response)
        response = re.sub(r'```\n?', '', response)
        response = response.strip()
        return response

    async def analyze_job_relevance(
        self,
        job_title: str,
        job_description: str,
        company: str,
        location: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze if job is relevant for the user based on their profile.

        Args:
            job_title: Title of the job posting
            job_description: Full job description
            company: Company name
            location: Job location
            user_profile: User's profile with skills, experience, etc.

        Returns:
            Dictionary with relevance score, match reasons, concerns, and recommendation
        """
        # Extract user skills and preferences from profile
        user_skills = user_profile.get("skills", "")
        user_experience = user_profile.get("experience", "")
        preferred_locations = user_profile.get("preferred_locations", [])

        # Build comprehensive user context
        user_context = f"""
        Skills: {user_skills}
        Experience: {user_experience}
        Preferred Locations: {', '.join(preferred_locations) if preferred_locations else 'Any'}
        """

        prompt = f"""
You are an expert job matcher helping a job seeker in Norway. Analyze this job posting and determine its relevance.

**Candidate Profile:**
{user_context}

**Job Details:**
- Title: {job_title}
- Company: {company}
- Location: {location}
- Description: {job_description[:2000]}

Analyze the job and provide a detailed assessment. Consider:
1. Skills match (how many required skills does the candidate have?)
2. Experience level alignment
3. Location compatibility (Norwegian jobs only)
4. Career growth potential
5. Any red flags or concerns

Respond with ONLY valid JSON, no markdown formatting:
{{
    "relevance_score": 85,
    "is_relevant": true,
    "match_reasons": [
        "Strong match on Python and FastAPI skills",
        "Location aligns with preferences",
        "Company offers growth opportunities"
    ],
    "concerns": [
        "Requires 5 years experience, candidate has 3"
    ],
    "recommendation": "APPLY",
    "salary_estimate": "500,000 - 700,000 NOK",
    "key_requirements": ["Python", "FastAPI", "Docker"],
    "missing_skills": ["Kubernetes"]
}}

Recommendation must be one of: APPLY, REVIEW, SKIP
Relevance score: 0-100 (70+ is APPLY, 50-69 is REVIEW, <50 is SKIP)
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional job matching AI assistant. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )

            raw_response = response.choices[0].message.content
            cleaned_response = self.clean_json_response(raw_response)

            result = json.loads(cleaned_response)

            # Ensure all required fields are present
            result.setdefault("relevance_score", 0)
            result.setdefault("is_relevant", False)
            result.setdefault("match_reasons", [])
            result.setdefault("concerns", [])
            result.setdefault("recommendation", "SKIP")

            return result

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {raw_response[:500]}...")
            return {
                "relevance_score": 0,
                "is_relevant": False,
                "match_reasons": [],
                "concerns": ["AI analysis failed - JSON parsing error"],
                "recommendation": "SKIP"
            }
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {
                "relevance_score": 0,
                "is_relevant": False,
                "match_reasons": [],
                "concerns": [f"AI analysis error: {str(e)}"],
                "recommendation": "SKIP"
            }

    async def generate_cover_letter(
        self,
        job_title: str,
        job_description: str,
        company: str,
        user_profile: Dict[str, Any],
        language: str = "no"
    ) -> str:
        """
        Generate a personalized cover letter in Norwegian or English.

        Args:
            job_title: Job title
            job_description: Job description
            company: Company name
            user_profile: User profile with experience and skills
            language: Language code ('no' for Norwegian, 'en' for English)

        Returns:
            Generated cover letter text
        """
        full_name = user_profile.get("full_name", "")
        phone = user_profile.get("phone", "")
        email = user_profile.get("email", "")
        experience = user_profile.get("experience", "")
        skills = user_profile.get("skills", "")

        lang_instruction = "Norwegian (bokmål)" if language == "no" else "English"

        prompt = f"""
Write a professional cover letter in {lang_instruction} for this job application.

**Applicant Information:**
Name: {full_name}
Phone: {phone}
Email: {email}
Experience: {experience}
Skills: {skills}

**Job Information:**
Title: {job_title}
Company: {company}
Description: {job_description[:1500]}

Write a compelling, professional cover letter that:
1. Opens with enthusiasm for the specific role
2. Highlights relevant experience and skills that match the job requirements
3. Demonstrates knowledge of the company (if possible from context)
4. Explains why this is a good mutual fit
5. Closes with a call to action

Keep it concise (250-350 words), professional, and personalized. Use proper Norwegian business letter format if language is Norwegian.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional cover letter writer helping job seekers in Norway. Write in {lang_instruction}."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            cover_letter = response.choices[0].message.content.strip()
            return cover_letter

        except Exception as e:
            print(f"Cover letter generation error: {e}")
            return f"Error generating cover letter: {str(e)}"
