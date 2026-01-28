#!/usr/bin/env python
"""
Quick test script for Kokoro TTS installation
"""
import subprocess
import tempfile
import os
from pathlib import Path

def test_kokoro_installation():
    """Test if Kokoro TTS is properly installed"""
    print("🧪 Testing Kokoro TTS Installation")
    print("=" * 50)
    
    # Test 1: Check if kokoro-tts command is available
    print("\n1. Checking kokoro-tts command...")
    try:
        result = subprocess.run(
            ["kokoro-tts", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print("   ✅ kokoro-tts command found")
    except FileNotFoundError:
        print("   ❌ kokoro-tts command not found")
        print("   💡 Install with: pip install kokoro-tts")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Check available voices
    print("\n2. Checking available voices...")
    try:
        result = subprocess.run(
            ["kokoro-tts", "--help-voices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        voices = result.stdout
        print(f"   ✅ Found voices (showing first 300 chars):")
        print(f"   {voices[:300]}...")
    except Exception as e:
        print(f"   ⚠️ Could not list voices: {e}")
    
    # Test 3: Check available languages
    print("\n3. Checking available languages...")
    try:
        result = subprocess.run(
            ["kokoro-tts", "--help-languages"],
            capture_output=True,
            text=True,
            timeout=5
        )
        languages = result.stdout
        print(f"   ✅ Supported languages:")
        print(f"   {languages}")
    except Exception as e:
        print(f"   ⚠️ Could not list languages: {e}")
    
    # Test 4: Generate a test audio file
    print("\n4. Testing audio generation...")
    test_text = "Hello, this is a test of Kokoro TTS in English. This is a local model that could be used to generate podcasts based on Pumed's recent articles."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_text)
        temp_txt = f.name
    
    temp_wav = tempfile.mktemp(suffix='.wav')
    
    try:
        result = subprocess.run(
            [
                "kokoro-tts",
                temp_txt,
                temp_wav,
                "--lang", "en-us",
                "--voice", "af_sarah",
                "--speed", "1.0"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if Path(temp_wav).exists():
            file_size = Path(temp_wav).stat().st_size
            print(f"   ✅ Audio generated successfully!")
            print(f"   📁 File size: {file_size} bytes")
            print(f"   📍 Location: {temp_wav}")
            
            # Cleanup
            os.unlink(temp_wav)
            print("   🗑️ Test file cleaned up")
        else:
            print(f"   ❌ Audio file was not created")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("   ❌ Audio generation timed out")
    except Exception as e:
        print(f"   ❌ Error generating audio: {e}")
    finally:
        # Cleanup text file
        try:
            os.unlink(temp_txt)
        except:
            pass
    
    print("\n" + "=" * 50)
    print("✅ Kokoro TTS test complete!")
    return True

if __name__ == "__main__":
    test_kokoro_installation()
