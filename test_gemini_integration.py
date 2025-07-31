#!/usr/bin/env python3
"""
Test script to validate Gemini AI integration
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.gemini_api import GeminiAPIService
from models.schemas import AgentContext, CustomerProfile, Message
from datetime import datetime


async def test_gemini_integration():
    """Test basic Gemini AI integration"""
    print("🤖 Testing Gemini AI Integration...")
    
    try:
        # Initialize Gemini service
        gemini_service = GeminiAPIService()
        print("✅ Gemini service initialized successfully")
        
        # Test connection
        connection_test = await gemini_service.test_connection()
        if connection_test:
            print("✅ Gemini API connection successful")
        else:
            print("❌ Gemini API connection failed")
            return False
        
        # Create test context
        customer_profile = CustomerProfile(
            name="John Doe",
            company="Test Corp",
            pain_points=["High costs", "Manual processes"]
        )
        
        test_messages = [
            Message(
                session_id="test",
                speaker="seller",
                text="Hello! Thanks for joining our call today.",
                confidence=1.0,
                stage="opening"
            ),
            Message(
                session_id="test", 
                speaker="customer",
                text="Hi, I'm interested in learning more about your solution.",
                confidence=0.95,
                stage="opening"
            )
        ]
        
        context = AgentContext(
            current_stage="discovery",
            customer_profile=customer_profile,
            recent_messages=test_messages,
            conversation_history=test_messages,
            context_stack=[],
            session_metadata={"session_id": "test"}
        )
        
        # Test suggestion generation
        print("\n🧠 Testing suggestion generation...")
        suggestion = await gemini_service.generate_suggestion(
            context=context,
            agent_type="discovery",
            conversation_history=test_messages
        )
        
        print(f"✅ Generated suggestion: {suggestion.get('suggestion', 'No suggestion')}")
        print(f"✅ Suggestion type: {suggestion.get('type', 'unknown')}")
        print(f"✅ Confidence: {suggestion.get('confidence', 0.0)}")
        
        # Test customer profile analysis
        print("\n👤 Testing customer profile analysis...")
        profile = await gemini_service.analyze_customer_profile(test_messages)
        print(f"✅ Analyzed customer profile: {profile.name or 'Unknown'}")
        print(f"✅ Pain points detected: {len(profile.pain_points)}")
        
        # Test conversation stage determination
        print("\n🎯 Testing stage determination...")
        stage_result = await gemini_service.determine_conversation_stage(
            test_messages, "opening"
        )
        print(f"✅ Recommended stage: {stage_result.get('recommended_stage', 'unknown')}")
        print(f"✅ Confidence: {stage_result.get('confidence', 0.0)}")
        
        print("\n🎉 All Gemini AI tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


async def main():
    """Main test function"""
    print("=" * 50)
    print("🚀 Real-time AI Sales Assistant - Gemini Integration Test")
    print("=" * 50)
    
    success = await test_gemini_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ INTEGRATION TEST SUCCESSFUL")
        print("🚀 System ready for deployment!")
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("Please check your API keys and configuration")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main()) 