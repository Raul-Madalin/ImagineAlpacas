import numpy as np
import os
import matplotlib.pyplot as plt
import cv2

BASE_DIR = "E:/WADe/WADe_ImagineAlpacas/app/training"

# ✅ Load the first batch of images
X = np.load(os.path.join(BASE_DIR, "X_batch_0.npy"))
y_phase = np.load(os.path.join(BASE_DIR, "y_phase_batch_0.npy"))

# ✅ Load filenames for piece extraction
image_dir = "E:/WADe/WADe_ImagineAlpacas/dataset/train"
image_files = [f for f in sorted(os.listdir(image_dir)) if f.endswith((".jpeg", ".png"))]

# ✅ Print dataset shapes
print(f"🔹 X shape: {X.shape}")  # Expect (batch_size, 128, 128, 3)
print(f"🔹 y_phase shape: {y_phase.shape}")  # Expect (batch_size, 3)

def visualize_image(image):
    """
    Debugging function to visualize images.
    Ensures image is in correct format before processing.
    """
    print(f"🤮 Debug: Image type: {type(image)}, dtype: {image.dtype}, shape: {image.shape}, Contiguous: {image.flags['C_CONTIGUOUS']}")
    image = np.array(image, dtype=np.uint8)
    image = np.ascontiguousarray(image)

    if image is None or image.size == 0:
        print("❌ Error: Image is empty or corrupt!")
        return np.zeros((128, 128, 3), dtype=np.uint8)

    if np.isnan(image).any() or np.isinf(image).any():
        print("⚠️ Warning: Image contains NaN or Inf values! Fixing...")
        image = np.nan_to_num(image)

    print(f"✔️ Min: {image.min()}, Max: {image.max()}, Unique values: {np.unique(image)[:10]}")
    print(f"Sample pixel at (0,0): {image[0,0]}")

    if len(image.shape) != 3 or image.shape[-1] != 3:
        print("⚠️ Image does not have 3 channels! Converting to BGR...")
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    return image

def extract_piece_count(filename):
    """
    Extract the number of pieces from the filename in FEN format with dashes instead of slashes.
    """
    fen_part = filename.split('.')[0]  # Remove file extension
    fen_ranks = fen_part.split('-')[:8]  # Extract FEN ranks

    piece_count = 0
    for rank in fen_ranks:
        for char in rank:
            if char.isalpha():  # Each letter represents a piece
                piece_count += 1
    return piece_count

# ✅ Show a sample image
sample_index = 7
debug_image = visualize_image(X[sample_index].astype("uint8"))
filename = image_files[sample_index]  # Get corresponding filename
num_pieces = extract_piece_count(filename)

plt.imshow(debug_image)
plt.title(f"Phase: {np.argmax(y_phase[sample_index])}, Pieces from filename: {num_pieces}")
plt.axis("off")
plt.show()

# ✅ Print first 10 samples for verification
for i in range(10):
    filename = image_files[i]
    num_pieces = extract_piece_count(filename)
    print(f"Sample {i}: Phase={np.argmax(y_phase[i])}, Pieces from filename={num_pieces}")
