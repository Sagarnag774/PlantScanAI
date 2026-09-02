from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight


SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DATASET_ROOT = PROJECT_ROOT / "datasets" / "model"
WEIGHTS_DIR = PROJECT_ROOT / "ml" / "weights"
REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports" / "model"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
DEFAULT_EPOCHS = 10
LEARNING_RATE = 1e-3

SUPPORTED_CROPS = [
    "apple",
    "banana",
    "bell_pepper",
    "cotton",
    "grape",
    "maize",
    "mango",
    "potato",
    "rice",
    "tomato",
]


def set_reproducibility(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass


def get_crop_classes(crop: str) -> List[str]:
    train_dir = MODEL_DATASET_ROOT / crop / "train"
    if not train_dir.exists():
        raise FileNotFoundError(f"Train directory not found for crop '{crop}': {train_dir}")
    classes = sorted([d.name for d in train_dir.iterdir() if d.is_dir()])
    if not classes:
        raise ValueError(f"No class subdirectories found in {train_dir}")
    return classes


def load_dataset(crop: str, split: str, class_names: List[str]) -> tf.data.Dataset:
    directory = MODEL_DATASET_ROOT / crop / split
    if not directory.exists():
        raise FileNotFoundError(f"Dataset split directory not found: {directory}")

    ds = tf.keras.utils.image_dataset_from_directory(
        directory,
        labels="inferred",
        label_mode="int",
        class_names=class_names,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=(split == "train"),
        seed=SEED if split == "train" else None,
    )
    return ds


def build_mobilenetv2_model(num_classes: int) -> tf.keras.Model:
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    data_augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.15),
        tf.keras.layers.RandomZoom(0.1),
    ], name="data_augmentation")

    inputs = tf.keras.Input(shape=(*IMG_SIZE, 3))
    x = data_augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)

    if num_classes == 2:
        outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="predictions")(x)
        loss = "binary_crossentropy"
    else:
        outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="predictions")(x)
        loss = "sparse_categorical_crossentropy"

    model = tf.keras.Model(inputs, outputs, name="mobilenetv2_classifier")
    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    model.compile(optimizer=optimizer, loss=loss, metrics=["accuracy"])
    return model


def train_and_evaluate_crop(crop: str, epochs: int = DEFAULT_EPOCHS) -> Dict[str, any]:
    print("=" * 80)
    print(f"PlantScan AI — Training MobileNetV2 for Crop: {crop.upper()}")
    print("=" * 80)

    set_reproducibility()
    class_names = get_crop_classes(crop)
    num_classes = len(class_names)
    print(f"Discovered {num_classes} canonical classes for '{crop}': {class_names}")

    train_ds = load_dataset(crop, "train", class_names)
    val_ds = load_dataset(crop, "validation", class_names)
    test_ds = load_dataset(crop, "test", class_names)

    # Compute class weights
    y_train = []
    for _, labels in train_ds.unbatch():
        y_train.append(labels.numpy())
    y_train = np.array(y_train)

    unique_classes = np.unique(y_train)
    weights = compute_class_weight(class_weight="balanced", classes=unique_classes, y=y_train)
    class_weight_dict = {cls_idx: float(w) for cls_idx, w in zip(unique_classes, weights)}
    print(f"Computed Class Weights: {class_weight_dict}")

    # Build & compile model
    model = build_mobilenetv2_model(num_classes)

    # Prefetch
    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(buffer_size=autotune)
    val_ds = val_ds.prefetch(buffer_size=autotune)
    test_ds = test_ds.prefetch(buffer_size=autotune)

    # Callbacks
    crop_weights_dir = WEIGHTS_DIR / crop
    crop_weights_dir.mkdir(parents=True, exist_ok=True)
    model_checkpoint_path = crop_weights_dir / f"{crop}_mobilenetv2.keras"

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, verbose=1),
        tf.keras.callbacks.ModelCheckpoint(filepath=str(model_checkpoint_path), monitor="val_accuracy", save_best_only=True, verbose=1),
    ]

    print(f"\nStarting training for {epochs} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        class_weight=class_weight_dict,
        callbacks=callbacks,
    )

    # Evaluate on Test Split
    print("\nEvaluating model on Test dataset split...")
    test_loss, test_acc = model.evaluate(test_ds)
    print(f"Test Loss: {test_loss:.4f} | Test Accuracy: {test_acc*100:.2f}%")

    # Predictions for metrics
    y_true = []
    y_pred = []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        if num_classes == 2:
            pred_classes = (preds.ravel() > 0.5).astype(int)
        else:
            pred_classes = np.argmax(preds, axis=1)
        y_true.extend(labels.numpy())
        y_pred.extend(pred_classes)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted")
    report_dict = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    conf_matrix = confusion_matrix(y_true, y_pred).tolist()

    # Convert to TFLite model
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = crop_weights_dir / f"{crop}_model.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Exported TFLite model: {tflite_path}")

    # Also save to main weights dir if tomato
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    if crop == "tomato":
        with open(WEIGHTS_DIR / "disease_classifier.tflite", "wb") as f:
            f.write(tflite_model)

    # Save Evaluation Report
    crop_report_dir = REPORTS_DIR / crop
    crop_report_dir.mkdir(parents=True, exist_ok=True)
    report_path = crop_report_dir / "evaluation_report.json"

    eval_results = {
        "crop": crop,
        "classes": class_names,
        "test_loss": float(test_loss),
        "test_accuracy": float(test_acc),
        "weighted_precision": float(precision),
        "weighted_recall": float(recall),
        "weighted_f1_score": float(f1),
        "confusion_matrix": conf_matrix,
        "classification_report": report_dict,
        "weights_path": str(model_checkpoint_path),
        "tflite_path": str(tflite_path),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)

    print(f"Saved evaluation report: {report_path}")
    print(f"STATUS: PASS for '{crop}'\n")
    return eval_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MobileNetV2 classifier for PlantScan AI crops.")
    parser.add_argument("--crop", required=True, choices=SUPPORTED_CROPS + ["all"], help="Target crop name.")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Number of training epochs.")

    args = parser.parse_args()

    if args.crop == "all":
        crops_to_train = SUPPORTED_CROPS
    else:
        crops_to_train = [args.crop]

    summary_results = {}
    for c in crops_to_train:
        res = train_and_evaluate_crop(c, epochs=args.epochs)
        summary_results[c] = res

    print("=" * 80)
    print("ALL CROP MODEL TRAINING & EVALUATION COMPLETED")
    print("=" * 80)
    for c, r in summary_results.items():
        print(f"• {c.upper():12}: Test Accuracy = {r['test_accuracy']*100:.2f}%, F1 = {r['weighted_f1_score']:.4f}")


if __name__ == "__main__":
    main()
