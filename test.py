#pip install roboflow

from roboflow import Roboflow
rf = Roboflow(api_key="UWOU2vqDDSIsfBphWxJU")
project = rf.workspace().project("health-bqeyj")
model = project.version(1).model

# Predict an image
prediction = model.predict(r"C:\Users\HP\Desktop\k.jpg").json()


# Display result clearly
for pred in prediction["predictions"]:
    class_name = pred["class"]
    confidence = round(pred["confidence"] * 100, 2)
    print(f"🩺 Detected: {class_name} ({confidence}% confidence)")
