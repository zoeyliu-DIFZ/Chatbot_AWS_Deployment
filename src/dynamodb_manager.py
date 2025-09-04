import boto3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

class DynamoDBManager:
    """DynamoDB manager for chat sessions and history"""
    
    def __init__(self):
        # Use AWS session with proper configuration
        self.session = boto3.Session()
        self.dynamodb = self.session.resource('dynamodb')
        
        # Get table names from environment or use defaults
        self.session_table_name = os.environ.get('SESSION_TABLE', 'ai-chat-session-dev')
        self.history_table_name = os.environ.get('HISTORY_TABLE', 'ai-chat-history-dev')
        
        # Local storage for development when DynamoDB is not available
        self.local_sessions = {}
        self.local_messages = {}
        
        # Test AWS credentials first
        self._test_aws_credentials()
        
        try:
            self.session_table = self.dynamodb.Table(self.session_table_name)
            self.history_table = self.dynamodb.Table(self.history_table_name)
            
            # Test table access
            self._test_table_access()
            
            self.use_local = False
            print(f"✅ Connected to DynamoDB tables: {self.session_table_name}, {self.history_table_name}")
        except Exception as e:
            print(f"❌ Error connecting to DynamoDB: {e}")
            print("   Using local storage for development")
            self.session_table = None
            self.history_table = None
            self.use_local = True
    
    def _test_aws_credentials(self):
        """Test AWS credentials"""
        try:
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS credentials valid. Account: {identity['Account']}, User: {identity['Arn']}")
        except Exception as e:
            print(f"❌ AWS credentials error: {e}")
            print("   Please check your AWS credentials configuration")
    
    def _test_table_access(self):
        """Test access to DynamoDB tables"""
        try:
            # Test session table access
            self.session_table.load()
            print(f"✅ Session table '{self.session_table_name}' accessible")
        except Exception as e:
            print(f"❌ Cannot access session table '{self.session_table_name}': {e}")
            raise e
        
        try:
            # Test history table access
            self.history_table.load()
            print(f"✅ History table '{self.history_table_name}' accessible")
        except Exception as e:
            print(f"❌ Cannot access history table '{self.history_table_name}': {e}")
            raise e
    
    def create_session(self, session_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Create a new chat session"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        timestamp = datetime.utcnow().isoformat()
        
        session_item = {
            'session_id': session_id,
            'created_at': timestamp,
            'updated_at': timestamp,
            'message_count': 0,
            'metadata': metadata or {}
        }
        
        if self.use_local:
            # Store locally
            self.local_sessions[session_id] = session_item
            print(f"✅ Created local session: {session_id}")
        else:
            # Store in DynamoDB
            try:
                self.session_table.put_item(Item=session_item)
                print(f"✅ Created DynamoDB session: {session_id}")
            except Exception as e:
                print(f"❌ Error creating DynamoDB session: {e}")
                print(f"   Error details: {type(e).__name__}: {str(e)}")
                # Fallback to local storage
                self.local_sessions[session_id] = session_item
                print(f"✅ Created local session (fallback): {session_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if self.use_local:
            return self.local_sessions.get(session_id)
        
        try:
            response = self.session_table.get_item(Key={'session_id': session_id})
            return response.get('Item')
        except Exception as e:
            print(f"❌ Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, **kwargs):
        """Update session information"""
        timestamp = datetime.utcnow().isoformat()
        
        if self.use_local:
            if session_id in self.local_sessions:
                self.local_sessions[session_id]['updated_at'] = timestamp
                for key, value in kwargs.items():
                    self.local_sessions[session_id][key] = value
        else:
            try:
                update_expression = "SET updated_at = :updated_at"
                expression_values = {':updated_at': timestamp}
                
                for key, value in kwargs.items():
                    update_expression += f", {key} = :{key}"
                    expression_values[f':{key}'] = value
                
                self.session_table.update_item(
                    Key={'session_id': session_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values
                )
            except Exception as e:
                print(f"❌ Error updating session {session_id}: {e}")
    
    def add_chat_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add a chat message to history"""
        timestamp = datetime.utcnow().isoformat()
        message_id = str(uuid.uuid4())
        
        message_item = {
            'session_id': session_id,
            'timestamp': timestamp,
            'message_id': message_id,
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'metadata': metadata or {}
        }
        
        if self.use_local:
            # Store locally
            if session_id not in self.local_messages:
                self.local_messages[session_id] = []
            self.local_messages[session_id].append(message_item)
            
            # Update session message count
            if session_id in self.local_sessions:
                self.local_sessions[session_id]['message_count'] = len(self.local_messages[session_id])
        else:
            # Store in DynamoDB
            try:
                self.history_table.put_item(Item=message_item)
                
                # Update session message count
                self.update_session(session_id, message_count=self.get_session_message_count(session_id) + 1)
            except Exception as e:
                print(f"❌ Error adding chat message to DynamoDB: {e}")
                print(f"   Error details: {type(e).__name__}: {str(e)}")
                # Fallback to local storage
                if session_id not in self.local_messages:
                    self.local_messages[session_id] = []
                self.local_messages[session_id].append(message_item)
        
        return message_id
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        if self.use_local:
            messages = self.local_messages.get(session_id, [])
            # Sort by timestamp and limit
            messages.sort(key=lambda x: x['timestamp'])
            return messages[-limit:] if limit > 0 else messages
        
        try:
            print(f"🔍 Querying DynamoDB for session: {session_id}")
            response = self.history_table.query(
                KeyConditionExpression='session_id = :session_id',
                ExpressionAttributeValues={':session_id': session_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            # Reverse to get chronological order
            messages = response.get('Items', [])
            print(f"📊 DynamoDB returned {len(messages)} messages for session {session_id}")
            messages.reverse()
            return messages
        except Exception as e:
            print(f"❌ Error getting chat history for session {session_id}: {e}")
            return []
    
    def get_session_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session"""
        if self.use_local:
            return len(self.local_messages.get(session_id, []))
        
        try:
            response = self.history_table.query(
                KeyConditionExpression='session_id = :session_id',
                ExpressionAttributeValues={':session_id': session_id},
                Select='COUNT'
            )
            return response.get('Count', 0)
        except Exception as e:
            print(f"❌ Error getting message count for session {session_id}: {e}")
            return 0
    
    def delete_session(self, session_id: str):
        """Delete a session and all its messages"""
        if self.use_local:
            # Delete from local storage
            if session_id in self.local_sessions:
                del self.local_sessions[session_id]
            if session_id in self.local_messages:
                del self.local_messages[session_id]
            print(f"✅ Deleted local session: {session_id}")
        else:
            try:
                # Delete all messages in the session
                messages = self.get_chat_history(session_id, limit=1000)
                for message in messages:
                    self.history_table.delete_item(
                        Key={
                            'session_id': session_id,
                            'timestamp': message['timestamp']
                        }
                    )
                
                # Delete the session
                self.session_table.delete_item(Key={'session_id': session_id})
                print(f"✅ Deleted DynamoDB session: {session_id}")
            except Exception as e:
                print(f"❌ Error deleting session {session_id}: {e}")
    
    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent sessions"""
        if self.use_local:
            sessions = list(self.local_sessions.values())
            # Sort by updated_at and limit
            sessions.sort(key=lambda x: x['updated_at'], reverse=True)
            return sessions[:limit]
        
        try:
            response = self.session_table.scan(
                Limit=limit,
                ProjectionExpression='session_id, created_at, updated_at, message_count'
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get DynamoDB connection status"""
        return {
            'connected': not self.use_local,
            'session_table': self.session_table_name,
            'history_table': self.history_table_name,
            'local_sessions_count': len(self.local_sessions),
            'local_messages_count': sum(len(messages) for messages in self.local_messages.values())
        }

# Global instance
db_manager = DynamoDBManager()
