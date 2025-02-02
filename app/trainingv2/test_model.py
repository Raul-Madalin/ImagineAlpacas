import os
import numpy as np
import tensorflow as tf

# ✅ Print TensorFlow version to confirm compatibility
print(f"🔹 TensorFlow Version: {tf.__version__}")

# ✅ Set Path to the Saved Model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Adjust as needed
MODEL_PATH = os.path.join(BASE_DIR, "app/model/chess_phase_model.h5")  # Ensure this matches your save location

print(f"📂 Loading model from: {MODEL_PATH}")

try:
    # ✅ Load the trained model
    model = tf.keras.models.load_model(MODEL_PATH)
    print("✅ Model loaded successfully!")

    # ✅ Display the model architecture (optional)
    model.summary()

    # ✅ Create a dummy input to test prediction (128x128 RGB image)
    dummy_input = np.random.rand(1, 128, 128, 3).astype(np.float32)  # Random normalized image

    # ✅ Make a prediction
    predictions = model.predict(dummy_input)

    # ✅ Interpret the prediction
    phase_labels = {0: "Opening", 1: "Middlegame", 2: "Endgame"}
    predicted_index = np.argmax(predictions[0])
    predicted_phase = phase_labels[predicted_index]

    print(f"🔍 Dummy Prediction Result: {predicted_phase}")

except Exception as e:
    print(f"❌ Error loading or testing the model: {e}")
