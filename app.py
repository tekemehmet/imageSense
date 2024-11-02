from flask import Flask, request, jsonify, render_template
from PIL import Image
from io import BytesIO
import openai
import base64
import os
import requests

app = Flask(__name__)

# Load your API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def home():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    # Receive image
    image_file = request.files['image']
    image = Image.open(image_file)

    # Convert image to a format suitable for LLM processing
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    image_bytes = buffered.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Generate image description and keywords
    description, keywords = generate_description_and_keywords(image_base64)

    return jsonify({'description': description, 'keywords': keywords})

def generate_description_and_keywords(image_base64):
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image and provide 50 relevant keywords:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                ],
            }
        ],
        "max_tokens": 300
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    
    data = response.json()
    
    # Process the response
    text_output = data['choices'][0]['message']['content'].strip()
    description, keywords = text_output.split('Keywords:', 1)
    keywords = [k.strip() for k in keywords.strip().split(',')]

    return description.strip(), keywords[:50]

if __name__ == '__main__':
    app.run(debug=True)
