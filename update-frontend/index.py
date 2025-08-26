import json
import boto3
import urllib3
import os
import re

s3_client = boto3.client('s3')

def send_response(event, context, response_status, response_data=None, physical_resource_id=None):
    """Send response to CloudFormation"""
    if response_data is None:
        response_data = {}
    
    if physical_resource_id is None:
        physical_resource_id = context.log_stream_name
    
    response_url = event['ResponseURL']
    response_body = {
        'Status': response_status,
        'Reason': f'See CloudWatch Log Stream: {context.log_stream_name}',
        'PhysicalResourceId': physical_resource_id,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    }
    
    json_response_body = json.dumps(response_body)
    
    headers = {
        'content-type': '',
        'content-length': str(len(json_response_body))
    }
    
    http = urllib3.PoolManager()
    try:
        response = http.request('PUT', response_url, body=json_response_body, headers=headers)
        print(f"CloudFormation response status: {response.status}")
    except Exception as e:
        print(f"Failed to send response to CloudFormation: {e}")

def update_frontend_html(api_endpoint):
    """Update the frontend HTML with the correct API endpoint"""
    # Read the original frontend HTML from the local directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    html_path = os.path.join(frontend_dir, 'index.html')
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Use more flexible replacement logic
    # Replace the assignment statement with flexible whitespace handling
    updated_html = re.sub(
        r"const\s+API_ENDPOINT\s*=\s*['\"]YOUR_API_GATEWAY_URL_HERE['\"]\s*;",
        f"const API_ENDPOINT = '{api_endpoint}';",
        html_content,
        flags=re.MULTILINE
    )
    
    return updated_html

def handler(event, context):
    """Lambda handler for custom resource"""
    print(f"Event: {json.dumps(event, indent=2)}")
    
    try:
        request_type = event['RequestType']
        properties = event['ResourceProperties']
        
        api_endpoint = properties['ApiEndpoint']
        bucket_name = properties['BucketName']
        environment = properties['Environment']
        
        if request_type in ['Create', 'Update']:
            # Read frontend files from the deployment package
            # In Lambda, the frontend directory should be at the same level as the handler
            frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
            print(f"Looking for frontend files in: {frontend_dir}")
            
            # Check if frontend directory exists
            if not os.path.exists(frontend_dir):
                print(f"Frontend directory not found at: {frontend_dir}")
                # Try alternative paths
                alternative_paths = [
                    'frontend',
                    '/opt/frontend',
                    '/var/task/frontend'
                ]
                for alt_path in alternative_paths:
                    if os.path.exists(alt_path):
                        frontend_dir = alt_path
                        print(f"Found frontend directory at: {frontend_dir}")
                        break
                else:
                    raise Exception(f"Frontend directory not found. Checked paths: {[frontend_dir] + alternative_paths}")
            
            # List all files in frontend directory
            print(f"Files in frontend directory: {os.listdir(frontend_dir)}")
            
            # Upload all frontend files to S3
            for root, dirs, files in os.walk(frontend_dir):
                print(f"Walking directory: {root}, found files: {files}")
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = os.path.relpath(local_path, frontend_dir)
                    print(f"Processing file: {local_path} -> S3 key: {s3_key}")
                    
                    if file == 'index.html':
                        # Update HTML with API endpoint
                        with open(local_path, 'r') as f:
                            html_content = f.read()
                        
                        # Use more flexible replacement logic
                        # Replace the assignment statement with flexible whitespace handling
                        updated_html = re.sub(
                            r"const\s+API_ENDPOINT\s*=\s*['\"]YOUR_API_GATEWAY_URL_HERE['\"]\s*;",
                            f"const API_ENDPOINT = '{api_endpoint}';",
                            html_content,
                            flags=re.MULTILINE
                        )
                        
                        # Upload updated HTML
                        print(f"Uploading updated HTML to S3: {bucket_name}/{s3_key}")
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=s3_key,
                            Body=updated_html,
                            ContentType='text/html'
                        )
                        print(f"Successfully uploaded updated HTML")
                    else:
                        # Upload other files as-is
                        content_type = 'text/css' if file.endswith('.css') else 'application/javascript' if file.endswith('.js') else 'text/plain'
                        print(f"Uploading file to S3: {bucket_name}/{s3_key}")
                        with open(local_path, 'rb') as f:
                            s3_client.put_object(
                                Bucket=bucket_name,
                                Key=s3_key,
                                Body=f.read(),
                                ContentType=content_type
                            )
                        print(f"Successfully uploaded: {file}")
            
            print(f"Successfully uploaded frontend files to {bucket_name}")
            send_response(event, context, 'SUCCESS', {'Message': 'Frontend updated successfully'})
        
        elif request_type == 'Delete':
            # Clean up S3 bucket contents on stack deletion
            try:
                # List all objects in bucket
                response = s3_client.list_objects_v2(Bucket=bucket_name)
                if 'Contents' in response:
                    # Delete all objects
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                    s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                print(f"Cleaned up bucket {bucket_name}")
            except Exception as e:
                print(f"Error cleaning up bucket: {e}")
            
            send_response(event, context, 'SUCCESS', {'Message': 'Cleanup completed'})
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        send_response(event, context, 'FAILED', {'Error': str(e)}) 