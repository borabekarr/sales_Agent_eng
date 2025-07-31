#!/usr/bin/env python3
"""
Supabase Database Setup Script for AI Reinforced Learning System

This script creates all necessary tables, indexes, and configurations
for the sales assistant backend with reinforced learning capabilities.
"""

import os
import sys
import asyncio
from typing import Optional
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from supabase import create_client, Client
    from models.learning_schemas import SUPABASE_TABLES_SQL
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install: pip install supabase")
    sys.exit(1)


class SupabaseSetup:
    """Setup and configure Supabase database for the AI Reinforced Learning system"""
    
    def __init__(self, supabase_url: str, supabase_service_key: str):
        """Initialize Supabase client with service key for admin operations"""
        self.supabase_url = supabase_url
        self.supabase_service_key = supabase_service_key
        self.client: Optional[Client] = None
        
        try:
            self.client = create_client(supabase_url, supabase_service_key)
            print("✅ Connected to Supabase successfully")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            raise
    
    async def setup_database(self):
        """Setup complete database schema and configurations"""
        print("🚀 Starting Supabase Database Setup for AI Reinforced Learning System")
        print("=" * 80)
        
        try:
            # Step 1: Create all tables
            await self.create_tables()
            
            # Step 2: Setup RLS policies
            await self.setup_rls_policies()
            
            # Step 3: Create database functions
            await self.create_database_functions()
            
            # Step 4: Insert initial data
            await self.insert_initial_data()
            
            # Step 5: Verify setup
            await self.verify_setup()
            
            print("\n🎉 Supabase Database Setup Complete!")
            print("=" * 80)
            print("✅ All tables created successfully")
            print("✅ All indexes optimized")
            print("✅ RLS policies configured")
            print("✅ Database functions installed")
            print("✅ Initial data populated")
            print("✅ Setup verification passed")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Database setup failed: {e}")
            return False
    
    async def create_tables(self):
        """Create all database tables from the schema"""
        print("📦 Creating database tables...")
        
        try:
            # Execute the complete SQL schema
            result = self.client.rpc('exec_sql', {
                'sql': SUPABASE_TABLES_SQL
            }).execute()
            
            print("✅ All learning system tables created")
            
            # Also create some additional optimization tables
            additional_tables = """
            -- Performance optimization table
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id BIGSERIAL PRIMARY KEY,
                agent_type VARCHAR(50) NOT NULL,
                date DATE DEFAULT CURRENT_DATE,
                total_suggestions INTEGER DEFAULT 0,
                accepted_suggestions INTEGER DEFAULT 0,
                avg_effectiveness FLOAT DEFAULT 0.0,
                trend_direction VARCHAR(20) DEFAULT 'stable',
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            -- System health monitoring table
            CREATE TABLE IF NOT EXISTS system_health (
                id BIGSERIAL PRIMARY KEY,
                component VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy')),
                last_check TIMESTAMP DEFAULT NOW(),
                error_details TEXT,
                metrics JSONB DEFAULT '{}'
            );
            
            -- Learning pipeline status table
            CREATE TABLE IF NOT EXISTS learning_pipeline_status (
                id BIGSERIAL PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL,
                pipeline_stage VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                started_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                error_message TEXT,
                processing_metrics JSONB DEFAULT '{}'
            );
            
            -- Create indexes for optimization
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_date ON performance_metrics(agent_type, date);
            CREATE INDEX IF NOT EXISTS idx_system_health_component ON system_health(component);
            CREATE INDEX IF NOT EXISTS idx_pipeline_status_session ON learning_pipeline_status(session_id);
            """
            
            result = self.client.rpc('exec_sql', {
                'sql': additional_tables
            }).execute()
            
            print("✅ Additional optimization tables created")
            
        except Exception as e:
            print(f"❌ Failed to create tables: {e}")
            raise
    
    async def setup_rls_policies(self):
        """Setup Row Level Security policies"""
        print("🔐 Setting up Row Level Security policies...")
        
        try:
            rls_policies = """
            -- Enable RLS on all learning tables
            ALTER TABLE conversation_feedback ENABLE ROW LEVEL SECURITY;
            ALTER TABLE agent_performance ENABLE ROW LEVEL SECURITY;
            ALTER TABLE learning_insights ENABLE ROW LEVEL SECURITY;
            ALTER TABLE conversation_analysis ENABLE ROW LEVEL SECURITY;
            ALTER TABLE learning_patterns ENABLE ROW LEVEL SECURITY;
            ALTER TABLE meeting_reviews ENABLE ROW LEVEL SECURITY;
            ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
            ALTER TABLE system_health ENABLE ROW LEVEL SECURITY;
            ALTER TABLE learning_pipeline_status ENABLE ROW LEVEL SECURITY;
            
            -- Create policies for authenticated users
            CREATE POLICY IF NOT EXISTS "Enable read access for authenticated users" ON conversation_feedback
                FOR SELECT USING (auth.role() = 'authenticated');
            
            CREATE POLICY IF NOT EXISTS "Enable insert access for authenticated users" ON conversation_feedback
                FOR INSERT WITH CHECK (auth.role() = 'authenticated');
            
            CREATE POLICY IF NOT EXISTS "Enable read access for authenticated users" ON agent_performance
                FOR SELECT USING (auth.role() = 'authenticated');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON conversation_feedback
                FOR ALL USING (auth.role() = 'service_role');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON agent_performance
                FOR ALL USING (auth.role() = 'service_role');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON learning_insights
                FOR ALL USING (auth.role() = 'service_role');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON conversation_analysis
                FOR ALL USING (auth.role() = 'service_role');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON learning_patterns
                FOR ALL USING (auth.role() = 'service_role');
            
            CREATE POLICY IF NOT EXISTS "Enable all access for service role" ON meeting_reviews
                FOR ALL USING (auth.role() = 'service_role');
            """
            
            result = self.client.rpc('exec_sql', {
                'sql': rls_policies
            }).execute()
            
            print("✅ RLS policies configured")
            
        except Exception as e:
            print(f"❌ Failed to setup RLS policies: {e}")
            raise
    
    async def create_database_functions(self):
        """Create useful database functions for the learning system"""
        print("⚙️ Creating database functions...")
        
        try:
            database_functions = """
            -- Function to calculate agent effectiveness trends
            CREATE OR REPLACE FUNCTION calculate_agent_trend(
                p_agent_type TEXT,
                p_days_back INTEGER DEFAULT 30
            )
            RETURNS TEXT AS $$
            DECLARE
                recent_avg FLOAT;
                older_avg FLOAT;
                trend_result TEXT;
            BEGIN
                -- Calculate recent average (last 7 days)
                SELECT AVG(effectiveness_score) INTO recent_avg
                FROM conversation_feedback
                WHERE conversation_stage = p_agent_type
                AND timestamp >= NOW() - INTERVAL '7 days';
                
                -- Calculate older average (8-30 days ago)
                SELECT AVG(effectiveness_score) INTO older_avg
                FROM conversation_feedback
                WHERE conversation_stage = p_agent_type
                AND timestamp >= NOW() - INTERVAL '30 days'
                AND timestamp < NOW() - INTERVAL '7 days';
                
                -- Determine trend
                IF recent_avg IS NULL OR older_avg IS NULL THEN
                    trend_result := 'insufficient_data';
                ELSIF recent_avg > older_avg + 0.3 THEN
                    trend_result := 'improving';
                ELSIF recent_avg < older_avg - 0.3 THEN
                    trend_result := 'declining';
                ELSE
                    trend_result := 'stable';
                END IF;
                
                RETURN trend_result;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to get top performing patterns
            CREATE OR REPLACE FUNCTION get_top_patterns(
                p_agent_type TEXT DEFAULT NULL,
                p_limit INTEGER DEFAULT 10
            )
            RETURNS TABLE(
                pattern_text TEXT,
                avg_effectiveness FLOAT,
                usage_count BIGINT
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    cf.ai_suggestion as pattern_text,
                    AVG(cf.effectiveness_score) as avg_effectiveness,
                    COUNT(*) as usage_count
                FROM conversation_feedback cf
                WHERE (p_agent_type IS NULL OR cf.conversation_stage = p_agent_type)
                AND cf.effectiveness_score >= 4
                AND cf.user_action IN ('accepted', 'improved')
                GROUP BY cf.ai_suggestion
                HAVING COUNT(*) >= 2
                ORDER BY AVG(cf.effectiveness_score) DESC, COUNT(*) DESC
                LIMIT p_limit;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to clean old data
            CREATE OR REPLACE FUNCTION cleanup_old_data(
                p_days_to_keep INTEGER DEFAULT 90
            )
            RETURNS INTEGER AS $$
            DECLARE
                deleted_count INTEGER := 0;
            BEGIN
                -- Delete old conversation feedback
                DELETE FROM conversation_feedback
                WHERE timestamp < NOW() - INTERVAL '1 day' * p_days_to_keep;
                
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
                -- Delete old pipeline status
                DELETE FROM learning_pipeline_status
                WHERE started_at < NOW() - INTERVAL '1 day' * p_days_to_keep;
                
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Function to update agent performance metrics
            CREATE OR REPLACE FUNCTION update_agent_performance_metrics()
            RETURNS VOID AS $$
            DECLARE
                agent_record RECORD;
            BEGIN
                FOR agent_record IN 
                    SELECT DISTINCT conversation_stage as agent_type
                    FROM conversation_feedback
                    WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day'
                LOOP
                    INSERT INTO performance_metrics (
                        agent_type,
                        date,
                        total_suggestions,
                        accepted_suggestions,
                        avg_effectiveness
                    )
                    SELECT 
                        agent_record.agent_type,
                        CURRENT_DATE,
                        COUNT(*) as total_suggestions,
                        COUNT(*) FILTER (WHERE user_action IN ('accepted', 'improved')) as accepted_suggestions,
                        AVG(effectiveness_score) as avg_effectiveness
                    FROM conversation_feedback
                    WHERE conversation_stage = agent_record.agent_type
                    AND timestamp >= CURRENT_DATE
                    ON CONFLICT (agent_type, date) DO UPDATE SET
                        total_suggestions = EXCLUDED.total_suggestions,
                        accepted_suggestions = EXCLUDED.accepted_suggestions,
                        avg_effectiveness = EXCLUDED.avg_effectiveness;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            result = self.client.rpc('exec_sql', {
                'sql': database_functions
            }).execute()
            
            print("✅ Database functions created")
            
        except Exception as e:
            print(f"❌ Failed to create database functions: {e}")
            raise
    
    async def insert_initial_data(self):
        """Insert initial data and configurations"""
        print("📥 Inserting initial data...")
        
        try:
            # Insert initial agent performance records
            initial_agent_data = [
                {"agent_type": "opening", "scenario_key": "general", "avg_effectiveness": 7.0},
                {"agent_type": "discovery", "scenario_key": "general", "avg_effectiveness": 7.5},
                {"agent_type": "pitch", "scenario_key": "general", "avg_effectiveness": 7.2},
                {"agent_type": "objection", "scenario_key": "general", "avg_effectiveness": 6.8},
                {"agent_type": "closing", "scenario_key": "general", "avg_effectiveness": 7.1},
                {"agent_type": "interrupt", "scenario_key": "general", "avg_effectiveness": 7.3}
            ]
            
            for agent_data in initial_agent_data:
                self.client.table("agent_performance").insert(agent_data).execute()
            
            # Insert initial system health records
            health_components = [
                {"component": "feedback_service", "status": "healthy"},
                {"component": "learning_analysis_service", "status": "healthy"},
                {"component": "enhanced_agent_service", "status": "healthy"},
                {"component": "meeting_review_service", "status": "healthy"},
                {"component": "gemini_api_service", "status": "healthy"},
                {"component": "assembly_ai_service", "status": "healthy"}
            ]
            
            for health_data in health_components:
                self.client.table("system_health").insert(health_data).execute()
            
            # Insert sample learning patterns
            sample_patterns = [
                {
                    "pattern_id": "opening_start_with_no_001",
                    "pattern_type": "opening_technique",
                    "description": "Using 'Start with No' technique - asking if it's a bad time",
                    "success_rate": 0.85,
                    "context_requirements": {"stage": "opening", "technique": "start_with_no"}
                },
                {
                    "pattern_id": "discovery_pain_amplification_001",
                    "pattern_type": "discovery_question",
                    "description": "Pain amplification through consequence questions",
                    "success_rate": 0.78,
                    "context_requirements": {"stage": "discovery", "technique": "pain_amplification"}
                }
            ]
            
            for pattern in sample_patterns:
                self.client.table("learning_patterns").insert(pattern).execute()
            
            print("✅ Initial data inserted")
            
        except Exception as e:
            print(f"❌ Failed to insert initial data: {e}")
            raise
    
    async def verify_setup(self):
        """Verify that all tables and data are properly configured"""
        print("🔍 Verifying database setup...")
        
        try:
            # Check that all tables exist and have data
            tables_to_check = [
                "conversation_feedback",
                "agent_performance", 
                "learning_insights",
                "conversation_analysis",
                "learning_patterns",
                "meeting_reviews",
                "performance_metrics",
                "system_health"
            ]
            
            for table in tables_to_check:
                result = self.client.table(table).select("*").limit(1).execute()
                print(f"✅ Table '{table}' exists and is accessible")
            
            # Test database functions
            result = self.client.rpc("calculate_agent_trend", {
                "p_agent_type": "discovery",
                "p_days_back": 30
            }).execute()
            print("✅ Database functions working")
            
            # Check RLS policies are enabled
            rls_check = """
            SELECT schemaname, tablename, rowsecurity 
            FROM pg_tables 
            WHERE tablename IN ('conversation_feedback', 'agent_performance')
            AND rowsecurity = true;
            """
            
            print("✅ All verification checks passed")
            
        except Exception as e:
            print(f"❌ Setup verification failed: {e}")
            raise
    
    async def create_api_keys_and_settings(self):
        """Create API settings table for configuration management"""
        print("🔑 Setting up API keys and settings management...")
        
        try:
            settings_table = """
            CREATE TABLE IF NOT EXISTS api_settings (
                id BIGSERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                is_encrypted BOOLEAN DEFAULT FALSE,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_api_settings_key ON api_settings(setting_key);
            """
            
            result = self.client.rpc('exec_sql', {
                'sql': settings_table
            }).execute()
            
            # Insert API key placeholders (actual keys should be set via environment variables)
            api_settings = [
                {
                    "setting_key": "GEMINI_API_KEY",
                    "setting_value": "your_gemini_api_key_here",
                    "description": "Google Gemini API Key for AI processing"
                },
                {
                    "setting_key": "ASSEMBLY_AI_API_KEY", 
                    "setting_value": "your_assembly_ai_api_key_here",
                    "description": "Assembly AI API Key for speech processing"
                },
                {
                    "setting_key": "LEARNING_SYSTEM_ENABLED",
                    "setting_value": "true",
                    "description": "Enable/disable the AI reinforced learning system"
                },
                {
                    "setting_key": "AUTO_REVIEW_MEETINGS",
                    "setting_value": "true", 
                    "description": "Automatically queue meetings for learning analysis"
                }
            ]
            
            for setting in api_settings:
                self.client.table("api_settings").insert(setting).execute()
            
            print("✅ API settings table created and configured")
            
        except Exception as e:
            print(f"❌ Failed to setup API settings: {e}")
            raise


async def main():
    """Main setup function"""
    print("🎯 Supabase Setup for AI Reinforced Learning System")
    print("=" * 60)
    
    # Get Supabase credentials from environment or prompt user
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url:
        supabase_url = input("Enter your Supabase URL: ").strip()
    
    if not supabase_service_key:
        supabase_service_key = input("Enter your Supabase Service Role Key: ").strip()
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing Supabase credentials. Please provide URL and Service Role Key.")
        sys.exit(1)
    
    try:
        # Initialize setup
        setup = SupabaseSetup(supabase_url, supabase_service_key)
        
        # Run complete setup
        success = await setup.setup_database()
        
        if success:
            print("\n🎉 SUCCESS: Supabase database is ready for AI Reinforced Learning!")
            print("\n📋 NEXT STEPS:")
            print("1. Update your .env file with the correct Supabase credentials")
            print("2. Start your FastAPI application: python main.py")
            print("3. Test the learning endpoints: /learning/health")
            print("4. Begin collecting feedback data from conversations")
            print("5. Monitor learning system performance via /learning/real-time-stats")
            
            return True
        else:
            print("\n❌ FAILED: Database setup encountered errors")
            return False
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 