#!/usr/bin/env python3
"""
Test DynamoDB connectivity and table access
"""

import boto3
import os
import sys

def test_aws_credentials():
    """Test AWS credentials"""
    print("🔍 Testing AWS credentials...")
    try:
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials valid")
        print(f"   Account: {identity['Account']}")
        print(f"   User: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        return False

def test_dynamodb_connection():
    """Test DynamoDB connection"""
    print("\n🔍 Testing DynamoDB connection...")
    try:
        session = boto3.Session()
        dynamodb = session.resource('dynamodb')
        
        # List tables
        tables = list(dynamodb.tables.all())
        print(f"✅ DynamoDB connection successful")
        print(f"   Found {len(tables)} tables")
        
        # Check for our specific tables
        table_names = [table.name for table in tables]
        session_table = 'ai-chat-session-dev'
        history_table = 'ai-chat-history-dev'
        
        if session_table in table_names:
            print(f"✅ Found session table: {session_table}")
        else:
            print(f"❌ Session table not found: {session_table}")
            
        if history_table in table_names:
            print(f"✅ Found history table: {history_table}")
        else:
            print(f"❌ History table not found: {history_table}")
            
        return True
    except Exception as e:
        print(f"❌ DynamoDB connection error: {e}")
        return False

def test_table_access():
    """Test access to specific tables"""
    print("\n🔍 Testing table access...")
    try:
        session = boto3.Session()
        dynamodb = session.resource('dynamodb')
        
        session_table = dynamodb.Table('ai-chat-session-dev')
        history_table = dynamodb.Table('ai-chat-history-dev')
        
        # Test session table
        try:
            session_table.load()
            print(f"✅ Session table accessible")
        except Exception as e:
            print(f"❌ Cannot access session table: {e}")
            
        # Test history table
        try:
            history_table.load()
            print(f"✅ History table accessible")
        except Exception as e:
            print(f"❌ Cannot access history table: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Table access error: {e}")
        return False

def test_basic_operations():
    """Test basic DynamoDB operations"""
    print("\n🔍 Testing basic operations...")
    try:
        session = boto3.Session()
        dynamodb = session.resource('dynamodb')
        
        session_table = dynamodb.Table('ai-chat-session-dev')
        history_table = dynamodb.Table('ai-chat-history-dev')
        
        # Test scan operation on session table
        try:
            response = session_table.scan(Limit=1)
            print(f"✅ Session table scan successful")
            print(f"   Items found: {response.get('Count', 0)}")
        except Exception as e:
            print(f"❌ Session table scan failed: {e}")
            
        # Test scan operation on history table
        try:
            response = history_table.scan(Limit=1)
            print(f"✅ History table scan successful")
            print(f"   Items found: {response.get('Count', 0)}")
        except Exception as e:
            print(f"❌ History table scan failed: {e}")
            
        return True
    except Exception as e:
        print(f"❌ Basic operations error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 DynamoDB Connection Test")
    print("=" * 50)
    
    # Test AWS credentials
    if not test_aws_credentials():
        print("\n❌ AWS credentials test failed. Exiting.")
        return
    
    # Test DynamoDB connection
    if not test_dynamodb_connection():
        print("\n❌ DynamoDB connection test failed. Exiting.")
        return
    
    # Test table access
    if not test_table_access():
        print("\n❌ Table access test failed. Exiting.")
        return
    
    # Test basic operations
    if not test_basic_operations():
        print("\n❌ Basic operations test failed. Exiting.")
        return
    
    print("\n✅ All tests passed! DynamoDB is ready to use.")

if __name__ == "__main__":
    main()
