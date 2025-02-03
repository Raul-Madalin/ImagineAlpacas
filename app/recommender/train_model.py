import os
import cv2
import numpy as np
from sklearn.neighbors import NearestNeighbors
import joblib

# === Paths ===
train_dir = 'dataset/train'
model_save_path = 'knn_model.pkl'

# === Configuration ===
BATCH_SIZE = 1000  # You can adjust this based on your system's memory

# === Feature Extraction Function ===
def extract_features(image_path):
    """Extract color histogram features from an image."""
    image = cv2.imread(image_path)
    image = cv2.resize(image, (128, 128))  # Resize for consistency
    hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

# === Batch Processing for Feature Extraction ===
def process_in_batches(image_list, batch_size):
    """Process images in batches to optimize memory and speed."""
    total_images = len(image_list)
    features = []
    paths = []
    
    for start_idx in range(0, total_images, batch_size):
        end_idx = min(start_idx + batch_size, total_images)
        batch = image_list[start_idx:end_idx]
        
        print(f"Processing batch {start_idx // batch_size + 1}: Images {start_idx + 1} to {end_idx}")
        
        for img_name in batch:
            img_path = os.path.join(train_dir, img_name)
            feature = extract_features(img_path)
            features.append(feature)
            paths.append(img_path)
        
        print(f"Batch {start_idx // batch_size + 1} completed.")
    
    return features, paths

# === Main Workflow ===
print("Starting feature extraction from training images...")

# List all images in the training directory
image_files = os.listdir(train_dir)

# Process images in batches
train_features, train_image_paths = process_in_batches(image_files, BATCH_SIZE)

print("Feature extraction completed. Total images processed:", len(train_image_paths))

# === Model Training ===
print("Starting k-NN model training...")
knn = NearestNeighbors(n_neighbors=1, metric='euclidean')
knn.fit(train_features)
print("Model training completed.")

# === Save Model ===
print(f"Saving the model to {model_save_path}...")
joblib.dump((knn, train_image_paths), model_save_path)
print(f"Model trained and saved successfully at {model_save_path}")
