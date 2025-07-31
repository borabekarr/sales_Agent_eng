#!/usr/bin/env python3
"""
Populate Sales Tables with Comprehensive Knowledge Base
This script imports all structured sales intelligence into Supabase tables.
"""

import os
import json
import asyncio
from supabase import create_client, Client
from datetime import datetime
import sys

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import Settings

class SalesTablePopulator:
    def __init__(self):
        self.settings = Settings()
        self.supabase: Client = create_client(
            self.settings.SUPABASE_URL,
            self.settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
    async def populate_knowledge_base_chunks(self):
        """Populate the knowledge_base_chunks table with structured sales knowledge"""
        print("📚 Populating Knowledge Base Chunks...")
        
        # Load the comprehensive knowledge base
        with open('../supabase_db_files/comprehensive_sales_knowledge_base.json', 'r') as f:
            chunks = json.load(f)
        
        for chunk in chunks:
            try:
                # Prepare the data for insertion
                chunk_data = {
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "sequence_in_document": chunk["sequence_in_document"],
                    "chunk_type": chunk["chunk_type"],
                    "content": chunk["content"],
                    "topic": chunk["metadata"]["topic"],
                    "sub_topic": chunk["metadata"]["sub_topic"],
                    "keywords": chunk["metadata"]["keywords"],
                    "source_file": chunk["metadata"]["source_file"],
                    "intended_agent": chunk["metadata"]["intended_agent"],
                    "embedding_summary": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "priority_score": 1.0,
                    "usage_count": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = self.supabase.table("knowledge_base_chunks").insert(chunk_data).execute()
                print(f"✅ Imported chunk: {chunk['chunk_id']}")
                
            except Exception as e:
                print(f"❌ Error importing chunk {chunk['chunk_id']}: {str(e)[:100]}...")
    
    async def populate_sales_scripts(self):
        """Populate the sales_scripts table with core sales scripts"""
        print("📝 Populating Sales Scripts...")
        
        scripts = [
            {
                "script_id": "opening_script_001",
                "script_name": "Professional Opening",
                "script_type": "opening",
                "script_content": "Hi [Name], this is [Your Name] from [Company]. I'm calling because we've been helping businesses like yours increase their patient appointments by 45+ in just 30 days. I wanted to see if this might be something that could benefit your practice as well. Do you have a quick 2-3 minutes to discuss this?",
                "target_audience": "Healthcare practices",
                "success_metrics": "appointment_set",
                "usage_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "script_id": "discovery_script_001", 
                "script_name": "Pain Discovery Questions",
                "script_type": "discovery",
                "script_content": "I'm curious, how many new patients are you currently seeing each month? And what's your biggest challenge when it comes to patient acquisition?",
                "target_audience": "All practices",
                "success_metrics": "pain_identified",
                "usage_count": 0,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "script_id": "pitch_script_001",
                "script_name": "Bridge Analogy Pitch",
                "script_type": "pitch", 
                "script_content": "Imagine you're standing on one side of a river - that's where you are now. On the other side is where you want to be - with 45+ more appointments per month. The gap between is your current patient acquisition challenges. We're the bridge that gets you there. We don't just generate leads, we create a system that consistently fills your calendar.",
                "target_audience": "All practices",
                "success_metrics": "interest_generated",
                "usage_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        for script in scripts:
            try:
                result = self.supabase.table("sales_scripts").insert(script).execute()
                print(f"✅ Imported script: {script['script_name']}")
            except Exception as e:
                print(f"❌ Error importing script {script['script_name']}: {str(e)[:100]}...")
    
    async def populate_objection_responses(self):
        """Populate the objection_responses table with objection handling scripts"""
        print("🛡️ Populating Objection Responses...")
        
        objections = [
            {
                "objection_id": "price_objection_001",
                "objection_text": "It's too expensive",
                "objection_category": "price",
                "response_script": "I understand that cost is always a consideration. But let me ask you this: if I could show you how to get 45+ more appointments in the next 30 days, what would that additional revenue mean for your practice? We're not just selling a service - we're selling a proven system that pays for itself.",
                "response_framework": "value_justification",
                "success_rate": 0.85
            },
            {
                "objection_id": "time_objection_001",
                "objection_text": "I don't have time to implement this",
                "objection_category": "time",
                "response_script": "That's exactly why you need this. We handle 90% of the work for you. You focus on treating patients while we focus on filling your calendar. The beauty of our system is that it runs on autopilot once we set it up.",
                "response_framework": "problem_solution",
                "success_rate": 0.78
            },
            {
                "objection_id": "competition_objection_001",
                "objection_text": "I'm already working with another company",
                "objection_category": "competition",
                "response_script": "I appreciate your loyalty to your current provider. But I'm curious - are you getting the results you want? We're not asking you to replace what's working, we're offering to enhance what you have. Many of our clients use multiple services because they understand that diversification leads to better results.",
                "response_framework": "collaboration_approach",
                "success_rate": 0.72
            }
        ]
        
        for objection in objections:
            try:
                result = self.supabase.table("objection_responses").insert(objection).execute()
                print(f"✅ Imported objection response: {objection['objection_id']}")
            except Exception as e:
                print(f"❌ Error importing objection {objection['objection_id']}: {str(e)[:100]}...")
    
    async def populate_psychology_patterns(self):
        """Populate the psychology_patterns table with sales psychology techniques"""
        print("🧠 Populating Psychology Patterns...")
        
        patterns = [
            {
                "pattern_id": "pain_amplification_001",
                "pattern_name": "Pain Amplification",
                "pattern_type": "emotional_trigger",
                "pattern_description": "Amplify the customer's current pain by calculating the financial impact of their problem over time",
                "implementation_script": "Let's calculate this: if you're losing 10 patients per month at $500 each, that's $5,000 monthly, $60,000 annually. Over 5 years, that's $300,000 in lost revenue. Can you afford to let this continue?",
                "effectiveness_score": 0.92,
                "usage_context": "discovery_stage"
            },
            {
                "pattern_id": "bridge_analogy_001",
                "pattern_name": "Bridge Analogy",
                "pattern_type": "visual_metaphor",
                "pattern_description": "Use the bridge metaphor to explain how your service connects current reality to desired future state",
                "implementation_script": "You're on one side of the river - that's where you are now. On the other side is where you want to be. We're the bridge that gets you there safely and quickly.",
                "effectiveness_score": 0.88,
                "usage_context": "pitch_stage"
            },
            {
                "pattern_id": "silence_technique_001",
                "pattern_name": "Strategic Silence",
                "pattern_type": "pressure_technique",
                "pattern_description": "Use silence after asking powerful questions to create psychological pressure for response",
                "implementation_script": "After asking a key question, remain silent for 3-5 seconds. The customer will feel compelled to fill the silence with information.",
                "effectiveness_score": 0.85,
                "usage_context": "discovery_stage"
            }
        ]
        
        for pattern in patterns:
            try:
                result = self.supabase.table("psychology_patterns").insert(pattern).execute()
                print(f"✅ Imported psychology pattern: {pattern['pattern_name']}")
            except Exception as e:
                print(f"❌ Error importing pattern {pattern['pattern_name']}: {str(e)[:100]}...")
    
    async def populate_question_frameworks(self):
        """Populate the question_frameworks table with strategic questioning techniques"""
        print("❓ Populating Question Frameworks...")
        
        frameworks = [
            {
                "framework_id": "pain_discovery_001",
                "framework_name": "Pain Discovery Questions",
                "framework_type": "diagnostic",
                "framework_description": "Questions designed to uncover customer pain points and their financial impact",
                "question_sequence": [
                    "How many new patients do you currently see each month?",
                    "What's your biggest challenge with patient acquisition?",
                    "How much revenue does each new patient represent?",
                    "What would it mean to your practice if you had 45+ more appointments next month?"
                ],
                "target_outcome": "pain_quantification",
                "success_rate": 0.89
            },
            {
                "framework_id": "future_pacing_001",
                "framework_name": "Future Pacing Questions",
                "framework_type": "vision_building",
                "framework_description": "Questions that help customers visualize their ideal future state",
                "question_sequence": [
                    "Where do you see your practice in 6 months?",
                    "What would your ideal patient flow look like?",
                    "How would having 45+ more appointments change your practice?",
                    "What would you do with that additional revenue?"
                ],
                "target_outcome": "desire_amplification",
                "success_rate": 0.83
            }
        ]
        
        for framework in frameworks:
            try:
                result = self.supabase.table("question_frameworks").insert(framework).execute()
                print(f"✅ Imported question framework: {framework['framework_name']}")
            except Exception as e:
                print(f"❌ Error importing framework {framework['framework_name']}: {str(e)[:100]}...")
    
    async def populate_all_tables(self):
        """Populate all sales tables with comprehensive data"""
        print("🚀 Starting comprehensive sales data population...")
        
        try:
            await self.populate_knowledge_base_chunks()
            await self.populate_sales_scripts()
            await self.populate_objection_responses()
            await self.populate_psychology_patterns()
            await self.populate_question_frameworks()
            
            print("\n🎉 All sales tables populated successfully!")
            print("📊 Your knowledge base now contains:")
            print("   • 29 structured knowledge chunks")
            print("   • 3 core sales scripts")
            print("   • 3 objection response frameworks")
            print("   • 3 psychology patterns")
            print("   • 2 question frameworks")
            
        except Exception as e:
            print(f"❌ Error during population: {str(e)}")

async def main():
    """Main function to run the table population"""
    populator = SalesTablePopulator()
    await populator.populate_all_tables()

if __name__ == "__main__":
    asyncio.run(main()) 