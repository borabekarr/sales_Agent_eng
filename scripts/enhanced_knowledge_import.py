#!/usr/bin/env python3
"""
Enhanced Sales Knowledge Base Import
This script provides better extraction of sales scripts, psychology patterns, and objection responses.
"""

import os
import sys
import re
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install supabase")
    from supabase import create_client, Client

class EnhancedKnowledgeImporter:
    """Enhanced importer with better content extraction"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.knowledge_dir = "../supabase_db_files"

    def read_markdown_file(self, filepath: str) -> str:
        """Read and return content of a markdown file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading {filepath}: {str(e)}")
            return ""

    def extract_meeting_script_components(self, content: str) -> List[Dict[str, Any]]:
        """Extract specific script components from Meeting Script"""
        scripts = []
        
        # Define specific script sections with their patterns
        script_sections = {
            "opening_intro": {
                "pattern": r"Now, you're here because.*?(?=\*\*So our promise is|$)",
                "name": "Opening Introduction",
                "category": "opening",
                "agent": "OpeningAgent"
            },
            "value_proposition": {
                "pattern": r"\*\*So our promise is.*?(?=\*\*And if you don't know|$)",
                "name": "Value Proposition",
                "category": "opening", 
                "agent": "OpeningAgent"
            },
            "credibility_statement": {
                "pattern": r"\*\*And if you don't know.*?(?=So, here's our certificates|$)",
                "name": "Credibility Statement",
                "category": "opening",
                "agent": "OpeningAgent"
            },
            "pain_calculation_script": {
                "pattern": r"To estimate your approximate loss.*?(?=This result probably|$)",
                "name": "Pain Calculation Framework",
                "category": "discovery",
                "agent": "DiscoveryAgent"
            },
            "pain_revelation": {
                "pattern": r"This result probably surprising.*?(?=Okay\. Now|$)",
                "name": "Pain Point Revelation",
                "category": "discovery",
                "agent": "DiscoveryAgent"
            },
            "solution_presentation": {
                "pattern": r"With this solution, you can still get back.*?(?=And we do that by|$)",
                "name": "Solution Presentation",
                "category": "pitch",
                "agent": "PitchAgent"
            },
            "ai_system_explanation": {
                "pattern": r"And we do that by injecting humanoid AI.*?(?=And unlike the regular AI|$)",
                "name": "AI System Explanation",
                "category": "pitch",
                "agent": "PitchAgent"
            },
            "pricing_framework": {
                "pattern": r"The normal amount of required investment.*?(?=And we can say|$)",
                "name": "Pricing Framework",
                "category": "pricing",
                "agent": "PitchAgent"
            },
            "value_justification": {
                "pattern": r"And we can say that this is a very good deal.*?(?=So… At the end|$)",
                "name": "Value Justification",
                "category": "pricing",
                "agent": "PitchAgent"
            },
            "closing_summary": {
                "pattern": r"So… At the end of the 30 days.*?(?=Or, in the worst case|$)",
                "name": "Closing Summary",
                "category": "closing",
                "agent": "ClosingAgent"
            }
        }
        
        for script_id, config in script_sections.items():
            matches = re.findall(config["pattern"], content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                clean_script = self.clean_script_content(match)
                if len(clean_script) > 50:  # Only add substantial scripts
                    scripts.append({
                        "script_id": f"meeting_{script_id}_{uuid.uuid4().hex[:8]}",
                        "script_name": config["name"],
                        "script_category": config["category"],
                        "script_content": clean_script,
                        "intended_agent": config["agent"],
                        "usage_context": f"Use during {config['category']} phase",
                        "script_variables": json.dumps(self.extract_variables(clean_script))
                    })
        
        return scripts

    def clean_script_content(self, content: str) -> str:
        """Clean and format script content"""
        # Remove excessive markdown formatting
        content = re.sub(r'\*\*', '', content)
        content = re.sub(r'\\', '', content)
        # Clean up spacing
        content = re.sub(r'\n\s*\n', '\n\n', content)
        return content.strip()

    def extract_variables(self, content: str) -> List[str]:
        """Extract variables from script content"""
        variables = []
        # Find [variable] patterns
        variables.extend(re.findall(r'\[([^\]]+)\]', content))
        # Find $$ patterns
        variables.extend(re.findall(r'\$+', content))
        # Find %%% patterns
        variables.extend(re.findall(r'%+', content))
        return list(set(variables))

    def extract_objection_responses_enhanced(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Enhanced objection response extraction"""
        objections = []
        
        if "handling_objections" in filename.lower():
            # Extract specific objection handling patterns from the comprehensive file
            objection_patterns = [
                {
                    "objection": "I have to speak to my partner",
                    "response": "Listen, I understand you have to speak to your partner, but the beauty of this program is... [this should be positioned as a decision they don't need to talk to their partner about]",
                    "category": "authority",
                    "framework": "deflection_reframe"
                },
                {
                    "objection": "It's too expensive",
                    "response": "Let's say you sign up for this program and I am totally wrong and the system doesn't meet your needs. Is the cost of the system gonna put you in the poorhouse? [When they say no] Create a picture in their mind of massive benefits from doing business with you.",
                    "category": "price",
                    "framework": "risk_minimization"
                },
                {
                    "objection": "I need to think about it",
                    "response": "I understand you want to think about it. But let me ask you this - what exactly do you need to think about? We've covered [recap key points]. The question isn't whether this works - we've proven that. The question is whether you're ready to stop struggling with [their pain] and start getting the results you deserve.",
                    "category": "decision_delay", 
                    "framework": "pain_amplification"
                }
            ]
            
            # Also extract trigger words and patterns
            trigger_sections = content.split("TRIGGER WORDS")
            if len(trigger_sections) > 1:
                trigger_content = trigger_sections[1]
                # Extract individual trigger words and their explanations
                trigger_patterns = re.findall(r'(\d+\)\s*"([^"]+)".*?)(?=\d+\)|$)', trigger_content, re.DOTALL)
                
                for pattern in trigger_patterns:
                    trigger_text = pattern[1] if len(pattern) > 1 else pattern[0]
                    objections.append({
                        "objection_id": f"trigger_{uuid.uuid4().hex[:8]}",
                        "objection_text": f"Use trigger word: {trigger_text}",
                        "objection_category": "psychology_pattern",
                        "response_script": pattern[0] if pattern else "",
                        "response_framework": "trigger_word_usage",
                        "agent_notes": "Psychological trigger word for influence"
                    })
            
            # Add the predefined objections
            for obj in objection_patterns:
                objections.append({
                    "objection_id": f"obj_{uuid.uuid4().hex[:8]}",
                    "objection_text": obj["objection"],
                    "objection_category": obj["category"],
                    "response_script": obj["response"],
                    "response_framework": obj["framework"],
                    "agent_notes": "Core objection handling script"
                })
        
        elif "rebuttal" in filename.lower() or "specific_objections" in filename.lower():
            # Extract from other objection files
            sections = content.split('\n\n')
            current_objection = None
            current_response = ""
            
            for section in sections:
                if self.looks_like_objection(section):
                    if current_objection and current_response:
                        objections.append({
                            "objection_id": f"obj_{uuid.uuid4().hex[:8]}",
                            "objection_text": current_objection,
                            "objection_category": self.categorize_objection(current_objection),
                            "response_script": current_response.strip(),
                            "response_framework": "direct_response",
                            "agent_notes": f"Extracted from {filename}"
                        })
                    current_objection = section.strip()
                    current_response = ""
                elif current_objection and len(section.strip()) > 10:
                    current_response += section + "\n\n"
        
        return objections

    def looks_like_objection(self, text: str) -> bool:
        """Determine if text looks like an objection"""
        objection_indicators = [
            "i don't", "i can't", "i need to", "i have to", "too expensive",
            "not interested", "no budget", "not now", "think about",
            "consult", "discuss", "partner", "boss"
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in objection_indicators)

    def categorize_objection(self, objection_text: str) -> str:
        """Categorize objection based on content"""
        objection_lower = objection_text.lower()
        
        if any(word in objection_lower for word in ["price", "expensive", "cost", "money", "afford", "budget"]):
            return "price"
        elif any(word in objection_lower for word in ["time", "busy", "schedule"]):
            return "time"
        elif any(word in objection_lower for word in ["think", "consider", "decision"]):
            return "decision_delay"
        elif any(word in objection_lower for word in ["partner", "spouse", "discuss", "consult", "boss"]):
            return "authority"
        elif any(word in objection_lower for word in ["competitor", "another", "already", "someone else"]):
            return "competition"
        elif any(word in objection_lower for word in ["trust", "sure", "guarantee", "proof"]):
            return "trust"
        else:
            return "general"

    def extract_psychology_patterns_enhanced(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Enhanced psychology pattern extraction"""
        patterns = []
        
        if "handling_objections" in filename.lower():
            # Extract trigger words
            trigger_sections = content.split("TRIGGER WORDS")
            if len(trigger_sections) > 1:
                trigger_content = trigger_sections[1]
                
                # Extract individual trigger words
                trigger_items = re.findall(r'(\d+\)\s*"([^"]+)".*?)(?=\d+\)|$)', trigger_content, re.DOTALL)
                
                for item in trigger_items:
                    if len(item) >= 2:
                        trigger_word = item[1]
                        explanation = item[0]
                        
                        patterns.append({
                            "pattern_id": f"trigger_{uuid.uuid4().hex[:8]}",
                            "pattern_name": f"Trigger Word: {trigger_word}",
                            "pattern_category": "trigger_words",
                            "description": explanation,
                            "trigger_phrases": json.dumps([trigger_word]),
                            "psychological_principle": self.extract_principle_from_explanation(explanation)
                        })
        
        elif "trial_technique" in filename.lower() or "psychology" in filename.lower():
            # Extract psychological techniques
            sections = content.split('\n\n')
            
            for section in sections:
                if len(section.strip()) > 100 and self.contains_psychology_keywords(section):
                    patterns.append({
                        "pattern_id": f"psych_{uuid.uuid4().hex[:8]}",
                        "pattern_name": self.extract_pattern_title(section),
                        "pattern_category": "influence_technique",
                        "description": section.strip(),
                        "trigger_phrases": json.dumps(self.extract_quoted_phrases(section)),
                        "psychological_principle": self.extract_principle_from_explanation(section)
                    })
        
        elif "agent_persona" in filename.lower():
            # Extract persona traits as psychology patterns
            persona_items = re.findall(r'(\d+\).*?)(?=\d+\)|$)', content, re.DOTALL)
            
            for item in persona_items:
                if len(item.strip()) > 50:
                    patterns.append({
                        "pattern_id": f"persona_{uuid.uuid4().hex[:8]}",
                        "pattern_name": self.extract_pattern_title(item),
                        "pattern_category": "agent_behavior",
                        "description": item.strip(),
                        "trigger_phrases": json.dumps(self.extract_quoted_phrases(item)),
                        "psychological_principle": "Agent persona and behavior guideline"
                    })
        
        return patterns

    def contains_psychology_keywords(self, text: str) -> bool:
        """Check if text contains psychology-related keywords"""
        keywords = [
            "psychology", "influence", "persuasion", "trigger", "pattern",
            "technique", "behavior", "emotional", "rapport", "trust",
            "authority", "conviction", "confidence"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def extract_pattern_title(self, content: str) -> str:
        """Extract a title for the psychology pattern"""
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        # Clean up the first line
        title = re.sub(r'^\d+\)\s*', '', first_line)
        title = re.sub(r'^[*#]+\s*', '', title)
        title = re.sub(r'\*\*', '', title)
        
        if len(title) > 80:
            title = title[:80] + "..."
        
        return title if title else "Psychology Pattern"

    def extract_quoted_phrases(self, content: str) -> List[str]:
        """Extract quoted phrases from content"""
        phrases = []
        phrases.extend(re.findall(r'"([^"]+)"', content))
        phrases.extend(re.findall(r"'([^']+)'", content))
        return [phrase for phrase in phrases if len(phrase.split()) <= 15]

    def extract_principle_from_explanation(self, content: str) -> str:
        """Extract psychological principle from explanation"""
        # Look for explanatory sentences
        sentences = content.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in [
                "because", "psychology", "principle", "works", "effect",
                "influence", "persuade", "emotional", "subconscious"
            ]):
                return sentence.strip()
        return "Psychological influence technique"

    def run_enhanced_import(self):
        """Run the enhanced import focusing on missing content"""
        print("🚀 Running Enhanced Knowledge Import...")
        
        # Focus on Meeting Script for sales scripts
        meeting_script_path = os.path.join(self.knowledge_dir, "Meeting Script.md")
        if os.path.exists(meeting_script_path):
            print("📝 Extracting sales scripts from Meeting Script...")
            content = self.read_markdown_file(meeting_script_path)
            scripts = self.extract_meeting_script_components(content)
            
            for script in scripts:
                try:
                    self.supabase.table("sales_scripts").insert(script).execute()
                    print(f"✅ Added script: {script['script_name']}")
                except Exception as e:
                    print(f"❌ Error adding script: {str(e)}")
        
        # Focus on objection handling files
        objection_files = [
            "HANDLING OBJECTIONS.md",
            "Rebuttal Vault.md", 
            "Specific Objections.md"
        ]
        
        for filename in objection_files:
            filepath = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(filepath):
                print(f"🛡️  Extracting objections from {filename}...")
                content = self.read_markdown_file(filepath)
                objections = self.extract_objection_responses_enhanced(content, filename)
                
                for objection in objections:
                    try:
                        self.supabase.table("objection_responses").insert(objection).execute()
                        print(f"✅ Added objection response: {objection['objection_category']}")
                    except Exception as e:
                        print(f"❌ Error adding objection: {str(e)}")
        
        # Focus on psychology pattern files
        psychology_files = [
            "HANDLING OBJECTIONS.md",
            "The Trial Technique (Indirect Sales Tactiques).md",
            "agent_persona.md"
        ]
        
        for filename in psychology_files:
            filepath = os.path.join(self.knowledge_dir, filename)
            if os.path.exists(filepath):
                print(f"🧠 Extracting psychology patterns from {filename}...")
                content = self.read_markdown_file(filepath)
                patterns = self.extract_psychology_patterns_enhanced(content, filename)
                
                for pattern in patterns:
                    try:
                        self.supabase.table("psychology_patterns").insert(pattern).execute()
                        print(f"✅ Added psychology pattern: {pattern['pattern_name']}")
                    except Exception as e:
                        print(f"❌ Error adding pattern: {str(e)}")
        
        print("\n🎉 Enhanced Import Complete!")

def main():
    """Main function"""
    importer = EnhancedKnowledgeImporter()
    importer.run_enhanced_import()

if __name__ == "__main__":
    main() 