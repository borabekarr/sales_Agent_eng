#!/usr/bin/env python3
"""
Comprehensive Sales Knowledge Base Import
This script imports ALL sales knowledge from markdown files into properly categorized Supabase tables.
"""

import os
import sys
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase import create_client, Client
except ImportError:
    print("Installing required dependencies...")
    os.system("pip install supabase")
    from supabase import create_client, Client

class ComprehensiveKnowledgeImporter:
    """Imports ALL sales knowledge from markdown files into categorized Supabase tables"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Path to knowledge base files
        self.knowledge_dir = "../supabase_db_files"
        
        # Counters for tracking imports
        self.stats = {
            "knowledge_base_chunks": 0,
            "sales_scripts": 0,
            "objection_responses": 0,
            "psychology_patterns": 0,
            "question_frameworks": 0,
            "errors": 0
        }

    def clear_existing_data(self):
        """Clear existing data from all tables"""
        print("🧹 Clearing existing data...")
        
        tables = [
            "knowledge_base_chunks",
            "sales_scripts", 
            "objection_responses",
            "psychology_patterns",
            "question_frameworks"
        ]
        
        for table in tables:
            try:
                result = self.supabase.table(table).delete().neq('id', 0).execute()
                print(f"✅ Cleared {table}")
            except Exception as e:
                print(f"⚠️  Warning clearing {table}: {str(e)}")

    def read_markdown_file(self, filepath: str) -> str:
        """Read and return content of a markdown file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading {filepath}: {str(e)}")
            return ""

    def chunk_content(self, content: str, max_chunk_size: int = 2000) -> List[str]:
        """Split content into manageable chunks"""
        if len(content) <= max_chunk_size:
            return [content]
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk + paragraph) <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def categorize_content(self, filename: str, content: str) -> Dict[str, Any]:
        """Categorize content based on filename and content analysis"""
        
        # Determine primary categorization based on filename
        if "agent_persona" in filename.lower():
            return {
                "type": "mental_framework",
                "topic": "PersonaTrait",
                "sub_topic": "AgentBehavior",
                "intended_agent": "AllAgents"
            }
        elif "meeting_script" in filename.lower():
            return {
                "type": "sales_script",
                "topic": "CallStructure", 
                "sub_topic": "FullScript",
                "intended_agent": "ConversationOrchestrator"
            }
        elif "handling_objections" in filename.lower() or "objections" in filename.lower():
            return {
                "type": "objection_handling",
                "topic": "ObjectionHandling",
                "sub_topic": "ResponseFrameworks",
                "intended_agent": "ObjectionAgent"
            }
        elif "questions" in filename.lower():
            return {
                "type": "question_framework",
                "topic": "Discovery",
                "sub_topic": "QuestionStrategies", 
                "intended_agent": "DiscoveryAgent"
            }
        elif "psychology" in filename.lower() or "trial_technique" in filename.lower():
            return {
                "type": "psychology_pattern",
                "topic": "Psychology",
                "sub_topic": "InfluencePatterns",
                "intended_agent": "AllAgents"
            }
        elif "pitch" in filename.lower() or "writing_your_pitch" in filename.lower():
            return {
                "type": "sales_script",
                "topic": "Pitch",
                "sub_topic": "PitchStructure",
                "intended_agent": "PitchAgent"
            }
        elif "closing" in filename.lower() or "conversion" in filename.lower():
            return {
                "type": "sales_script", 
                "topic": "Closing",
                "sub_topic": "ClosingTechniques",
                "intended_agent": "ClosingAgent"
            }
        else:
            # Default to mental framework for general knowledge
            return {
                "type": "mental_framework",
                "topic": "TechnicalSkills",
                "sub_topic": "GeneralKnowledge",
                "intended_agent": "AllAgents"
            }

    def extract_scripts_from_content(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extract specific scripts from content"""
        scripts = []
        
        # Extract scripts from Meeting Script
        if "meeting_script" in filename.lower():
            # Extract different sections as separate scripts
            sections = {
                "opening": r"Now, you're here because.*?(?=\n\n|\Z)",
                "pain_calculation": r"To estimate your approximate loss.*?(?=Okay\. Now|$)",
                "solution_presentation": r"With this solution, you can still get back.*?(?=—\>|$)",
                "pricing": r"The normal amount of required investment.*?(?=—\>|$)",
                "closing": r"So… At the end of the 30 days.*?(?=—\>|$)"
            }
            
            for script_type, pattern in sections.items():
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    scripts.append({
                        "script_id": f"meeting_{script_type}_{uuid.uuid4().hex[:8]}",
                        "script_name": f"Meeting Script - {script_type.title()}",
                        "script_category": script_type,
                        "script_content": match.strip(),
                        "intended_agent": self.get_agent_for_script_type(script_type),
                        "usage_context": f"Use during {script_type} phase of sales call",
                        "script_variables": json.dumps(self.extract_variables(match))
                    })
        
        return scripts

    def get_agent_for_script_type(self, script_type: str) -> str:
        """Map script type to appropriate agent"""
        mapping = {
            "opening": "OpeningAgent",
            "pain_calculation": "DiscoveryAgent", 
            "solution_presentation": "PitchAgent",
            "pricing": "PitchAgent",
            "closing": "ClosingAgent"
        }
        return mapping.get(script_type, "AllAgents")

    def extract_variables(self, content: str) -> List[str]:
        """Extract variables from script content like [Client Name], [$$$], etc."""
        variables = re.findall(r'\[([^\]]+)\]', content)
        return list(set(variables))

    def extract_objections_from_content(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extract objection responses from content"""
        objections = []
        
        if "objection" in filename.lower() or "rebuttal" in filename.lower():
            # Split content into sections and extract objection-response pairs
            sections = content.split('\n\n')
            
            current_objection = None
            current_response = ""
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Look for objection patterns
                if any(phrase in section.lower() for phrase in ["objection:", "they say:", "customer says:", "if they say"]):
                    if current_objection and current_response:
                        objections.append({
                            "objection_id": f"obj_{uuid.uuid4().hex[:8]}",
                            "objection_text": current_objection,
                            "objection_category": self.categorize_objection(current_objection),
                            "response_script": current_response.strip(),
                            "response_framework": self.get_response_framework(current_response),
                            "agent_notes": "Extracted from knowledge base"
                        })
                    
                    current_objection = section
                    current_response = ""
                elif current_objection:
                    current_response += section + "\n\n"
            
            # Don't forget the last one
            if current_objection and current_response:
                objections.append({
                    "objection_id": f"obj_{uuid.uuid4().hex[:8]}",
                    "objection_text": current_objection,
                    "objection_category": self.categorize_objection(current_objection),
                    "response_script": current_response.strip(),
                    "response_framework": self.get_response_framework(current_response),
                    "agent_notes": "Extracted from knowledge base"
                })
        
        return objections

    def categorize_objection(self, objection_text: str) -> str:
        """Categorize objection based on content"""
        objection_lower = objection_text.lower()
        
        if any(word in objection_lower for word in ["price", "expensive", "cost", "money", "afford"]):
            return "price"
        elif any(word in objection_lower for word in ["time", "busy", "schedule"]):
            return "time"
        elif any(word in objection_lower for word in ["think", "consider", "decision"]):
            return "decision_delay"
        elif any(word in objection_lower for word in ["partner", "spouse", "discuss"]):
            return "authority"
        elif any(word in objection_lower for word in ["competitor", "another", "already"]):
            return "competition"
        else:
            return "general"

    def get_response_framework(self, response: str) -> str:
        """Determine response framework based on content"""
        response_lower = response.lower()
        
        if "value" in response_lower and "worth" in response_lower:
            return "value_justification"
        elif "understand" in response_lower and "feel" in response_lower:
            return "empathy_bridge"
        elif "exactly" in response_lower and "beauty" in response_lower:
            return "reframe_positive"
        else:
            return "direct_response"

    def extract_psychology_patterns(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extract psychological patterns and techniques"""
        patterns = []
        
        if any(keyword in filename.lower() for keyword in ["psychology", "trial", "technique", "trigger"]):
            # Extract trigger words and patterns
            sections = content.split('\n\n')
            
            for section in sections:
                if len(section.strip()) < 50:  # Skip very short sections
                    continue
                
                # Look for psychological techniques
                if any(indicator in section.lower() for indicator in ["trigger word", "pattern", "technique", "psycholog"]):
                    patterns.append({
                        "pattern_id": f"psych_{uuid.uuid4().hex[:8]}",
                        "pattern_name": self.extract_pattern_name(section),
                        "pattern_category": "influence_technique",
                        "description": section.strip(),
                        "trigger_phrases": json.dumps(self.extract_trigger_phrases(section)),
                        "psychological_principle": self.extract_principle(section)
                    })
        
        return patterns

    def extract_pattern_name(self, content: str) -> str:
        """Extract pattern name from content"""
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        # Clean up the first line to make it a good name
        name = re.sub(r'^\d+\)\s*', '', first_line)  # Remove numbers like "1) "
        name = re.sub(r'^[*#]+\s*', '', name)  # Remove markdown formatting
        
        if len(name) > 100:
            name = name[:100] + "..."
        
        return name if name else "Psychological Pattern"

    def extract_trigger_phrases(self, content: str) -> List[str]:
        """Extract trigger phrases from content"""
        # Look for quoted phrases or specific trigger words
        phrases = re.findall(r'"([^"]+)"', content)
        phrases.extend(re.findall(r"'([^']+)'", content))
        
        return list(set(phrase for phrase in phrases if len(phrase.split()) <= 10))

    def extract_principle(self, content: str) -> str:
        """Extract psychological principle from content"""
        # Look for explanatory text that describes why/how it works
        sentences = content.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ["because", "psychology", "principle", "works", "effect"]):
                return sentence.strip()
        
        return "Psychological influence technique"

    def extract_questions(self, content: str, filename: str) -> List[Dict[str, Any]]:
        """Extract question frameworks from content"""
        questions = []
        
        if "question" in filename.lower() or "discovery" in filename.lower():
            # Extract questions from content
            question_patterns = [
                r'\?[^\n]*',  # Lines ending with ?
                r'(What|How|When|Where|Why|Which|Who)[^?]*\?',  # Question words
            ]
            
            for pattern in question_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    question_text = match.strip()
                    if len(question_text) > 10:  # Skip very short matches
                        questions.append({
                            "question_id": f"q_{uuid.uuid4().hex[:8]}",
                            "question_text": question_text,
                            "question_purpose": self.get_question_purpose(question_text),
                            "question_stage": self.get_question_stage(question_text),
                            "psychological_impact": "Gathers information and builds rapport",
                            "agent_instructions": "Use to understand customer needs and pain points"
                        })
        
        return questions

    def get_question_purpose(self, question: str) -> str:
        """Determine the purpose of a question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["pain", "problem", "challenge", "struggle"]):
            return "pain_discovery"
        elif any(word in question_lower for word in ["goal", "want", "achieve", "future"]):
            return "goal_identification"
        elif any(word in question_lower for word in ["current", "now", "today", "situation"]):
            return "current_state_analysis"
        else:
            return "general_discovery"

    def get_question_stage(self, question: str) -> str:
        """Determine which stage of the call this question belongs to"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["revenue", "appointments", "patients", "business"]):
            return "discovery"
        elif any(word in question_lower for word in ["feel", "important", "priority"]):
            return "emotional_discovery"
        else:
            return "general"

    def import_file(self, filepath: str):
        """Import a single markdown file"""
        filename = os.path.basename(filepath)
        print(f"📖 Processing {filename}...")
        
        content = self.read_markdown_file(filepath)
        if not content:
            return
        
        # Get categorization info
        category_info = self.categorize_content(filename, content)
        
        # Process based on type
        if category_info["type"] == "sales_script":
            scripts = self.extract_scripts_from_content(content, filename)
            for script in scripts:
                try:
                    self.supabase.table("sales_scripts").insert(script).execute()
                    self.stats["sales_scripts"] += 1
                    print(f"✅ Added script: {script['script_name']}")
                except Exception as e:
                    print(f"❌ Error adding script: {str(e)}")
                    self.stats["errors"] += 1
        
        elif category_info["type"] == "objection_handling":
            objections = self.extract_objections_from_content(content, filename)
            for objection in objections:
                try:
                    self.supabase.table("objection_responses").insert(objection).execute()
                    self.stats["objection_responses"] += 1
                    print(f"✅ Added objection response")
                except Exception as e:
                    print(f"❌ Error adding objection: {str(e)}")
                    self.stats["errors"] += 1
        
        elif category_info["type"] == "psychology_pattern":
            patterns = self.extract_psychology_patterns(content, filename)
            for pattern in patterns:
                try:
                    self.supabase.table("psychology_patterns").insert(pattern).execute()
                    self.stats["psychology_patterns"] += 1
                    print(f"✅ Added psychology pattern: {pattern['pattern_name']}")
                except Exception as e:
                    print(f"❌ Error adding pattern: {str(e)}")
                    self.stats["errors"] += 1
        
        elif category_info["type"] == "question_framework":
            questions = self.extract_questions(content, filename)
            for question in questions:
                try:
                    self.supabase.table("question_frameworks").insert(question).execute()
                    self.stats["question_frameworks"] += 1
                    print(f"✅ Added question framework")
                except Exception as e:
                    print(f"❌ Error adding question: {str(e)}")
                    self.stats["errors"] += 1
        
        # Always add to knowledge base chunks for general knowledge
        chunks = self.chunk_content(content)
        for i, chunk in enumerate(chunks):
            try:
                chunk_data = {
                    "chunk_id": f"{filename}_{i+1}_{uuid.uuid4().hex[:8]}",
                    "document_id": filename.replace('.md', '').replace(' ', '_').lower(),
                    "sequence_in_document": i + 1,
                    "chunk_type": "detail" if len(chunks) > 1 else "summary",
                    "content": chunk,
                    "topic": category_info["topic"],
                    "sub_topic": category_info["sub_topic"],
                    "keywords": json.dumps(self.extract_keywords(chunk)),
                    "source_file": filename,
                    "intended_agent": category_info["intended_agent"]
                }
                
                self.supabase.table("knowledge_base_chunks").insert(chunk_data).execute()
                self.stats["knowledge_base_chunks"] += 1
                
            except Exception as e:
                print(f"❌ Error adding knowledge chunk: {str(e)}")
                self.stats["errors"] += 1

    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        # Filter common words
        common_words = {'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'their', 'said', 'each', 'which', 'your', 'into', 'than', 'only', 'over', 'also', 'back', 'after', 'first', 'well', 'many', 'some', 'time', 'very', 'when', 'much', 'new'}
        keywords = [word for word in set(words) if word not in common_words]
        return keywords[:10]  # Return top 10 keywords

    def import_all_files(self):
        """Import all markdown files from the knowledge directory"""
        print("🚀 Starting comprehensive knowledge base import...")
        
        # Clear existing data first
        self.clear_existing_data()
        
        # Get all markdown files
        markdown_files = []
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.knowledge_dir, filename)
                markdown_files.append(filepath)
        
        print(f"📁 Found {len(markdown_files)} markdown files to process")
        
        # Process each file
        for filepath in markdown_files:
            self.import_file(filepath)
        
        # Print final statistics
        print("\n🎉 Import Complete!")
        print("📊 Final Statistics:")
        print(f"   📚 Knowledge Base Chunks: {self.stats['knowledge_base_chunks']}")
        print(f"   📝 Sales Scripts: {self.stats['sales_scripts']}")
        print(f"   🛡️  Objection Responses: {self.stats['objection_responses']}")
        print(f"   🧠 Psychology Patterns: {self.stats['psychology_patterns']}")
        print(f"   ❓ Question Frameworks: {self.stats['question_frameworks']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        total_imported = sum(v for k, v in self.stats.items() if k != 'errors')
        print(f"\n✨ Total items imported: {total_imported}")

def main():
    """Main function"""
    importer = ComprehensiveKnowledgeImporter()
    importer.import_all_files()

if __name__ == "__main__":
    main() 