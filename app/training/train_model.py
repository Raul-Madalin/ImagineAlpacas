import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.utils import to_categorical

# ✅ Print TensorFlow version
print(f"🔹 TensorFlow Version: {tf.__version__}")

# ✅ Set Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Root directory
DATASET_PATH = os.path.join(BASE_DIR, "app/training")  # Dataset path
MODEL_PATH = os.path.join(BASE_DIR, "app/model/chess_analysis_model.h5")  # Save trained model

print(f"📂 Dataset Path: {DATASET_PATH}")

# ✅ Load dataset filenames
all_files = os.listdir(DATASET_PATH)
X_batches = sorted([f for f in all_files if f.startswith("X_batch_") and f.endswith(".npy")])
y_phase_batches = sorted([f for f in all_files if f.startswith("y_phase_batch_") and f.endswith(".npy")])
y_castling_batches = sorted([f for f in all_files if f.startswith("y_castling_batch_") and f.endswith(".npy")])
y_en_passant_batches = sorted([f for f in all_files if f.startswith("y_en_passant_batch_") and f.endswith(".npy")])

# ✅ Ensure batch count consistency
assert len(X_batches) == len(y_phase_batches) == len(y_castling_batches) == len(y_en_passant_batches), \
    "❌ Mismatch in batch file counts!"

print(f"📦 Found {len(X_batches)} batches.")

# ✅ Batch Generator Function (Avoids Memory Overload)
def data_generator(batch_size=32):
    for i, (X_batch, y_p, y_c, y_e) in enumerate(zip(X_batches, y_phase_batches, y_castling_batches, y_en_passant_batches)):
        print(f"🔹 Loading batch {i+1}/{len(X_batches)}: {X_batch}")

        X = np.load(os.path.join(DATASET_PATH, X_batch)).astype(np.float32) / 255.0  # Normalize
        y_phase = np.load(os.path.join(DATASET_PATH, y_p))
        y_castling = np.load(os.path.join(DATASET_PATH, y_c))
        y_en_passant = np.load(os.path.join(DATASET_PATH, y_e))

        # One-hot encode `y_phase` if necessary
        if len(y_phase.shape) == 1:
            y_phase = to_categorical(y_phase, num_classes=3)

        # Expand dims for binary outputs
        y_castling = np.expand_dims(y_castling, axis=-1)
        y_en_passant = np.expand_dims(y_en_passant, axis=-1)

        print(f"   ✅ Shapes - X: {X.shape}, y_phase: {y_phase.shape}, y_castling: {y_castling.shape}, y_en_passant: {y_en_passant.shape}")

        yield X, {"phase_output": y_phase, "castling_output": y_castling, "en_passant_output": y_en_passant}

# ✅ Define CNN Model (Functional API)
input_layer = Input(shape=(128, 128, 3))

# ✅ Convolutional Layers
x = Conv2D(32, (3, 3), activation='relu')(input_layer)
x = MaxPooling2D((2, 2))(x)

x = Conv2D(64, (3, 3), activation='relu')(x)
x = MaxPooling2D((2, 2))(x)

x = Conv2D(128, (3, 3), activation='relu')(x)
x = MaxPooling2D((2, 2))(x)

# ✅ Flatten and Fully Connected Layers
x = Flatten()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)

# ✅ Multiple Output Layers
phase_output = Dense(3, activation='softmax', name="phase_output")(x)  # Categorical classification
castling_output = Dense(1, activation='sigmoid', name="castling_output")(x)  # Binary classification
en_passant_output = Dense(1, activation='sigmoid', name="en_passant_output")(x)  # Binary classification

# ✅ Create the Model (Functional API)
model = Model(inputs=input_layer, outputs=[phase_output, castling_output, en_passant_output])

# ✅ Run Forward Pass (To Initialize Model)
dummy_input = tf.random.normal((1, 128, 128, 3))
_ = model(dummy_input)  # First pass initializes model layers

# ✅ Now we can safely access model.output
print(f"🔹 Model output names: {[output.name for output in model.outputs]}")

# ✅ Compile Model
# ✅ Define separate metrics for each output
model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss={
        "phase_output": "categorical_crossentropy",
        "castling_output": "binary_crossentropy",
        "en_passant_output": "binary_crossentropy"
    },
    metrics={
        "phase_output": ["accuracy"],       # ✅ Accuracy for phase classification
        "castling_output": ["accuracy"],    # ✅ Accuracy for castling rights
        "en_passant_output": ["accuracy"]   # ✅ Accuracy for en passant
    }
)


# ✅ Save Best Model Checkpoint
checkpoint = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor="val_loss", mode="min", verbose=1)

# ✅ Define batch size before using it
batch_size = 32  # You can adjust this based on memory availability

# ✅ Create dataset with correct shapes (no extra batch dimension)
dataset = tf.data.Dataset.from_generator(
    lambda: data_generator(batch_size),
    output_signature=(
        tf.TensorSpec(shape=(None, 128, 128, 3), dtype=tf.float32),  # ✅ Expect batches, not single samples
        {
            "phase_output": tf.TensorSpec(shape=(None, 3), dtype=tf.float32),  # ✅ Expect batch dimension
            "castling_output": tf.TensorSpec(shape=(None, 1), dtype=tf.float32),
            "en_passant_output": tf.TensorSpec(shape=(None, 1), dtype=tf.float32),
        }
    )
).repeat()




# ✅ Dynamically determine steps_per_epoch
steps_per_epoch = len(X_batches) if len(X_batches) > 0 else None
print("🚀 Training CNN Model...")
history = model.fit(
    dataset,
    epochs=10,
    steps_per_epoch=steps_per_epoch,  # ✅ Uses only available data
    validation_data=None,
    callbacks=[checkpoint]
)


# ✅ Save Final Model
model.save(MODEL_PATH)
print(f"🎉 Model training complete! Saved as: {MODEL_PATH}")
