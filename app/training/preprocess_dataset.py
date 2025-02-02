import os
import cv2
import numpy as np
import pandas as pd
from tensorflow.keras.utils import to_categorical
import matplotlib.pyplot as plt

# ✅ Update dataset path to point to the dataset folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Get root directory
DATASET_PATH = os.path.join(BASE_DIR, "dataset/train")  # Adjust if needed

# Image processing parameters
IMG_SIZE = 128  # You might consider using a larger size (e.g., 256) if detail is lost

# Labels for game phases
phase_labels = {"Opening": 0, "Middlegame": 1, "Endgame": 2}


def count_pieces(image):
    """
    Counts the number of chess pieces on the board using a robust pre-processing
    approach designed to work on the diverse images from the Chess Positions dataset.
    It combines contrast enhancement (CLAHE) with thresholding based on both the
    enhanced grayscale image and the HSV value channel.
    """
    # Assume the image is in RGB format.
    # Convert to grayscale.
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Enhance contrast using CLAHE.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Convert to HSV and extract the value channel.
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    value_channel = hsv[:, :, 2]

    # Blur both images to reduce noise.
    blurred_enhanced = cv2.GaussianBlur(enhanced, (5, 5), 0)
    blurred_value = cv2.GaussianBlur(value_channel, (5, 5), 0)

    # Apply Otsu thresholding to both blurred images.
    _, thresh1 = cv2.threshold(blurred_enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, thresh2 = cv2.threshold(blurred_value, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Combine the threshold images to capture as many piece features as possible.
    combined_thresh = cv2.bitwise_or(thresh1, thresh2)

    # Apply morphological operations to reduce noise.
    kernel = np.ones((3, 3), np.uint8)
    morph = cv2.morphologyEx(combined_thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    morph = cv2.morphologyEx(morph, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Find contours that may correspond to chess pieces.
    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by area (adjust min_area as needed).
    min_area = 20
    piece_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

    # Return the number of detected piece contours.
    return len(piece_contours)


def detect_game_phase(image):
    """
    Determines whether the game is in the Opening, Middlegame, or Endgame
    based on the number of pieces detected on the board.
    """
    num_pieces = count_pieces(image)
    if num_pieces >= 24:
        return phase_labels["Opening"]
    elif 14 <= num_pieces < 24:
        return phase_labels["Middlegame"]
    else:
        return phase_labels["Endgame"]


def detect_castling_rights(image):
    """
    Determines if castling rights are available by ensuring:
      1. The king and rooks are in their starting positions.
      2. The path between them is clear.
      3. The king has not moved.
      
    Uses adaptive thresholding on the grayscale (converted from RGB) image.
    """
    # Convert from RGB to grayscale.
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Adaptive thresholding.
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Morphological operations to reduce noise.
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Find contours.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_pieces = set()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        grid_x = x // (image.shape[1] // 8)
        grid_y = y // (image.shape[0] // 8)
        detected_pieces.add((grid_y, grid_x))
    
    # Check for white castling positions.
    white_king_start = (7, 4)
    white_rook_queenside_start = (7, 0)
    white_rook_kingside_start = (7, 7)
    white_clear_queenside = {(7, 1), (7, 2), (7, 3)}
    white_clear_kingside = {(7, 5), (7, 6)}
    
    white_castling = False
    if white_king_start in detected_pieces:
        if white_rook_queenside_start in detected_pieces and white_clear_queenside.isdisjoint(detected_pieces):
            white_castling = True
        if white_rook_kingside_start in detected_pieces and white_clear_kingside.isdisjoint(detected_pieces):
            white_castling = True
    
    # Check for black castling positions.
    black_king_start = (0, 4)
    black_rook_queenside_start = (0, 0)
    black_rook_kingside_start = (0, 7)
    black_clear_queenside = {(0, 1), (0, 2), (0, 3)}
    black_clear_kingside = {(0, 5), (0, 6)}
    
    black_castling = False
    if black_king_start in detected_pieces:
        if black_rook_queenside_start in detected_pieces and black_clear_queenside.isdisjoint(detected_pieces):
            black_castling = True
        if black_rook_kingside_start in detected_pieces and black_clear_kingside.isdisjoint(detected_pieces):
            black_castling = True
    
    return white_castling or black_castling


def detect_en_passant(image):
    """
    Determines if en passant is possible by:
      1. Identifying pawns in the correct rank.
      2. Ensuring they are adjacent.
      3. Checking if a pawn has moved two squares.
      
    The grayscale conversion is applied on the RGB image.
    """
    # Convert from RGB to grayscale.
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Adaptive thresholding.
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    # Morphological operations.
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    
    # Find contours.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_pieces = set()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        grid_x = x // (image.shape[1] // 8)
        grid_y = y // (image.shape[0] // 8)
        detected_pieces.add((grid_y, grid_x))
    
    # Check en passant conditions.
    for y, x in detected_pieces:
        if y == 3:  # White en passant capture rank.
            if (y, x - 1) in detected_pieces or (y, x + 1) in detected_pieces:
                return True
        if y == 4:  # Black en passant capture rank.
            if (y, x - 1) in detected_pieces or (y, x + 1) in detected_pieces:
                return True
    return False


# ✅ Process images in BATCHES (to avoid RAM overload)
X, y_phase, y_castling, y_en_passant = [], [], [], []
batch_size = 1000  # Adjust based on your memory capacity

print(f"📂 Scanning dataset folder: {DATASET_PATH}")

image_files = [f for f in os.listdir(DATASET_PATH) if f.endswith((".jpeg", ".png"))]

for idx, filename in enumerate(image_files):
    img_path = os.path.join(DATASET_PATH, filename)

    try:
        print(f"🖼️ Processing image {idx + 1}/{len(image_files)}: {filename}")

        # ✅ Load image and ensure it's not None.
        image = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if image is None:
            print(f"⚠️ Skipping {filename}: Unable to load image!")
            continue

        # ✅ Resize and convert image format.
        image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # ✅ Count pieces and log the result.
        num_pieces = count_pieces(image)
        print(f"🔍 {filename}: Detected Pieces: {num_pieces}")

        # ✅ Detect game phase.
        phase_label = detect_game_phase(image)

        # ✅ Detect castling rights.
        castling_label = detect_castling_rights(image)

        # ✅ Detect en passant possibility.
        en_passant_label = detect_en_passant(image)

        # Store results.
        X.append(image)
        y_phase.append(phase_label)
        y_castling.append(int(castling_label))
        y_en_passant.append(int(en_passant_label))

        # Save in batches to avoid RAM issues.
        if len(X) >= batch_size or (idx == len(image_files) - 1):
            batch_number = idx // batch_size
            np.save(os.path.join(BASE_DIR, f"app/training/X_batch_{batch_number}.npy"), np.array(X, dtype=np.float32))
            np.save(os.path.join(BASE_DIR, f"app/training/y_phase_batch_{batch_number}.npy"),
                    to_categorical(y_phase, num_classes=3))
            np.save(os.path.join(BASE_DIR, f"app/training/y_castling_batch_{batch_number}.npy"), np.array(y_castling, dtype=np.uint8))
            np.save(os.path.join(BASE_DIR, f"app/training/y_en_passant_batch_{batch_number}.npy"),
                    np.array(y_en_passant, dtype=np.uint8))

            print(f"✅ Batch {batch_number} saved. Cleared memory!")
            # Clear lists to free up memory.
            X, y_phase, y_castling, y_en_passant = [], [], [], []

    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
