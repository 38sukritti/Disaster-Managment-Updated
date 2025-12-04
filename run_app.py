#!/usr/bin/env python3
"""
Quick setup and run script for the disaster management app
"""
import os
import subprocess
import sys

def install_requirements():
    """Install minimal requirements"""
    print("Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements_simple.txt"])
        print("✅ Requirements installed!")
        return True
    except:
        print("❌ Error installing requirements")
        return False

def setup_env():
    """Setup environment file"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write('GROQ_API_KEY=your_groq_api_key_here\n')
        print("📝 Created .env file - please add your Groq API key")
        return False
    
    with open('.env', 'r') as f:
        if 'your_groq_api_key_here' in f.read():
            print("⚠️  Please update GROQ_API_KEY in .env file")
            print("Get key from: https://console.groq.com/")
            return False
    
    print("✅ Environment configured!")
    return True

def run_app():
    """Run the Flask app"""
    print("🚀 Starting the app...")
    os.system("python app.py")

def test_pydantic_models():
    """Test Pydantic models"""
    print("Testing Pydantic models...")
    try:
        result = subprocess.run([sys.executable, "test_models.py"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Pydantic models working correctly!")
            return True
        else:
            print(f"❌ Pydantic model tests failed")
            return False
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Disaster Management AI Chatbot with Pydantic Setup")
    print("=" * 55)
    
    if install_requirements():
        models_ok = test_pydantic_models()
        env_ready = setup_env()
        
        if env_ready and models_ok:
            print("\n🎉 All systems ready!")
            print("Commands available:")
            print("  python app.py        - Start the application")
            print("  python test_models.py - Test Pydantic validation")
            print("  python test_api.py   - Test API endpoints")
            run_app()
        else:
            print("\n📋 Next steps:")
            if not env_ready:
                print("1. Get API key: https://console.groq.com/")
                print("2. Update .env file with your key")
            if not models_ok:
                print("3. Fix Pydantic model issues")
            print("4. Run: python run_app.py")