import json
import boto3
import os
from agent import ChatAgent
from dynamodb_manager import db_manager

# Global agent instance for reuse across invocations
agent = None

def get_agent():
    """Get or create agent instance"""
    global agent
    if agent is None:
        agent = ChatAgent()
    return agent

def lambda_handler(event, context):
    """Lambda function handler for chat API and session management using LangGraph workflow with DynamoDB integration"""
    
    # Set CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,DELETE'
    }
    
    try:
        # Handle preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'OK'})
            }
        
        # Route based on path and method
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        resource = event.get('resource', '')
        
        # Check if this is a sessions endpoint
        if resource == '/sessions' and method == 'GET':
            return handle_list_sessions(event, headers)
        elif resource == '/sessions/{session_id}' and method == 'GET':
            return handle_get_session(event, headers)
        elif resource == '/sessions/{session_id}' and method == 'DELETE':
            return handle_delete_session(event, headers)
        elif path == '/chat' and method == 'POST':
            return handle_chat_request(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_chat_request(event, headers):
    """Handle chat requests"""
    try:
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
        
        # Get or create session ID
        session_id = body.get('session_id')
        if not session_id:
            # Create new session
            session_id = db_manager.create_session(metadata={
                'user_agent': event.get('headers', {}).get('User-Agent', ''),
                'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', '')
            })
        
        # Get chat history from DynamoDB
        chat_history_messages = db_manager.get_chat_history(session_id, limit=20)
        
        # Convert to format expected by agent
        chat_history = []
        for msg in chat_history_messages:
            if msg['role'] == 'user':
                chat_history.append(('human', msg['content']))
            elif msg['role'] == 'assistant':
                chat_history.append(('assistant', msg['content']))
        
        # Get agent and process message using LangGraph workflow with path tracking
        chat_agent = get_agent()
        response, workflow_info = chat_agent.query_with_path(user_message, chat_history, session_id)
        
        # Save user message to DynamoDB
        db_manager.add_chat_message(
            session_id=session_id,
            role='user',
            content=user_message,
            metadata={
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent')
            }
        )
        
        # Save assistant response to DynamoDB
        db_manager.add_chat_message(
            session_id=session_id,
            role='assistant',
            content=response,
            metadata={
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent')
            }
        )
        
        # Update session with latest activity
        db_manager.update_session(session_id, last_message_at=workflow_info.get('timestamp'))
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'response': response,
                'session_id': session_id,
                'workflow_path': workflow_info.get('path', []),
                'intent_type': workflow_info.get('intent_type'),
                'final_agent': workflow_info.get('final_agent'),
                'message': user_message
            })
        }
    except Exception as e:
        print(f"Error in handle_chat_request: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_list_sessions(event, headers):
    """Handle GET /sessions - list all sessions"""
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 20))
        
        sessions = db_manager.list_sessions(limit=limit)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'sessions': sessions,
                'count': len(sessions)
            })
        }
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Error listing sessions: {str(e)}'})
        }

def handle_get_session(event, headers):
    """Handle GET /sessions/{session_id} - get session details and history"""
    try:
        # Extract session_id from path parameters
        path_params = event.get('pathParameters', {}) or {}
        session_id = path_params.get('session_id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Session ID is required'})
            }
        
        # Get session details
        session = db_manager.get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Session not found'})
            }
        
        # Get chat history
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 50))
        chat_history = db_manager.get_chat_history(session_id, limit=limit)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'session': session,
                'chat_history': chat_history,
                'message_count': len(chat_history)
            })
        }
    except Exception as e:
        print(f"Error getting session: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Error getting session: {str(e)}'})
        }

def handle_delete_session(event, headers):
    """Handle DELETE /sessions/{session_id} - delete session and all messages"""
    try:
        # Extract session_id from path parameters
        path_params = event.get('pathParameters', {}) or {}
        session_id = path_params.get('session_id')
        
        if not session_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Session ID is required'})
            }
        
        # Check if session exists
        session = db_manager.get_session(session_id)
        if not session:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Session not found'})
            }
        
        # Delete session and all messages
        db_manager.delete_session(session_id)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Session deleted successfully',
                'session_id': session_id
            })
        }
    except Exception as e:
        print(f"Error deleting session: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Error deleting session: {str(e)}'})
        } 