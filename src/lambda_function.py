import json
import boto3
import os
from agent import ChatAgent

# Global agent instance for reuse across invocations
agent = None

def get_agent():
    """Get or create agent instance"""
    global agent
    if agent is None:
        agent = ChatAgent()
    return agent

def lambda_handler(event, context):
    """Lambda function handler for chat API using LangGraph workflow"""
    
    # Set CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
    }
    
    try:
        # Handle preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Parse request body
        if 'body' in event and event['body']:
            body = json.loads(event['body'])
        else:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Request body is required'})
            }
        
        # Extract user message
        user_message = body.get('message', '').strip()
        if not user_message:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Get chat history (optional)
        chat_history = body.get('chat_history', [])
        
        # Get agent and process message using LangGraph workflow with path tracking
        chat_agent = get_agent()
        response, workflow_info = chat_agent.query_with_path(user_message, chat_history)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response,
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent'),
                'message': user_message
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        } 