#pip install roboflow

# from roboflow import Roboflow

# # Load Roboflow model
# print("Loading Roboflow workspace...")
# rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")

# print("Loading Roboflow project...")
# project = rf.workspace("telemedicneproject").project("classification_data")
# model = project.version(3).model

# # Predict image
# image_path = r"C:\Users\HP\Desktop\a.jpg"
# prediction = model.predict(image_path).json()

# # Debug: Print full prediction dictionary
# print("Full prediction result:", prediction)

# # Safely parse prediction
# if "top" in prediction:  # Classification model
#     class_name = prediction["top"]["class"]
#     confidence = round(prediction["top"]["confidence"] * 100, 2)
#     print(f"🩺 Predicted Class: {class_name} ({confidence}% confidence)")

# elif "predictions" in prediction and prediction["predictions"]:  # Detection model
#     for pred in prediction["predictions"]:
#         class_name = pred.get("class", "Unknown")
#         confidence = round(pred.get("confidence", 0) * 100, 2)
#         print(f"🩺 Detected: {class_name} ({confidence}% confidence)")

# else:
#     print("⚠️ No predictions were returned. Check image quality or model status.")




#pip install roboflow

# from roboflow import Roboflow
# rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")
# project = rf.workspace().project("health-bqeyj")
# model = project.version(1).model

# # Predict an image
# prediction = model.predict(r"C:\Users\HP\Desktop\k.jpg").json()

# # Display result clearly
# for pred in prediction["predictions"]:
#     class_name = pred["class"]
#     confidence = round(pred["confidence"] * 100, 2)
#     print(f"🩺 Detected: {class_name} ({confidence}% confidence)")


#pip install roboflow

# from roboflow import Roboflow
# rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")
# project = rf.workspace("Telemedicneproject").project("skin-d7dr2")
# model = project.version(2).model

# # Predict an image
# prediction = model.predict(r"C:\Users\HP\Desktop\v.jpg").json()

# # Display result clearly
# for pred in prediction["predictions"]:
#     class_name = pred["class"]
#     confidence = round(pred["confidence"] * 100, 2)
#     print(f"🩺 Detected: {class_name} ({confidence}% confidence)")

'''
For single model 
'''
# from inference_sdk import InferenceHTTPClient

# CLIENT = InferenceHTTPClient(
#     api_url="https://serverless.roboflow.com",
#     api_key="UWOU2vqDDSIsfBphWxJU"
# )

# result = CLIENT.infer(r"C:\Users\HP\Desktop\ringworm-facts.jpg", model_id="skin-d7dr2/2")

# # Get predictions dictionary
# predictions = result["predictions"]

# # Get top class (max confidence)
# top_class = max(predictions.items(), key=lambda x: x[1]["confidence"])

# # Print single classification result
# print(f"Predicted class: {top_class[0]} with {top_class[1]['confidence']*100:.2f}% confidence")


import os
from inference_sdk import InferenceHTTPClient

# Initialize the Roboflow client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="UWOU2vqDDSIsfBphWxJU"
)

# Define model categories and their Roboflow model IDs
MODEL_IDS = {
    "Skin": "skin-d7dr2/2",
    "Teeth": "dental-gjlh1/1",
    "Eyes": "classification_data/3",
    "Hair": "hair-disease-detection-o2ok0-vqwpb/1"
}

def analyze_medical_image(image_path: str) -> str:
    """Analyze a medical image using multiple Roboflow models and return detected conditions."""
    if not os.path.exists(image_path):
        return f"❌ Image not found: {image_path}"

    report = []

    for category, model_id in MODEL_IDS.items():
        try:
            result = CLIENT.infer(image_path, model_id=model_id)

            predictions = result.get("predictions", {})
            if not predictions:
                report.append(f"✅ {category}: No issues detected.")
                continue

            # Find the class with the highest confidence
            top_class = max(predictions.items(), key=lambda x: x[1]["confidence"])
            class_name = top_class[0]
            confidence = round(top_class[1]["confidence"] * 100, 2)
            report.append(f"🩺 {category} - {class_name} ({confidence}% confidence)")

        except Exception as e:
            report.append(f"⚠️ {category}: Error analyzing - {str(e)}")

    return "\n".join(report)


