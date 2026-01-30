"""
Gemini AI Service
Integration with Google Gemini for AI counselling and voice onboarding
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Try to import Gemini SDK
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("Warning: google-genai package not found. AI features will use fallback responses.")
    GEMINI_AVAILABLE = False


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = 'gemini-1.5-flash'
        
        if GEMINI_AVAILABLE and self.api_key and self.api_key != "your-gemini-api-key-here":
            self.client = genai.Client(api_key=self.api_key)
    
    def _get_counsellor_system_prompt(self, context: dict) -> str:
        """Generate system prompt with user context"""
        return f"""You are an expert study-abroad AI counsellor. Your name is "AI Counsellor".
You help students make informed decisions about studying abroad.

CURRENT USER CONTEXT:
- Name: {context.get('user_name', 'Student')}
- Current Stage: {self._get_stage_name(context.get('current_stage', 1))}
- Profile: {json.dumps(context.get('profile', {}), indent=2)}
- Shortlisted Universities: {json.dumps(context.get('shortlisted_universities', []), indent=2)}
- Locked Universities: {json.dumps(context.get('locked_universities', []), indent=2)}
- Pending Tasks: {json.dumps(context.get('pending_tasks', []), indent=2)}

YOUR ROLE:
1. Analyze the student's profile - highlight STRENGTHS and GAPS
2. Recommend universities categorized as:
   - DREAM: Highly competitive, low acceptance rate (<15%), student has <50% chance
   - TARGET: Moderate competition, student has 50-70% chance
   - SAFE: Higher acceptance, student has >70% chance
3. Always EXPLAIN WHY a university fits or has risks
4. Suggest actionable next steps based on current stage
5. Be encouraging but REALISTIC about chances
6. When the student agrees to shortlist or lock a university, mention you can do that for them

GREETING RULES:
- If the user says "Hello", "Hi", or a simple greeting: Respond with a SHORT, friendly greeting (1-2 sentences). Do NOT provide a full profile analysis or long list of suggestions unless asked.
- Ask a simple open-ended question like "How can I help you with your study abroad plans today?"

SAFETY & CLARITY RULES:
- **Abuse/Profanity**: If the user uses offensive, abusive, or inappropriate language, strictly refuse to engage with it. Say: "I prefer to keep our conversation professional and focused on your study abroad journey. How can I assist you with your applications?"
- **Gibberish/Unclear**: If the input is random characters (e.g., "adsf", "blah") or unintelligible, politely ask for clarification. Say: "I'm not sure I understood that. Could you please rephrase? I can help with university recommendations, profile analysis, or application tasks."

LANGUAGE & STYLE:
- **Match User's Language (Hinglish)**: If the user speaks in **Hinglish** (Hindi + English mix), reply in the same Hinglish style to be relatable.
  - *Example User*: "Mujhe USA jana hai masters ke liye."
  - *Example Response*: "Bilkul! USA masters ke liye ek great option hai. Aapka current profile dekhte hue, main kuch universities suggest kar sakta hoon."
- **English Default**: If the user speaks English, reply in standard English.
- **Technical Terms**: Keep terms like "GPA", "Intake", "Visa", "University" in English.

RESPONSE GUIDELINES:
- **Be Concise by Default**: Provide short, direct answers. Avoid long, overwhelming paragraphs.
- **On-Demand Details**: Only provide deep details (curriculum, full tuition breakdown, city life) IF the user explicitly asks for them.
- **Responsive**: Answer EXACTLY what the user asks. Do not pivot to unsolicited advice immediately.
- **Categorize**: Keep recommendations clear (Dream/Target/Safe).

