#!/usr/bin/env python3
"""
Local testing script - directly test Agent business logic
No Web framework, directly call Python functions
"""

import sys
import os

# Add src directory to path
sys.path.append('src')

from agent import ChatAgent

def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing Agent Basic Functionality...")
    
    try:
        # Initialize agent
        agent = ChatAgent()
        print("✅ Agent initialized successfully")
        
        # Test basic conversation
        test_messages = [
            "Hello, how are you?",
            "What is artificial intelligence?",
            "Can you help me with Python programming?",
            "Tell me a joke"
        ]
        
        chat_history = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i} ---")
            print(f"🧑 User: {message}")
            
            # Call agent
            response = agent.query(message, chat_history)
            print(f"🤖 Assistant: {response}")
            
            # Update chat history
            chat_history.append(("human", message))
            chat_history.append(("assistant", response))
            
            # Keep chat history within reasonable range
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_interactive_mode():
    """Interactive testing mode"""
    print("\n🎮 Interactive Testing Mode")
    print("Type 'quit' or 'exit' to stop")
    print("-" * 50)
    
    try:
        agent = ChatAgent()
        chat_history = []
        
        while True:
            user_input = input("\n🧑 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Call agent
            response = agent.query(user_input, chat_history)
            print(f"🤖 Assistant: {response}")
            
            # Update chat history
            chat_history.append(("human", user_input))
            chat_history.append(("assistant", response))
            
            # Keep chat history within reasonable range
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
                
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 AI Chat Assistant - Local Testing")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("⚠️  Warning: AWS_ACCESS_KEY_ID not found in environment")
        print("   Make sure your AWS credentials are set up for Bedrock access")
    
    choice = input("\nChoose testing mode:\n1. Automated tests\n2. Interactive mode\n\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_basic_functionality()
    elif choice == "2":
        test_interactive_mode()
    else:
        print("Invalid choice. Running automated tests...")
        test_basic_functionality()

if __name__ == "__main__":
    main() 