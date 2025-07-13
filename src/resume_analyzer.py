"""Resume analyzer for multiple file formats using Azure OpenAI."""
import os
import json
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2
import docx
from openai import AzureOpenAI

class ResumeAnalyzer:
    def __init__(self):
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            api_key=os.getenv("OPENAI_KEY"),
            api_version="2024-05-01-preview"
        )
        self.resume_dir = Path("/app/data/resumes")
        self.resume_dir.mkdir(exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            print(f"❌ Error reading PDF {pdf_path}: {e}")
            return ""

    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from Word document."""
        try:
            doc = docx.Document(docx_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"❌ Error reading DOCX {docx_path}: {e}")
            return ""

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats."""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self.extract_text_from_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.docx', '.doc']:
            return self.extract_text_from_docx(str(file_path))
        elif file_path.suffix.lower() == '.txt':
            return file_path.read_text(encoding='utf-8')
        else:
            print(f"❌ Unsupported file format: {file_path.suffix}")
            return ""

    def analyze_single_resume(self, resume_text: str, filename: str) -> Dict[str, Any]:
        """Analyze single resume using Azure OpenAI."""
        prompt = f"""
        Analyze this resume and extract structured information. The resume is from file: {filename}

        Resume text:
        {resume_text[:4000]}

        Extract and return ONLY valid JSON with this structure:
        {{
            "personal_info": {{
                "name": "Full Name",
                "email": "email@example.com",
                "phone": "phone number",
                "location": "current location"
            }},
            "professional_summary": "Brief professional summary",
            "work_experience": [
                {{
                    "company": "Company Name",
                    "position": "Job Title",
                    "duration": "2020-2023",
                    "responsibilities": ["responsibility1", "responsibility2"]
                }}
            ],
            "education": [
                {{
                    "degree": "Degree Name",
                    "institution": "University Name",
                    "year": "2020"
                }}
            ],
            "skills": {{
                "technical": ["skill1", "skill2"],
                "languages": ["Norwegian", "English"],
                "soft_skills": ["leadership", "communication"]
            }},
            "certifications": ["cert1", "cert2"],
            "career_objective": "What type of job they're seeking"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # Clean JSON response
            result_text = result_text.replace('```json\n', '').replace('\n```', '').strip()
            
            result = json.loads(result_text)
            result['source_file'] = filename
            
            print(f"✅ Analyzed resume: {filename}")
            return result
            
        except Exception as e:
            print(f"❌ Error analyzing resume {filename}: {e}")
            return {"error": str(e), "source_file": filename}

    def combine_multiple_resumes(self, resume_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple resume analyses into unified profile."""
        if not resume_analyses:
            return {}

        # Filter out errored analyses
        valid_analyses = [r for r in resume_analyses if 'error' not in r]
        
        if not valid_analyses:
            return {"error": "No valid resume analyses"}

        combine_prompt = f"""
        I have {len(valid_analyses)} resume analyses from different files. 
        Combine them into ONE comprehensive professional profile.
        
        Resume analyses:
        {json.dumps(valid_analyses, indent=2)[:6000]}

        Create a unified profile with ONLY valid JSON:
        {{
            "unified_profile": {{
                "personal_info": {{"name": "...", "email": "...", "phone": "...", "location": "..."}},
                "comprehensive_summary": "Detailed professional summary combining all experiences",
                "total_experience_years": 5,
                "all_work_experience": [...],
                "all_education": [...],
                "comprehensive_skills": {{
                    "technical": [...],
                    "languages": [...],
                    "soft_skills": [...],
                    "industry_knowledge": [...]
                }},
                "all_certifications": [...],
                "career_preferences": "What type of roles and industries they're targeting",
                "key_strengths": ["strength1", "strength2", "strength3"],
                "adaptability_areas": ["areas where they could adapt to new roles"]
            }},
            "resume_sources": ["file1.pdf", "file2.docx"],
            "analysis_confidence": "high/medium/low"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4"),
                messages=[{"role": "user", "content": combine_prompt}],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            result_text = result_text.replace('```json\n', '').replace('\n```', '').strip()
            
            combined_profile = json.loads(result_text)
            
            print(f"✅ Combined {len(valid_analyses)} resumes into unified profile")
            return combined_profile
            
        except Exception as e:
            print(f"❌ Error combining resumes: {e}")
            return {"error": str(e)}

    def process_all_resumes(self) -> Dict[str, Any]:
        """Process all resume files and create unified profile."""
        print("🔍 Scanning for resume files...")
        
        # Find all resume files
        resume_files = []
        for pattern in ['*.pdf', '*.docx', '*.doc', '*.txt']:
            resume_files.extend(self.resume_dir.glob(pattern))
        
        if not resume_files:
            print("❌ No resume files found!")
            print(f"📁 Please add resume files to: {self.resume_dir}")
            return {"error": "No resume files found"}
        
        print(f"📄 Found {len(resume_files)} resume files:")
        for file in resume_files:
            print(f"  - {file.name}")
        
        # Analyze each resume
        resume_analyses = []
        for resume_file in resume_files:
            print(f"\n📖 Processing: {resume_file.name}")
            
            # Extract text
            resume_text = self.extract_text_from_file(str(resume_file))
            if not resume_text:
                continue
            
            print(f"📝 Extracted {len(resume_text)} characters")
            
            # Analyze with AI
            analysis = self.analyze_single_resume(resume_text, resume_file.name)
            resume_analyses.append(analysis)
        
        # Combine all analyses
        print(f"\n🔄 Combining {len(resume_analyses)} resume analyses...")
        unified_profile = self.combine_multiple_resumes(resume_analyses)
        
        # Save unified profile
        profile_file = self.resume_dir / "unified_profile.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(unified_profile, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved unified profile to: {profile_file}")
        return unified_profile

if __name__ == "__main__":
    analyzer = ResumeAnalyzer()
    profile = analyzer.process_all_resumes()
    print("\n📊 UNIFIED PROFILE SUMMARY:")
    if 'error' not in profile and 'unified_profile' in profile:
        up = profile['unified_profile']
        print(f"👤 Name: {up.get('personal_info', {}).get('name', 'N/A')}")
        print(f"💼 Experience: {up.get('total_experience_years', 'N/A')} years")
        print(f"🎯 Career focus: {up.get('career_preferences', 'N/A')[:100]}...")
    else:
        print(f"❌ Error: {profile.get('error', 'Unknown error')}")
