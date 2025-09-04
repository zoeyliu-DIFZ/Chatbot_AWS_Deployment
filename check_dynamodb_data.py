#!/usr/bin/env python3
"""
Check DynamoDB data directly
"""

import boto3
import json
from datetime import datetime

def check_dynamodb_data():
    """Check data in DynamoDB tables"""
    session = boto3.Session()
    dynamodb = session.resource('dynamodb')
    
    # Check session table
    print("🔍 Checking session table...")
    session_table = dynamodb.Table('ai-chat-session-dev')
    response = session_table.scan(Limit=5)
    
    print(f"✅ Found {response['Count']} sessions:")
    for item in response['Items']:
        print(f"   Session ID: {item['session_id']}")
        print(f"   Created: {item['created_at']}")
        print(f"   Messages: {item.get('message_count', 0)}")
        print()
    
    # Check history table
    print("🔍 Checking history table...")
    history_table = dynamodb.Table('ai-chat-history-dev')
    response = history_table.scan(Limit=10)
    
    print(f"✅ Found {response['Count']} messages:")
    for item in response['Items']:
        print(f"   Session: {item['session_id']}")
        print(f"   Role: {item['role']}")
        print(f"   Content: {item['content'][:50]}...")
        print(f"   Timestamp: {item['timestamp']}")
        print()

if __name__ == "__main__":
    check_dynamodb_data()
