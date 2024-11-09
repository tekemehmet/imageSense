from flask import Flask, request, jsonify, render_template
from PIL import Image
from io import BytesIO
import base64
import os
from openai import OpenAI
import re

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # correct model name
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Provide:\n1. Description (max 200 characters)\n2. Keywords: followed by 50 relevant comma-separated single-word keywords"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                    ],
                }
            ],
            max_tokens=1000
        )
        
        # Process the response
        text_output = response.choices[0].message.content.strip()
        description_match = re.search(r"\*\*Description:\*\* (.+?)(?=\n|$)", text_output)
        keywords_match = re.search(r"\*\*Keywords:\*\* (.+?)(?=\n|$)", text_output)

        description = description_match.group(1) if description_match else ""
        keywords = keywords_match.group(1).split(", ") if keywords_match else []
        return description, keywords
    except Exception as e:
        print(f"Error generating description and keywords: {e}")
        return "", []

if __name__ == '__main__':
    app.run(debug=True)
