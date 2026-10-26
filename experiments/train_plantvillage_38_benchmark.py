"""
PlantScanAI - PlantVillage Benchmark MobileNetV2 Training Pipeline
Trains and evaluates MobileNetV2 on the authoritative PlantVillage benchmark split
with field augmentations (rotation, zoom, flip, brightness, contrast, Gaussian noise).

Outputs:
- ml/weights/plantvillage_38/plantvillage_benchmark.keras
- ml/weights/plantvillage_38/plantvillage_benchmark.tflite
- ml/weights/plantvillage_38/classes.json
- datasets/reports/model/plantvillage_38_evaluation_report.json
"""

import argparse
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "datasets" / "plantvillage_38"
WEIGHTS_DIR = PROJECT_ROOT / "ml" / "weights" / "plantvillage_38"
REPORT_PATH = PROJECT_ROOT / "datasets" / "reports" / "model" / "plantvillage_38_evaluation_report.json"

IMG_SIZE = (224, 224)
BATCH_SIZE = 16


def set_seed(seed: int = SEED):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def get_classes() -> List[str]:
    train_dir = DATASET_ROOT / "train"
    if not train_dir.exists():
        raise FileNotFoundError(f"Training directory not found at {train_dir}")
    classes = sorted([d.name for d in train_dir.iterdir() if d.is_dir()])
    if not classes:
        raise ValueError(f"No class subdirectories found in {train_dir}")
    return classes


def load_split(split_name: str, classes: List[str]) -> tf.data.Dataset:
    directory = DATASET_ROOT / split_name
    return tf.keras.utils.image_dataset_from_directory(
        directory,
        labels="inferred",
        label_mode="int",
        class_names=classes,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=(split_name == "train"),
        seed=SEED if split_name == "train" else None,
    )


def build_model(num_classes: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3), name="image")

    # Phase 3 Required Field Augmentation Pipeline
    augmented = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.15),
            tf.keras.layers.RandomZoom(height_factor=0.1, width_factor=0.1),
            tf.keras.layers.RandomBrightness(0.15, value_range=(0, 255)),
            tf.keras.layers.RandomContrast(0.15),
            tf.keras.layers.GaussianNoise(0.03),
        ],
        name="field_augmentations",
    )(inputs)

    preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(augmented)

    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    x = base_model(preprocessed, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="PlantVillage_MobileNetV2_Benchmark")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train_and_evaluate(epochs: int = 5):
    set_seed()
    classes = get_classes()
    num_classes = len(classes)
    print(f"Loaded {num_classes} benchmark classes: {classes}")

    train_ds = load_split("train", classes)
    val_ds = load_split("validation", classes)
    test_ds = load_split("test", classes)

    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(WEIGHTS_DIR / "classes.json", "w", encoding="utf-8") as f:
        json.dump(classes, f, indent=2)

    model = build_model(num_classes)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=3,
            restore_best_weights=True,
            mode="max",
        ),
    ]

    print("\nStarting MobileNetV2 Transfer Learning...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluate on held-out test split
    print("\nEvaluating on held-out test partition...")
    y_true = []
    y_pred = []

    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy().tolist())
        y_pred.extend(np.argmax(preds, axis=1).tolist())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    test_acc = float(np.mean(y_true == y_pred))
    p_micro, r_micro, f1_micro, _ = precision_recall_fscore_support(y_true, y_pred, average="micro", zero_division=0)
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)

    report_dict = classification_report(y_true, y_pred, target_names=classes, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred).tolist()

    print(f"\n==================================================")
    print(f"PlantVillage Benchmark Test Accuracy: {test_acc * 100:.2f}%")
    print(f"Weighted F1: {f1_weighted:.4f} | Macro F1: {f1_macro:.4f}")
    print(f"==================================================")

    # Save Keras Model
    keras_path = WEIGHTS_DIR / "plantvillage_benchmark.keras"
    model.save(keras_path)
    print(f"Saved Keras model to {keras_path}")

    # Export TFLite Model
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        tflite_path = WEIGHTS_DIR / "plantvillage_benchmark.tflite"
        with open(tflite_path, "wb") as f:
            f.write(tflite_model)
        print(f"Exported TFLite model to {tflite_path} ({len(tflite_model)/1024/1024:.2f} MB)")
    except Exception as e:
        print(f"Warning: TFLite conversion error: {e}")

    # Save Evaluation Report
    eval_report = {
        "model_architecture": "MobileNetV2 (ImageNet Transfer Learning)",
        "benchmark_name": "PlantVillage Benchmark Evaluation",
        "reference_standard": "Phase 1 Project Report (Mohanty et al., 2016)",
        "num_classes_evaluated": num_classes,
        "classes": classes,
        "metrics": {
            "test_accuracy": round(test_acc, 4),
            "micro_f1": round(float(f1_micro), 4),
            "macro_f1": round(float(f1_macro), 4),
            "weighted_f1": round(float(f1_weighted), 4),
            "weighted_precision": round(float(p_weighted), 4),
            "weighted_recall": round(float(r_weighted), 4),
        },
        "target_accuracy": 0.85,
        "meets_85_pct_target": bool(test_acc >= 0.85),
        "per_class_metrics": {k: v for k, v in report_dict.items() if k in classes},
        "confusion_matrix": cm,
        "epochs_trained": len(history.history["loss"]),
        "field_augmentations_applied": [
            "RandomFlip(horizontal)",
            "RandomRotation(0.15)",
            "RandomZoom(0.1)",
            "RandomBrightness(0.15)",
            "RandomContrast(0.15)",
            "GaussianNoise(0.03)",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    print(f"Saved evaluation report to {REPORT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=4, help="Number of epochs to train")
    args = parser.parse_args()
    train_and_evaluate(epochs=args.epochs)
