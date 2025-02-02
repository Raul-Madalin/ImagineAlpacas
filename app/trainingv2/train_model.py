import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint

# ✅ Print TensorFlow version
print(f"🔹 TensorFlow Version: {tf.__version__}")

# ✅ Set Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Root directory
TRAIN_PATH = os.path.join(BASE_DIR, "app/preprocesed_dataset/training")  # Training data path
VALIDATION_PATH = os.path.join(BASE_DIR, "app/preprocesed_dataset/test")  # Validation data path
MODEL_PATH = os.path.join(BASE_DIR, "app/model/chess_phase_model.h5")  # Save trained model

print(f"📂 Training Dataset Path: {TRAIN_PATH}")
print(f"📂 Validation Dataset Path: {VALIDATION_PATH}")

# ✅ Load training and validation dataset filenames
train_files = os.listdir(TRAIN_PATH)
X_train_batches = sorted([f for f in train_files if f.startswith("X_batch_") and f.endswith(".npy")])
y_train_batches = sorted([f for f in train_files if f.startswith("y_phase_batch_") and f.endswith(".npy")])

validation_files = os.listdir(VALIDATION_PATH)
X_val_batches = sorted([f for f in validation_files if f.startswith("X_batch_") and f.endswith(".npy")])
y_val_batches = sorted([f for f in validation_files if f.startswith("y_phase_batch_") and f.endswith(".npy")])

# ✅ Ensure batch count consistency
assert len(X_train_batches) == len(y_train_batches), "❌ Mismatch in training batch file counts!"
assert len(X_val_batches) == len(y_val_batches), "❌ Mismatch in validation batch file counts!"

print(f"📦 Found {len(X_train_batches)} training batches.")
print(f"📦 Found {len(X_val_batches)} validation batches.")

# ✅ Data Generator Function (Avoids Memory Overload)
def data_generator(batch_files, label_files, dataset_path, batch_size=32):
    for i, (X_batch, y_batch) in enumerate(zip(batch_files, label_files)):
        print(f"🔹 Loading batch {i+1}/{len(batch_files)}: {X_batch}")
        X = np.load(os.path.join(dataset_path, X_batch)).astype(np.float32) / 255.0  # Normalize images
        y_phase = np.load(os.path.join(dataset_path, y_batch))  # Load labels

        # Ensure labels are one-hot encoded
        if len(y_phase.shape) == 1 or y_phase.shape[-1] != 3:
            y_phase = tf.keras.utils.to_categorical(y_phase, num_classes=3)

        yield X, y_phase

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

# ✅ Output Layer for Phase Classification
phase_output = Dense(3, activation='softmax', name="phase_output")(x)

# ✅ Create the Model
model = Model(inputs=input_layer, outputs=phase_output)

# ✅ Compile Model
model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss="categorical_crossentropy",
    metrics=["accuracy"]  # Accuracy for phase classification
)

# ✅ Save Best Model Checkpoint
checkpoint = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor="val_loss", mode="min", verbose=1)

# ✅ Define batch size
batch_size = 32  # Adjust based on memory availability

# ✅ Create datasets for training and validation
train_dataset = tf.data.Dataset.from_generator(
    lambda: data_generator(X_train_batches, y_train_batches, TRAIN_PATH),
    output_signature=(
        tf.TensorSpec(shape=(None, 128, 128, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, 3), dtype=tf.float32)
    )
).repeat()

validation_dataset = tf.data.Dataset.from_generator(
    lambda: data_generator(X_val_batches, y_val_batches, VALIDATION_PATH),
    output_signature=(
        tf.TensorSpec(shape=(None, 128, 128, 3), dtype=tf.float32),
        tf.TensorSpec(shape=(None, 3), dtype=tf.float32)
    )
).repeat()

# ✅ Dynamically determine steps_per_epoch and validation_steps
steps_per_epoch = len(X_train_batches)
validation_steps = len(X_val_batches)

# ✅ Start Training
print("🚀 Training CNN Model...")
history = model.fit(
    train_dataset,
    epochs=10,
    steps_per_epoch=steps_per_epoch,
    validation_data=validation_dataset,
    validation_steps=validation_steps,
    callbacks=[checkpoint]
)

# ✅ Save Final Model
model.save(MODEL_PATH)
print(f"🎉 Model training complete! Saved as: {MODEL_PATH}")
