import os
import cv2
import joblib
import numpy as np
import matplotlib.pyplot as plt

# === Paths ===
test_dir = 'dataset/test'
model_path = 'knn_model.pkl'

# === Feature Extraction Function ===
def extract_features(image_path):
    """Extract color histogram features from an image."""
    image = cv2.imread(image_path)
    image = cv2.resize(image, (128, 128))  # Resize for consistency
    hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()
    return hist

# === Load Trained Model ===
knn, train_image_paths = joblib.load(model_path)

# === Recommend and Visualize Function ===
def recommend_and_visualize(test_img_path):
    """Recommend a similar image and visualize both the test and recommended images."""
    # Extract features from test image
    test_features = extract_features(test_img_path).reshape(1, -1)
    
    # Find the most similar image using k-NN
    distance, index = knn.kneighbors(test_features)
    recommended_img_path = train_image_paths[index[0][0]]
    
    print(f"Test Image: {os.path.basename(test_img_path)} -> Recommended Similar Image: {os.path.basename(recommended_img_path)}")
    
    # Visualize both images
    show_images(test_img_path, recommended_img_path)

# === Visualization Function ===
def show_images(test_img_path, recommended_img_path):
    """Display test and recommended images side by side."""
    test_img = cv2.imread(test_img_path)
    recommended_img = cv2.imread(recommended_img_path)
    
    plt.figure(figsize=(8, 4))
    
    # Test Image
    plt.subplot(1, 2, 1)
    plt.title("Test Image")
    plt.imshow(cv2.cvtColor(test_img, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    # Recommended Image
    plt.subplot(1, 2, 2)
    plt.title("Recommended Image")
    plt.imshow(cv2.cvtColor(recommended_img, cv2.COLOR_BGR2RGB))
    plt.axis('off')
    
    plt.show()

# === Run Recommendation for All Test Images ===
for test_img_name in os.listdir(test_dir):
    test_img_path = os.path.join(test_dir, test_img_name)
    recommend_and_visualize(test_img_path)
