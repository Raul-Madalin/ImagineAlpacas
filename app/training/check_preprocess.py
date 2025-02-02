import numpy as np
import os
import matplotlib.pyplot as plt
import cv2

BASE_DIR = "E:/WADe/WADe_ImagineAlpacas/app/training"

# ✅ Load the first batch of images
X = np.load(os.path.join(BASE_DIR, "X_batch_0.npy"))
y_phase = np.load(os.path.join(BASE_DIR, "y_phase_batch_0.npy"))
y_castling = np.load(os.path.join(BASE_DIR, "y_castling_batch_0.npy"))
y_en_passant = np.load(os.path.join(BASE_DIR, "y_en_passant_batch_0.npy"))

# ✅ Print dataset shapes
print(f"🔹 X shape: {X.shape}")  # Expect (batch_size, 128, 128, 3)
print(f"🔹 y_phase shape: {y_phase.shape}")  # Expect (batch_size, 3)
print(f"🔹 y_castling shape: {y_castling.shape}")  # Expect (batch_size, 1)
print(f"🔹 y_en_passant shape: {y_en_passant.shape}")  # Expect (batch_size, 1)

def visualize_contours(image):
    """
    Debugging function to visualize detected contours.
    Ensures image is in correct format before processing.
    """

    # Debugging: Print image properties
    print(f"🧐 Debug: Image type: {type(image)}, dtype: {image.dtype}, shape: {image.shape}, Contiguous: {image.flags['C_CONTIGUOUS']}")

    # Ensure image is a valid numpy array
    image = np.array(image, dtype=np.uint8)
    image = np.ascontiguousarray(image)  # Ensure contiguous memory

    # Ensure image is not empty
    if image is None or image.size == 0:
        print("❌ Error: Image is empty or corrupt!")
        return np.zeros((128, 128, 3), dtype=np.uint8)

    # Debugging: Check for NaN or Inf values
    if np.isnan(image).any() or np.isinf(image).any():
        print("⚠️ Warning: Image contains NaN or Inf values! Fixing...")
        image = np.nan_to_num(image)

    # Debugging: Check if values are in range
    print(f"✔️ Min: {image.min()}, Max: {image.max()}, Unique values: {np.unique(image)[:10]}")
    print(f"Sample pixel at (0,0): {image[0,0]}")

    # Ensure image has 3 channels
    if len(image.shape) != 3 or image.shape[-1] != 3:
        print("⚠️ Image does not have 3 channels! Converting to BGR...")
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Test with a dummy image before converting
    dummy_image = np.zeros((128, 128, 3), dtype=np.uint8)
    try:
        dummy_converted = cv2.cvtColor(dummy_image, cv2.COLOR_RGB2BGR)
        print("✔️ OpenCV successfully converted the dummy image.")
    except Exception as e:
        print(f"❌ OpenCV error with dummy image: {str(e)}")

    # Convert to BGR for OpenCV compatibility
    try:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        print("✔️ OpenCV successfully converted the image.")
    except Exception as e:
        print(f"❌ OpenCV error: {str(e)}")
        return np.zeros((128, 128, 3), dtype=np.uint8)

    # Debugging: Display image in OpenCV
    try:
        cv2.imshow("Debug Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"❌ OpenCV imshow error: {str(e)}")

    # Debugging: Save with Matplotlib and reload in OpenCV
    plt.imsave("debug_matplotlib.jpg", image)
    reloaded_matplotlib = cv2.imread("debug_matplotlib.jpg")

    if reloaded_matplotlib is None:
        print("❌ OpenCV cannot load the Matplotlib-saved image!")
        return np.zeros((128, 128, 3), dtype=np.uint8)
    else:
        print("✔️ OpenCV successfully loaded the Matplotlib-saved image.")

    return image


# ✅ Show a sample image with contour visualization
sample_index = 7
debug_image = visualize_contours(X[sample_index].astype("uint8"))
plt.imshow(debug_image)
plt.title(f"Phase: {np.argmax(y_phase[sample_index])}, Castling: {y_castling[sample_index]}, En Passant: {y_en_passant[sample_index]}")
plt.axis("off")
plt.show()

# ✅ Print first 40 samples for verification
for i in range(10):  # Check first 40 samples
    print(f"Sample {i}: Phase={np.argmax(y_phase[i])}, Castling={y_castling[i]}, En Passant={y_en_passant[i]}")
