from flask import Flask, request, jsonify, render_template
import os
import re
from main import capture_audio_input
from tools import analyze_medical_image
from agents import search_agent, symptom_chain, connect_agent
from dotenv import load_dotenv

import traceback

load_dotenv()
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # Serve index.html from /templates

@app.route("/analyze", methods=["POST"])
def analyze_symptoms():
    try:
        mode = request.form.get("mode")
        user_input = ""

        if mode == "text":
            user_input = request.form.get("text", "").strip()

        elif mode == "audio":
            user_input = capture_audio_input()

        elif mode == "image":
            if 'image' not in request.files:
                return jsonify({"error": "No image file provided"}), 400

            image_file = request.files['image']
            image_path = f"./temp/{image_file.filename}"
            os.makedirs("temp", exist_ok=True)
            image_file.save(image_path)

            print(f"Image saved at {image_path}: Exists? {os.path.exists(image_path)}")

            category = request.form.get("image_category", "").strip().lower()
            if category not in ['skin', 'dental', 'eye', 'hair']:
                return jsonify({"error": "Invalid or missing image_category. Must be one of skin, dental, eye, hair."}), 400

            print(f"Analyzing image: {image_path} with category: {category}")
            image_result = analyze_medical_image(image_path, category)
            print(f"Image analysis result: {image_result}")

            match = re.search(r"Detected:\s*(.*?)\s*\(", image_result)
            if match:
                user_input = match.group(1)
            else:
                return jsonify({"error": "Could not interpret condition from image", "image_result": image_result}), 400

        else:
            return jsonify({"error": "Invalid mode. Use 'text', 'image', or 'audio'."}), 400

        if not user_input:
            return jsonify({"error": "No valid input provided."}), 400

        # Process using symptom_chain
        diagnosis = symptom_chain.run(user_input)

        # Check if escalation needed
        search_results = search_agent.invoke({"input": user_input})
        should_connect = connect_agent.invoke({"input": user_input})

        response = {"diagnosis": diagnosis}

        if should_connect.strip().lower() in ["yes", "true"]:
            response["meet_link"] = os.getenv("MEET_LINK", "https://meet.google.com/test-link")

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)