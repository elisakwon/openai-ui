from flask import Flask, request, jsonify, render_template, send_from_directory
from requests_oauthlib import OAuth1
import requests
import base64
import time
from openai import OpenAI
import logging
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
import time
import os
app = Flask(__name__)

# API Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Logging setup
logging.basicConfig(
    filename='flask_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

folder_name = "UPLOAD_FOLDER"  # Create valid directory 
#os.mkdir(UPLOAD_FOLDER, exist_ok=True)
#app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def home():
    """Interactive form for user input."""
    return render_template('index.html')  # Render a form to accept the user's prompt.


@app.route('/process-comment', methods=['POST'])
def process_comment():
    """Fetch image, text, and generate text"""
    try:
        # Step 0: Fetch the prompt/description from the form
        prompt = request.form.get('prompt')
        logging.info(f"prompt: {prompt}")
        dev_prompt = "The Geneplore model is a dual process model of creativity that defines generative and exploratory " \
                     "processes. Generation involves the initial construction of preinventive structures, defined as " \
                     "precursors to final creative results that are subsequently interpreted and transformed following " \
                     "exploration.  In the Geneplore model, properties of preinventive structures that emerge in " \
                     "design concepts are examined during exploration and are then refined and expanded under further " \
                     "generative processes. The image and description you will be provided includes a redesign of an " \
                     "IKEA cabinet, consisting of top, bottom, side, front and center panels and 4 legs. " \
                     "Using this knowledge, identify and list new preinventive structures in the submitted design idea " \
                     "to inspire further idea generation."

        user_prompt = "My idea is: " + prompt

        # Step 1: Check if an image file was uploaded
        if 'image' in request.files:
            image_file = request.files['image']

            # Convert image to base64
            image = Image.open(image_file)
            buffered = BytesIO()
            image.save(buffered, format="PNG")  # Ensure it's in PNG format
            base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

            logging.info("Image received and converted to base64.")
            timestamp = int(time.time())
            filename = secure_filename(f"{timestamp}_{image_file.filename}")
            image_path = os.path.join(os.getcwd(), folder_name, filename)

            # Save the image directly
            image.save(image_path)

        else:
            base64_image is None
            logging.info("No image uploaded.")

        # Step 2: Generate OpenAI text response
        try:
            # Make the API request -- new gpt-4.1 and client.responses.create (vs. chat completion)
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "developer",
                        "content": dev_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": user_prompt},
                            {"type": "input_image",
                             "image_url": f"data:image/jpeg;base64,{base64_image}"}
                        ]
                    }
                ],
            )

            ai_response = response.output_text  # response.choices[0].message.content
            logging.info(f"AI-generated response: {ai_response}")
            return jsonify({"message": "Comment added successfully.", "ai_response": ai_response})

        except Exception as e:
            logging.error(f"Error during OpenAI API call: {str(e)}")
            return jsonify({"error": "Failed to generate text."}), 500

    except Exception as e:
        logging.error(f"Exception in /process-comment: {str(e)}")
        return jsonify({"Text prompt error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

