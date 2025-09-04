#!/usr/bin/env python3
"""
Local development environment setup script
Automatically start API and frontend servers
"""

import subprocess
import webbrowser
import time
import os
import signal
import sys
from pathlib import Path

class LocalDevEnvironment:
    def __init__(self):
        self.processes = []
        self.api_port = 5000
        self.frontend_port = 8001
        
    def check_dependencies(self):
        """Check if dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        try:
            import uvicorn
            import fastapi
            print("✅ FastAPI and Uvicorn are installed")
        except ImportError:
            print("❌ FastAPI or Uvicorn not found. Please install dependencies:")
            print("   pip install -r requirements-dev.txt")
            return False
        
        # Check AWS credentials
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            print("⚠️  Warning: AWS_ACCESS_KEY_ID not found")
            print("   Make sure your AWS credentials are set up for Bedrock access")
        
        return True
    
    def start_api_server(self):
        """Start local API server"""
        print(f"🚀 Starting API server on port {self.api_port}...")
        
        try:
            process = subprocess.Popen([
                sys.executable, "local_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(("API Server", process))
            print(f"✅ API server started (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return False
    
    def start_frontend_server(self):
        """Start frontend server"""
        print(f"🌐 Starting frontend server on port {self.frontend_port}...")
        
        # Check if index_local.html exists (created by update_frontend_config)
        index_file = Path("index_local.html")
        if not index_file.exists():
            print("❌ index_local.html not found. Please run update_frontend_config first.")
            return False
        
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "http.server", str(self.frontend_port)
            ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(("Frontend Server", process))
            print(f"✅ Frontend server started (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return False
    
    def update_frontend_config(self):
        """Update frontend configuration to connect to local API"""
        frontend_file = Path("update-frontend/frontend/index.html")
        
        if not frontend_file.exists():
            print("❌ update-frontend/frontend/index.html not found")
            return False
        
        try:
            content = frontend_file.read_text()
            
            # Find and replace API endpoint
            if "YOUR_API_GATEWAY_URL_HERE" in content:
                content = content.replace(
                    "const API_ENDPOINT = 'YOUR_API_GATEWAY_URL_HERE';",
                    f"const API_ENDPOINT = 'http://localhost:{self.api_port}/chat';"
                )
                
                # Create local configuration file
                local_file = Path("index_local.html")
                local_file.write_text(content)
                
                print("✅ Created local frontend configuration")
                print(f"   Source: {frontend_file}")
                print(f"   Local: {local_file}")
                return True
            else:
                print("⚠️  API endpoint already configured")
                return True
                
        except Exception as e:
            print(f"❌ Failed to update frontend config: {e}")
            return False
    
    def wait_for_servers(self):
        """Wait for servers to start"""
        print("⏳ Waiting for servers to start...")
        time.sleep(3)
        
        # Check if servers are responding
        try:
            import requests
            
            # Check API server
            response = requests.get(f"http://localhost:{self.api_port}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server is responding")
            else:
                print("⚠️  API server may not be ready")
                
        except Exception as e:
            print(f"⚠️  Could not verify API server status: {e}")
    
    def open_browser(self):
        """Open browser"""
        print("🌐 Opening browser...")
        
        # Use local frontend configuration if available
        if Path("index_local.html").exists():
            url = f"http://localhost:{self.frontend_port}/index_local.html"
        else:
            url = f"http://localhost:{self.frontend_port}"
        
        try:
            webbrowser.open(url)
            print(f"✅ Browser opened: {url}")
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
            print(f"   Please manually open: {url}")
    
    def display_info(self):
        """Display development environment information"""
        print("\n" + "="*60)
        print("🎉 Local Development Environment Started!")
        print("="*60)
        print(f"📍 API Server:      http://localhost:{self.api_port}")
        print(f"📖 API Docs:        http://localhost:{self.api_port}/docs")
        print(f"🌐 Frontend:        http://localhost:{self.frontend_port}")
        print(f"🔧 Health Check:    http://localhost:{self.api_port}/health")
        print("="*60)
        print("💡 Tips:")
        print("   - Make code changes and the API server will auto-reload")
        print("   - Use Ctrl+C to stop all servers")
        print("   - Check the terminal for any error messages")
        print("="*60)
    
    def cleanup(self):
        """Clean up processes"""
        print("\n🧹 Cleaning up...")
        
        for name, process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"   Stopping {name} (PID: {process.pid})")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        # Delete temporary file
        temp_file = Path("index_local.html")
        if temp_file.exists():
            temp_file.unlink()
            print("   Removed temporary frontend file")
        
        print("✅ Cleanup completed")
    
    def run(self):
        """Run development environment"""
        print("🚀 Setting up Local Development Environment")
        print("="*50)
        
        # Check dependencies
        if not self.check_dependencies():
            return
        
        try:
            # Update frontend configuration first
            if not self.update_frontend_config():
                return
            
            # Start servers
            if not self.start_api_server():
                return
            
            if not self.start_frontend_server():
                return
            
            # Wait for servers to start
            self.wait_for_servers()
            
            # Open browser
            self.open_browser()
            
            # Display information
            self.display_info()
            
            # Wait for user to stop
            print("\nPress Ctrl+C to stop all servers...")
            
            while True:
                # Check if processes are still running
                running_processes = [p for name, p in self.processes if p.poll() is None]
                if not running_processes:
                    print("❌ All servers have stopped")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping development environment...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.cleanup()

def main():
    """Main function"""
    env = LocalDevEnvironment()
    env.run()

if __name__ == "__main__":
    main() 