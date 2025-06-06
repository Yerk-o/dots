from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import re
import time
import random

app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyC9cSq5TVfTjBVbJ2jb9l5NwmfdrsqRf8I"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_pattern_from_keywords(text):
    """
    Fallback function that creates patterns based on keywords when AI fails
    """
    text_lower = text.lower()
    
    # Default values
    params = {
        "speed": 1.0,
        "attraction": 0.08,
        "repulsion": 30,
        "wander": 0.1,
        "cluster": 0.2,
        "homeForce": 0.003,
        "interpretation": "Pattern generated using keyword analysis (AI fallback)"
    }
    
    # Energetic/Fast keywords
    if any(word in text_lower for word in ['storm', 'lightning', 'explosion', 'fast', 'energetic', 'chaotic', 'wild']):
        params.update({
            "speed": random.uniform(1.5, 2.0),
            "wander": random.uniform(0.3, 0.5),
            "repulsion": random.uniform(40, 60),
            "cluster": random.uniform(0.05, 0.15),
            "interpretation": "High energy pattern detected - fast movement with chaos"
        })
    
    # Calm/Peaceful keywords
    elif any(word in text_lower for word in ['calm', 'peaceful', 'gentle', 'slow', 'meditation', 'quiet', 'serene']):
        params.update({
            "speed": random.uniform(0.2, 0.6),
            "attraction": random.uniform(0.02, 0.06),
            "wander": random.uniform(0.02, 0.08),
            "homeForce": random.uniform(0.005, 0.01),
            "interpretation": "Calm pattern detected - slow, gentle movement"
        })
    
    # Water/Ocean keywords
    elif any(word in text_lower for word in ['water', 'ocean', 'wave', 'river', 'flow', 'current']):
        params.update({
            "speed": random.uniform(0.6, 1.2),
            "attraction": random.uniform(0.06, 0.12),
            "wander": random.uniform(0.08, 0.15),
            "cluster": random.uniform(0.15, 0.3),
            "interpretation": "Fluid motion pattern - flowing like water"
        })
    
    # Social/Love keywords
    elif any(word in text_lower for word in ['love', 'together', 'family', 'friends', 'group', 'community']):
        params.update({
            "attraction": random.uniform(0.12, 0.18),
            "cluster": random.uniform(0.3, 0.45),
            "repulsion": random.uniform(15, 25),
            "interpretation": "Social clustering pattern - particles drawn together"
        })
    
    # Sad/Melancholy keywords
    elif any(word in text_lower for word in ['sad', 'lonely', 'melancholy', 'depression', 'isolated']):
        params.update({
            "speed": random.uniform(0.3, 0.7),
            "attraction": random.uniform(0.02, 0.05),
            "repulsion": random.uniform(35, 55),
            "wander": random.uniform(0.05, 0.12),
            "interpretation": "Melancholic pattern - slower, more isolated movement"
        })
    
    return params

def analyze_text_for_pattern_with_retry(text, max_retries=3):
    """
    Analyze text with retry logic and fallback to keyword analysis
    """
    prompt = f"""
    Analyze this text and convert it into parameters for a cellular automata/particle system animation: "{text}"
    
    Based on the meaning, emotion, and imagery of this text, provide values for these parameters:
    - speed: 0.1 to 2.0 (how fast particles move)
    - attraction: 0.0 to 0.2 (how much particles attract each other)
    - repulsion: 10 to 60 (minimum distance between particles)
    - wander: 0.0 to 0.5 (randomness in movement)
    - cluster: 0.0 to 0.5 (tendency to form groups)
    - homeForce: 0.001 to 0.01 (pull back to original position)
    
    Consider:
    - Energetic/exciting words = higher speed, more wander
    - Calm/peaceful words = lower speed, higher homeForce
    - Social/love themes = higher attraction, higher cluster
    - Chaos/conflict = higher wander, lower cluster
    - Nature themes = moderate values with gentle variations
    
    Respond ONLY with a valid JSON object like this:
    {{
        "speed": 1.2,
        "attraction": 0.08,
        "repulsion": 30,
        "wander": 0.15,
        "cluster": 0.25,
        "homeForce": 0.003,
        "interpretation": "Brief explanation of why these values match the text"
    }}
    """
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting Gemini API call {attempt + 1}/{max_retries}...")
            
            # Configure generation with timeout
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500,
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={'timeout': 30}  # Shorter timeout
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parameters = json.loads(json_str)
                
                # Validate and clamp values
                parameters['speed'] = max(0.1, min(2.0, parameters.get('speed', 1.0)))
                parameters['attraction'] = max(0.0, min(0.2, parameters.get('attraction', 0.08)))
                parameters['repulsion'] = max(10, min(60, parameters.get('repulsion', 30)))
                parameters['wander'] = max(0.0, min(0.5, parameters.get('wander', 0.1)))
                parameters['cluster'] = max(0.0, min(0.5, parameters.get('cluster', 0.2)))
                parameters['homeForce'] = max(0.001, min(0.01, parameters.get('homeForce', 0.003)))
                
                print("✅ Gemini API success!")
                return parameters
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                # Wait before retry with exponential backoff
                wait_time = (attempt + 1) * 2
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print("🔄 All AI attempts failed, using keyword fallback...")
                return get_pattern_from_keywords(text)
    
    # This shouldn't be reached, but just in case
    return get_pattern_from_keywords(text)

@app.route('/generate-pattern', methods=['POST'])
def generate_pattern():
    """
    API endpoint to generate cellular automata parameters from text
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({'error': 'Empty text provided'}), 400
        
        print(f"🎯 Generating pattern for: '{text}'")
        
        # Generate parameters with retry logic and fallback
        parameters = analyze_text_for_pattern_with_retry(text)
        
        # Add metadata
        response_data = {
            'success': True,
            'input_text': text,
            'parameters': parameters,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        print(f"✅ Pattern generated successfully!")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'})

@app.route('/test-ai', methods=['GET'])
def test_ai():
    """Test endpoint to check AI connectivity"""
    try:
        test_params = analyze_text_for_pattern_with_retry("calm ocean waves", max_retries=1)
        return jsonify({
            'ai_status': 'working',
            'test_result': test_params
        })
    except Exception as e:
        return jsonify({
            'ai_status': 'failed',
            'error': str(e),
            'fallback_available': True
        })

@app.route('/', methods=['GET'])
def home():
    """Basic home page with API info"""
    return jsonify({
        'message': 'Cellular Dots Pattern Generator API',
        'endpoints': {
            '/generate-pattern': 'POST - Generate parameters from text',
            '/health': 'GET - Health check',
            '/test-ai': 'GET - Test AI connectivity'
        },
        'example_request': {
            'url': '/generate-pattern',
            'method': 'POST',
            'body': {'text': 'flowing river under moonlight'}
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Cellular Dots AI API...")
    print("🔧 Testing initial AI connection...")
    
    # Test AI on startup
    try:
        test_result = analyze_text_for_pattern_with_retry("test", max_retries=1)
        print("✅ AI system ready!")
    except Exception as e:
        print(f"⚠️  AI system will use fallback mode: {e}")
    
    print("🌐 Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
