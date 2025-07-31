#!/usr/bin/env python3
"""
System Health Check for Sales Assistant
This script validates all system components and troubleshoots common issues.
"""

import os
import sys
import subprocess
import json
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_python_environment() -> Dict[str, Any]:
    """Check Python environment status"""
    result = {
        "status": "✅ PASS",
        "details": {},
        "issues": []
    }
    
    try:
        # Check Python version
        python_version = sys.version_info
        result["details"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
        
        # Check if we're in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        result["details"]["virtual_environment"] = "Active" if in_venv else "Not Active"
        
        if not in_venv:
            result["issues"].append("⚠️  Virtual environment not active")
        
        # Check required packages
        required_packages = [
            ("supabase", "supabase"),
            ("requests", "requests"), 
            ("python-dateutil", "dateutil")
        ]
        installed_packages = []
        missing_packages = []
        
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                installed_packages.append(package_name)
            except ImportError:
                missing_packages.append(package_name)
        
        result["details"]["installed_packages"] = installed_packages
        result["details"]["missing_packages"] = missing_packages
        
        if missing_packages:
            result["issues"].append(f"❌ Missing packages: {', '.join(missing_packages)}")
            result["status"] = "❌ FAIL"
            
    except Exception as e:
        result["status"] = "❌ FAIL"
        result["issues"].append(f"❌ Python environment error: {str(e)}")
    
    return result

def check_environment_variables() -> Dict[str, Any]:
    """Check required environment variables"""
    result = {
        "status": "✅ PASS",
        "details": {},
        "issues": []
    }
    
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            result["details"][var] = "✅ Set" + (" (masked)" if "KEY" in var else f" ({value})")
        else:
            result["details"][var] = "❌ Not Set"
            result["issues"].append(f"❌ Missing environment variable: {var}")
            result["status"] = "❌ FAIL"
    
    return result

def check_supabase_connection() -> Dict[str, Any]:
    """Check Supabase database connection"""
    result = {
        "status": "✅ PASS",
        "details": {},
        "issues": []
    }
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            result["status"] = "❌ FAIL"
            result["issues"].append("❌ Missing Supabase credentials")
            return result
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Test connection by querying a table
        response = supabase.table("knowledge_base_chunks").select("count", count="exact").limit(1).execute()
        
        result["details"]["connection"] = "✅ Connected"
        result["details"]["knowledge_chunks"] = len(response.data) if hasattr(response, 'data') else 0
        
        # Check all tables exist
        tables = ["knowledge_base_chunks", "sales_scripts", "objection_responses", "psychology_patterns", "question_frameworks"]
        table_status = {}
        
        for table in tables:
            try:
                resp = supabase.table(table).select("count", count="exact").limit(1).execute()
                table_status[table] = f"✅ ({resp.count if hasattr(resp, 'count') else '?'} rows)"
            except Exception as e:
                table_status[table] = f"❌ Error: {str(e)[:50]}"
                result["issues"].append(f"❌ Table {table} issue: {str(e)[:50]}")
        
        result["details"]["tables"] = table_status
        
    except Exception as e:
        result["status"] = "❌ FAIL"
        result["issues"].append(f"❌ Supabase connection error: {str(e)}")
    
    return result

def check_knowledge_base_files() -> Dict[str, Any]:
    """Check knowledge base markdown files"""
    result = {
        "status": "✅ PASS",
        "details": {},
        "issues": []
    }
    
    try:
        knowledge_dir = "../supabase_db_files"
        
        if not os.path.exists(knowledge_dir):
            result["status"] = "❌ FAIL"
            result["issues"].append(f"❌ Knowledge base directory not found: {knowledge_dir}")
            return result
        
        markdown_files = [f for f in os.listdir(knowledge_dir) if f.endswith('.md')]
        
        result["details"]["directory"] = os.path.abspath(knowledge_dir)
        result["details"]["total_files"] = len(markdown_files)
        result["details"]["files"] = markdown_files[:10]  # First 10 files
        
        if len(markdown_files) < 15:
            result["issues"].append(f"⚠️  Only {len(markdown_files)} markdown files found, expected ~20")
        
        # Check key files exist
        key_files = ["Meeting Script.md", "HANDLING OBJECTIONS.md", "agent_persona.md"]
        missing_key_files = [f for f in key_files if f not in markdown_files]
        
        if missing_key_files:
            result["issues"].append(f"❌ Missing key files: {', '.join(missing_key_files)}")
            result["status"] = "❌ FAIL"
        
    except Exception as e:
        result["status"] = "❌ FAIL"
        result["issues"].append(f"❌ Knowledge base files error: {str(e)}")
    
    return result

def check_import_scripts() -> Dict[str, Any]:
    """Check import scripts can be loaded"""
    result = {
        "status": "✅ PASS",
        "details": {},
        "issues": []
    }
    
    scripts = [
        "scripts.comprehensive_knowledge_import",
        "scripts.enhanced_knowledge_import"
    ]
    
    for script in scripts:
        try:
            module = __import__(script, fromlist=[''])
            result["details"][script] = "✅ Imports successfully"
        except Exception as e:
            result["details"][script] = f"❌ Import error: {str(e)[:50]}"
            result["issues"].append(f"❌ Script {script} import error: {str(e)[:50]}")
            result["status"] = "❌ FAIL"
    
    return result

def generate_fix_recommendations(all_results: Dict[str, Dict[str, Any]]) -> List[str]:
    """Generate fix recommendations based on health check results"""
    recommendations = []
    
    for check_name, result in all_results.items():
        if result["status"] == "❌ FAIL":
            recommendations.append(f"\n🔧 **Fix {check_name}:**")
            for issue in result["issues"]:
                if "Virtual environment not active" in issue:
                    recommendations.append("   • Run: `source venv/bin/activate`")
                elif "Missing packages" in issue:
                    recommendations.append("   • Run: `pip install supabase python-dateutil requests`")
                elif "Missing environment variable" in issue:
                    recommendations.append("   • Set environment variables before running scripts")
                elif "Missing key files" in issue:
                    recommendations.append("   • Check that all markdown files are in ../supabase_db_files/")
                else:
                    recommendations.append(f"   • {issue}")
    
    return recommendations

def main():
    """Run complete system health check"""
    print("🔍 **Sales Assistant System Health Check**")
    print("=" * 50)
    
    checks = {
        "Python Environment": check_python_environment,
        "Environment Variables": check_environment_variables,
        "Supabase Connection": check_supabase_connection,
        "Knowledge Base Files": check_knowledge_base_files,
        "Import Scripts": check_import_scripts
    }
    
    all_results = {}
    overall_status = "✅ HEALTHY"
    
    for check_name, check_func in checks.items():
        print(f"\n📋 {check_name}:")
        result = check_func()
        all_results[check_name] = result
        
        print(f"   Status: {result['status']}")
        
        for key, value in result["details"].items():
            print(f"   {key}: {value}")
        
        if result["issues"]:
            for issue in result["issues"]:
                print(f"   {issue}")
        
        if result["status"] == "❌ FAIL":
            overall_status = "❌ NEEDS ATTENTION"
    
    print("\n" + "=" * 50)
    print(f"🎯 **Overall Status: {overall_status}**")
    
    if overall_status == "❌ NEEDS ATTENTION":
        recommendations = generate_fix_recommendations(all_results)
        print("\n🛠️  **Recommended Fixes:**")
        for rec in recommendations:
            print(rec)
    else:
        print("✨ All systems operational! Your sales assistant is ready.")
    
    print("\n📊 **Quick Summary:**")
    for check_name, result in all_results.items():
        print(f"   {result['status']} {check_name}")

if __name__ == "__main__":
    main() 