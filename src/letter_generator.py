"""Generate personalized cover letters using Azure OpenAI."""
import os
import json
from openai import AzureOpenAI
from pathlib import Path
from datetime import datetime

def generate_cover_letter(job_title: str, company: str, job_description: str, user_skills: str) -> str:
    """Generate personalized cover letter."""
    client = AzureOpenAI(
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_key=os.getenv("OPENAI_KEY"),
        api_version="2024-05-01-preview"
    )
    
    user_name = os.getenv("NAME", "Vitalii Berbeha")
    
    prompt = f"""
    Skriv et kort og profesjonelt søknadsbrev på norsk for denne stillingen:
    
    Stilling: {job_title}
    Bedrift: {company}
    Beskrivelse: {job_description[:1000]}
    
    Søkerens ferdigheter: {user_skills}
    Søkerens navn: {user_name}
    
    Krav:
    - Maksimum 150 ord
    - På norsk
    - Profesjonell tone
    - Fokuser på relevante ferdigheter
    - Ikke bruk "Kjære" - start direkt med "Hei"
    """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating letter: {e}")
        return f"Hei,\n\nJeg søker herved på stillingen som {job_title}. Med mine ferdigheter innen {user_skills} mener jeg å være en god kandidat.\n\nMed vennlig hilsen,\n{user_name}"

def save_letter(job_id: int, letter_text: str) -> Path:
    """Save generated letter to file."""
    letters_dir = Path("/app/data/letters")
    letters_dir.mkdir(exist_ok=True)
    
    letter_file = letters_dir / f"{job_id}.txt"
    letter_file.write_text(letter_text, encoding='utf-8')
    
    return letter_file

if __name__ == "__main__":
    # Test letter generation
    test_letter = generate_cover_letter(
        "Python Developer",
        "Test Company AS",
        "Vi søker en utvikler med Python erfaring",
        "Python, FastAPI, SQL, Docker"
    )
    print(test_letter)