HUMAN-LIKE TONE GUIDELINES:
- **Be Empathetic**: Acknowledge the stress/excitement of studying abroad (e.g., "That's a tough choice," or "That sounds exciting!").
- **Natural Language**: Use contractions (I'm, It's, You'll). Avoid "I am", "It is" which sound robotic.
- **No Robot Speak**: Avoid phrases like "As an AI...", "Based on my analysis...". Just say "I think..." or "Here's what I recommend...".
- **Use Name Sparingly**: Use the student's first name occasionally to be warm, but not in every single response.
- **Vary Sentence Length**: Mix short, punchy sentences with longer explanations to sound natural.

RESPONSE FORMAT:
- Talk like a helpful, knowledgeable friend, not a search engine.
- Use bullet points for lists (but don't overuse them).
- Keep initial responses brief (under 150 words preferred).
- If the student needs to take action, be specific but encouraging.

IMPORTANT:
- If the student asks about specific universities, check if they're in the shortlist
- Guide them through the process step by step
- Don't overwhelm with too much information at once
"""
    
    def _get_stage_name(self, stage: int) -> str:
        stages = {
            1: "Building Profile",
            2: "Discovering Universities", 
            3: "Finalizing Universities",
            4: "Preparing Applications"
        }
        return stages.get(stage, "Unknown")
    
    async def get_counsellor_response(self, message: str, context: dict) -> dict:
        """Get AI counsellor response"""
        if not self.client:
            # Fallback response when Gemini not available
            return self._get_fallback_response(message, context)
        
        try:
            system_prompt = self._get_counsellor_system_prompt(context)
            
            # Build conversation with history
            history = context.get('conversation_history', [])
            conversation_text = system_prompt + "\n\nCONVERSATION:\n"
            for msg in history[-6:]:  # Last 6 messages for context
                role = "User" if msg['role'] == 'user' else "Counsellor"
                conversation_text += f"{role}: {msg['content']}\n"
            
            conversation_text += f"User: {message}\nCounsellor:"
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=conversation_text
            )
            
            # Parse response for actions
            response_text = response.text
            actions = self._extract_actions(response_text)
            suggestions = self._generate_suggestions(context)
            
            return {
                "message": response_text,
                "actions": actions,
                "suggestions": suggestions
            }
        except Exception as e:
            print(f"Gemini error: {e}")
            return self._get_fallback_response(message, context)
    
    def _get_fallback_response(self, message: str, context: dict) -> dict:
        """Fallback responses when Gemini is not available"""
        message_lower = message.lower()
        profile = context.get('profile', {})
        stage = context.get('current_stage', 1)
        
        # Context-aware fallback responses
        if 'hello' in message_lower or 'hi' in message_lower:
            name = context.get('user_name', 'there')
            return {
                "message": f"Hello {name}! 👋 I'm your AI Study Abroad Counsellor. I'm here to help you navigate your journey to studying abroad. Based on your profile, you're currently in the **{self._get_stage_name(stage)}** stage. How can I help you today?",
                "suggestions": ["What universities should I apply to?", "Analyze my profile", "What should I do next?"]
            }
        
        if 'universit' in message_lower or 'recommend' in message_lower or 'apply' in message_lower:
            countries = profile.get('preferred_countries', '[]')
            intended = profile.get('intended_degree', 'your degree')
            return {
                "message": f"""Based on your profile, here are my recommendations for {intended} programs:

**🌟 DREAM Universities** (Highly competitive):
- MIT (USA) - Top CS program, 4% acceptance
- Stanford University (USA) - Excellent reputation, 4% acceptance

**🎯 TARGET Universities** (Good fit):
- University of Toronto (Canada) - Strong programs, 43% acceptance
- TU Munich (Germany) - Low tuition, great engineering

**✅ SAFE Universities** (High chance):
- University of British Columbia (Canada) - 52% acceptance
- Arizona State University (USA) - Good acceptance rate

Would you like me to add any of these to your shortlist? Or would you like more details about any specific university?""",
                "actions": [
                    {"type": "shortlist", "label": "Add MIT to shortlist", "university_id": 1},
                    {"type": "shortlist", "label": "Add U of Toronto to shortlist", "university_id": 4}
                ],
                "suggestions": ["Tell me more about MIT", "Add University of Toronto to shortlist", "What are my chances?"]
            }
        
        if 'profile' in message_lower or 'strength' in message_lower or 'analyz' in message_lower:
            gpa = profile.get('gpa', 'not provided')
            ielts = profile.get('ielts_status', 'not started')
            sop = profile.get('sop_status', 'not started')
            
            return {
                "message": f"""Here's my analysis of your profile:

**📚 Academic Background**
- GPA: {gpa} {'✅ Competitive' if gpa and gpa >= 3.5 else '⚠️ Consider highlighting other strengths'}
- Degree: {profile.get('degree', 'Not specified')} in {profile.get('major', 'Not specified')}

**📝 Test Readiness**
- IELTS/TOEFL: {ielts} {'✅ Ready' if ielts == 'completed' else '⚠️ Priority action needed'}
- GRE/GMAT: {profile.get('gre_status', 'not started')}

**📄 Application Materials**
- SOP Status: {sop} {'✅ Good progress' if sop == 'ready' else '📝 Needs attention'}

**💰 Budget**
- Range: ${profile.get('budget_min', 0):,} - ${profile.get('budget_max', 0):,}/year
- Funding: {profile.get('funding_type', 'Not specified')}

**Recommended Next Steps:**
1. {'Complete IELTS preparation' if ielts != 'completed' else '✅ IELTS done'}
2. {'Start working on your SOP' if sop != 'ready' else '✅ SOP ready'}
3. Explore university options that match your profile

Would you like specific university recommendations?""",
                "suggestions": ["Recommend universities", "What should I prepare next?", "Help me with SOP"]
            }
        
        if 'next' in message_lower or 'should' in message_lower or 'step' in message_lower:
            return {
                "message": f"""Based on your current stage (**{self._get_stage_name(stage)}**), here's what you should focus on:

{self._get_stage_advice(stage, profile)}

Would you like help with any of these?""",
                "suggestions": ["Show my pending tasks", "Recommend universities", "Analyze my profile"]
            }
        
        if 'shortlist' in message_lower or 'add' in message_lower:
            return {
                "message": "I can help you shortlist universities! Tell me which university you'd like to add, or ask me for recommendations based on your profile.",
                "suggestions": ["Recommend universities for me", "Show my current shortlist", "What's the difference between Dream and Safe?"]
            }
        
        # Default response
        return {
            "message": f"""I'm here to help with your study abroad journey! As your AI counsellor, I can:

🎓 **Recommend universities** based on your profile
📊 **Analyze your profile** strengths and gaps
📝 **Guide you** through the application process
✅ **Create tasks** to keep you on track

What would you like to explore? You're currently in the **{self._get_stage_name(stage)}** stage.""",
            "suggestions": ["Recommend universities", "Analyze my profile", "What should I do next?"]
        }
    
    def _get_stage_advice(self, stage: int, profile: dict) -> str:
        if stage == 1:
            return """**Stage 1: Complete Your Profile**
- Fill in your academic background
- Set your study goals and preferences  
- Define your budget range
- Update exam readiness status"""
        
        elif stage == 2:
            return """**Stage 2: Discover Universities**
- Browse universities matching your profile
- Consider Dream, Target, and Safe options
- Research program details and requirements
- Start shortlisting potential matches"""
        
        elif stage == 3:
            return """**Stage 3: Finalize Your List**
- Review your shortlisted universities
- Compare costs, deadlines, and requirements
- Lock at least one university to proceed
- This commits you to the application stage"""
        
        elif stage == 4:
            ielts = profile.get('ielts_status', 'not_started')
            sop = profile.get('sop_status', 'not_started')
            tasks = []
            if ielts != 'completed':
                tasks.append("- ⚠️ Complete IELTS/TOEFL exam")
            if sop != 'ready':
                tasks.append("- ⚠️ Finalize your Statement of Purpose")
            tasks.extend([
                "- Gather official transcripts",
                "- Request recommendation letters",
                "- Prepare application documents",
                "- Submit applications before deadlines"
            ])
            return "**Stage 4: Application Preparation**\n" + "\n".join(tasks)
        
        return "Keep exploring and let me know how I can help!"
    
    def _extract_actions(self, response: str) -> list:
        """Extract actionable items from response"""
        # Simple action extraction - can be enhanced
        actions = []
        if 'shortlist' in response.lower() and 'add' in response.lower():
            actions.append({"type": "suggest_shortlist", "label": "View recommendations"})
        return actions if actions else None
    
    def _generate_suggestions(self, context: dict) -> list:
        """Generate follow-up suggestions"""
        stage = context.get('current_stage', 1)
        suggestions = []
        
        if stage == 2:
            suggestions = ["Recommend universities", "Show universities in USA", "What's my fit score?"]
        elif stage == 3:
            suggestions = ["Compare my shortlist", "Lock a university", "Show deadline calendar"]
        elif stage == 4:
            suggestions = ["Show application checklist", "Review my tasks", "Help with SOP"]
        else:
            suggestions = ["Analyze my profile", "What should I prepare?", "Show popular destinations"]
        
        return suggestions
    
    async def process_voice_onboarding(
        self, 
        transcript: str, 
        current_step: Optional[str],
        current_profile: dict
    ) -> dict:
        """Process voice onboarding transcript and extract data"""
        
        if not self.client:
            return self._process_voice_fallback(transcript, current_step, current_profile)
        
        try:
            prompt = f"""You are an AI assistant helping with voice-based onboarding for a study abroad platform.

Current onboarding step: {current_step or 'start'}
Current profile data: {json.dumps(current_profile, indent=2)}

User said: "{transcript}"

Your tasks:
1. Extract any relevant profile information from what the user said
2. Generate a friendly spoken response
3. Determine the next step

ONBOARDING STEPS:
1. education_level - Ask about current education (high school, bachelor's, master's)
2. degree_major - Ask about their degree and major
3. graduation_year - Ask when they graduate/graduated
4. gpa - Ask about their GPA (optional)
5. intended_degree - What degree they want to pursue abroad
6. field_of_study - What field they want to study
7. preferred_countries - Which countries interest them
8. target_intake - When do they want to start (Fall 2025, Spring 2026, etc.)
9. budget - Their budget range per year
10. exams - IELTS/TOEFL/GRE status
11. complete - Summary and completion

Respond in this JSON format:
{{
    "response_text": "Your spoken response to the user",
    "next_step": "The next step to ask about",
    "extracted_data": {{
        "field_name": "extracted_value"
    }},
    "is_complete": false
}}

Extract data that matches these fields:
- education_level, degree, major, graduation_year, gpa
- intended_degree, field_of_study, target_intake, preferred_countries (as JSON array string)
- budget_min, budget_max, funding_type
- ielts_status, ielts_score, gre_status, gre_score, sop_status
"""
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                response_text = response.text
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return self._process_voice_fallback(transcript, current_step, current_profile)
                
        except Exception as e:
            print(f"Gemini voice error: {e}")
            return self._process_voice_fallback(transcript, current_step, current_profile)
    
    def _process_voice_fallback(
        self,
        transcript: str,
        current_step: Optional[str],
        current_profile: dict
    ) -> dict:
        """Fallback voice processing without AI"""
        
        transcript_lower = transcript.lower()
        extracted = {}
        
        # Step flow
        steps = [
            'start', 'education_level', 'degree_major', 'graduation_year',
            'intended_degree', 'field_of_study', 'preferred_countries',
            'target_intake', 'budget', 'exams', 'complete'
        ]
        
        current_idx = steps.index(current_step) if current_step in steps else 0
        
        # Simple extraction based on current step
        if current_step == 'start' or not current_step:
            return {
                "response_text": "Hi! I'm your AI counsellor. Let's set up your profile together. What's your current education level? Are you in high school, doing a bachelor's, or have you completed a master's?",
                "next_step": "education_level",
                "extracted_data": {},
                "is_complete": False
            }
        
        elif current_step == 'education_level':
            if 'bachelor' in transcript_lower:
                extracted['education_level'] = 'bachelors'
            elif 'master' in transcript_lower:
                extracted['education_level'] = 'masters'
            elif 'high school' in transcript_lower or 'school' in transcript_lower:
                extracted['education_level'] = 'high_school'
            
            return {
                "response_text": "Great! What's your degree and major? For example, Bachelor's in Computer Science.",
                "next_step": "degree_major",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'degree_major':
            # Extract degree and major from transcript
            if 'computer' in transcript_lower:
                extracted['major'] = 'Computer Science'
            elif 'business' in transcript_lower:
                extracted['major'] = 'Business Administration'
            elif 'engineer' in transcript_lower:
                extracted['major'] = 'Engineering'
            
            return {
                "response_text": "Good! What year are you graduating or did you graduate?",
                "next_step": "graduation_year",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'graduation_year':
            # Extract year
            import re
            years = re.findall(r'20\d{2}', transcript)
            if years:
                extracted['graduation_year'] = int(years[0])
            
            return {
                "response_text": "Perfect! What degree are you planning to pursue abroad? Bachelor's, Master's, MBA, or PhD?",
                "next_step": "intended_degree",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'intended_degree':
            if 'master' in transcript_lower or 'ms' in transcript_lower:
                extracted['intended_degree'] = 'masters'
            elif 'mba' in transcript_lower:
                extracted['intended_degree'] = 'mba'
            elif 'phd' in transcript_lower or 'doctor' in transcript_lower:
                extracted['intended_degree'] = 'phd'
            elif 'bachelor' in transcript_lower:
                extracted['intended_degree'] = 'bachelors'
            
            return {
                "response_text": "What field would you like to study?",
                "next_step": "field_of_study",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'field_of_study':
            extracted['field_of_study'] = transcript.strip().title()
            
            return {
                "response_text": "Which countries are you interested in? You can mention multiple, like USA, Canada, or UK.",
                "next_step": "preferred_countries",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'preferred_countries':
            countries = []
            if 'usa' in transcript_lower or 'america' in transcript_lower or 'united states' in transcript_lower:
                countries.append('USA')
            if 'canada' in transcript_lower:
                countries.append('Canada')
            if 'uk' in transcript_lower or 'britain' in transcript_lower or 'england' in transcript_lower:
                countries.append('UK')
            if 'germany' in transcript_lower:
                countries.append('Germany')
            if 'australia' in transcript_lower:
                countries.append('Australia')
            
            if countries:
                extracted['preferred_countries'] = json.dumps(countries)
            
            return {
                "response_text": "When do you want to start your studies? Fall 2025, Spring 2026, or later?",
                "next_step": "target_intake",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'target_intake':
            if 'fall' in transcript_lower and '2025' in transcript:
                extracted['target_intake'] = 'fall_2025'
            elif 'spring' in transcript_lower and '2026' in transcript:
                extracted['target_intake'] = 'spring_2026'
            elif 'fall' in transcript_lower and '2026' in transcript:
                extracted['target_intake'] = 'fall_2026'
            
            return {
                "response_text": "What's your budget per year for tuition? You can give me a range.",
                "next_step": "budget",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'budget':
            import re
            numbers = re.findall(r'\d+', transcript.replace(',', ''))
            if len(numbers) >= 2:
                extracted['budget_min'] = int(numbers[0]) * (1000 if int(numbers[0]) < 100 else 1)
                extracted['budget_max'] = int(numbers[1]) * (1000 if int(numbers[1]) < 100 else 1)
            elif len(numbers) == 1:
                extracted['budget_max'] = int(numbers[0]) * (1000 if int(numbers[0]) < 100 else 1)
                extracted['budget_min'] = 0
            
            return {
                "response_text": "Last question - have you taken IELTS or TOEFL? If yes, what was your score?",
                "next_step": "exams",
                "extracted_data": extracted,
                "is_complete": False
            }
        
        elif current_step == 'exams':
            if 'not' in transcript_lower or 'no' in transcript_lower:
                extracted['ielts_status'] = 'not_started'
            elif 'preparing' in transcript_lower or 'studying' in transcript_lower:
                extracted['ielts_status'] = 'preparing'
            else:
                extracted['ielts_status'] = 'completed'
                # Try to extract score
                import re
                scores = re.findall(r'(\d\.?\d?)', transcript)
                for score in scores:
                    if 5 <= float(score) <= 9:
                        extracted['ielts_score'] = float(score)
                        break
            
            return {
                "response_text": "Excellent! I now have all the information I need. Your profile is complete! You can now access the AI Counsellor for personalized university recommendations. Would you like to proceed to your dashboard?",
                "next_step": "complete",
                "extracted_data": extracted,
                "is_complete": True
            }
        
        # Default
        return {
            "response_text": "I didn't quite catch that. Could you please repeat?",
            "next_step": current_step,
            "extracted_data": {},
            "is_complete": False
        }
