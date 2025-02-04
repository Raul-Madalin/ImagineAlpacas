import os
import cv2
import numpy as np
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt

# Update dataset path to point to the dataset folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Get root directory
DATASET_PATH = os.path.join(BASE_DIR, "dataset/train")  # Adjust if needed
DEBUG_DIR = os.path.join(BASE_DIR, "app/debug")  # Directory to save debug images

# Image processing parameters
IMG_SIZE = 128  # Consider using a larger size (e.g., 256) if detail is lost

# Labels for game phases
phase_labels = {"Opening": 0, "Middlegame": 1, "Endgame": 2}

# Set this variable to 'yes' or 'no' to control debug image saving
save_debug_images = 'no'  # Change to 'no' to disable saving debug images

if save_debug_images == 'yes':
    os.makedirs(DEBUG_DIR, exist_ok=True)  # Create debug directory if it doesn't exist

def extract_piece_count(filename):
    """
    Extract the number of pieces from the filename in FEN format with dashes instead of slashes.
    """
    fen_part = filename.split('.')[0]  # Remove file extension
    fen_ranks = fen_part.split('-')[:8]  # FEN ranks are the first 8 parts

    piece_count = 0
    for rank in fen_ranks:
        for char in rank:
            if char.isalpha():  # Each letter represents a piece
                piece_count += 1

    return piece_count

def detect_game_phase(piece_count):
    """
    Determines whether the game is in the Opening, Middlegame, or Endgame
    based on the number of pieces detected on the board.
    """
    if piece_count >= 24:
        return phase_labels["Opening"]
    elif 14 <= piece_count <= 23:
        return phase_labels["Middlegame"]
    else:
        return phase_labels["Endgame"]

def save_debug_image(image, filename, piece_count, phase_label, batch_number, idx):
    """
    Save the debug image with the detected information overlay.
    """
    plt.figure(figsize=(2, 2))
    plt.imshow(image)
    plt.title(f"Phase: {phase_label}, Pieces: {piece_count}")
    plt.axis('off')
    debug_image_path = os.path.join(DEBUG_DIR, f"batch_{batch_number}_img_{idx}.png")
    plt.savefig(debug_image_path, bbox_inches='tight', pad_inches=0.1)
    plt.close()

# Process images in BATCHES (to avoid RAM overload)
X, y_phase = [], []
batch_size = 1000  # Adjust based on your memory capacity

print(f"📂 Scanning dataset folder: {DATASET_PATH}")

image_files = [f for f in os.listdir(DATASET_PATH) if f.endswith((".jpeg", ".png"))]

for idx, filename in enumerate(image_files):
    img_path = os.path.join(DATASET_PATH, filename)

    try:
        print(f"🔼️ Processing image {idx + 1}/{len(image_files)}: {filename}")

        # Load image and ensure it's not None.
        image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if image is None:
            print(f"⚠️ Skipping {filename}: Unable to load image!")
            continue

        # Resize and convert image format.
        image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Extract piece count from filename
        piece_count = extract_piece_count(filename)
        print(f"🔍 {filename}: Detected Pieces from filename: {piece_count}")

        # Detect game phase.
        phase_label = detect_game_phase(piece_count)

        # Store results.
        X.append(image)
        y_phase.append(phase_label)

        # Save debug image if option is enabled
        batch_number = idx // batch_size
        if save_debug_images == 'yes':
            save_debug_image(image, filename, piece_count, phase_label, batch_number, idx)

        # Save in batches to avoid RAM issues.
        if len(X) >= batch_size or (idx == len(image_files) - 1):
            np.save(os.path.join(BASE_DIR, f"app/preprocesed_dataset/training/X_batch_{batch_number}.npy"), np.array(X, dtype=np.float32))
            np.save(os.path.join(BASE_DIR, f"app/preprocesed_dataset/training/y_phase_batch_{batch_number}.npy"), to_categorical(y_phase, num_classes=3))

            print(f"✅ Batch {batch_number} saved. Cleared memory!")
            # Clear lists to free up memory.
            X, y_phase = [], []

    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
