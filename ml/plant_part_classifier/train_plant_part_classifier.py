"""
PlantScan AI - Stage 1 MobileNetV2 Plant-Part Classifier Training Pipeline
Trains a lightweight transfer-learning MobileNetV2 model to classify plant images
into 4 anatomical parts: Leaf, Stem, Fruit, and Bark.
Supports training on verified cleaned datasets (e.g. datasets/plant_parts_cleaned)
with balanced class weighting, robust field augmentations, and held-out test evaluation.

Outputs:
    ml/weights/plant_part_classifier/plant_part_model.keras
    ml/weights/plant_part_classifier/plant_part_model.tflite
    ml/weights/plant_part_classifier/classes.json
    datasets/reports/model/plant_part_classifier/evaluation_report.json
    datasets/reports/model/plant_part_classifier/comparison_report.json
"""

import argparse
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.utils.class_weight import compute_class_weight

SEED = 42
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
DEFAULT_EPOCHS = 12

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET_DIR = PROJECT_ROOT / "datasets" / "plant_parts_cleaned"
WEIGHTS_DIR = PROJECT_ROOT / "ml" / "weights" / "plant_part_classifier"
REPORTS_DIR = PROJECT_ROOT / "datasets" / "reports" / "model" / "plant_part_classifier"

CLASSES = ["bark", "fruit", "leaf", "stem"]

# Baseline metrics from previously audited contaminated dataset (for honest comparison)
CONTAMINATED_BASELINE = {
    "dataset": "datasets/plant_parts (uncleaned)",
    "status": "AFFECTED_BY_DATASET_CONTAMINATION",
    "contamination_details": "Included 52 botanical illustrations/engravings, 7 patent text pages, 43 mislabeled organs (including 34 dead mango leaves as stems), 29 distant landscapes, and 11 non-plant objects (coins, food plates, machinery).",
    "test_accuracy": 0.8197,
    "macro_f1": 0.8171,
    "weighted_f1": 0.8155,
    "per_class_f1": {
        "bark": 0.8966,
        "fruit": 0.7273,
        "leaf": 0.9091,
        "stem": 0.7353,
    },
    "test_sample_count": 61,
}


def set_seed(seed: int = SEED):
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def load_dataset(dataset_dir: Path, split: str) -> Tuple[tf.data.Dataset, List[int], Dict[str, int]]:
    directory = dataset_dir / split
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Count samples per class
    counts = {}
    for c in CLASSES:
        cdir = directory / c
        counts[c] = len(list(cdir.glob("*.jpg")) + list(cdir.glob("*.png"))) if cdir.exists() else 0

    ds = tf.keras.utils.image_dataset_from_directory(
        directory,
        labels="inferred",
        label_mode="int",
        class_names=CLASSES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=(split == "train"),
        seed=SEED if split == "train" else None,
    )

    # Extract all labels for class weighting or metrics
    all_labels = []
    for _, y in ds:
        all_labels.extend(y.numpy().tolist())

    return ds, all_labels, counts


def build_plant_part_model(num_classes: int = len(CLASSES)) -> Tuple[tf.keras.Model, tf.keras.Model]:
    inputs = tf.keras.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3), name="image_input")

    # Field-robust data augmentation
    augmentation = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.20),
            tf.keras.layers.RandomZoom(height_factor=0.15, width_factor=0.15),
            tf.keras.layers.RandomBrightness(factor=0.15),
            tf.keras.layers.RandomContrast(factor=0.15),
        ],
        name="field_augmentation",
    )
    x = augmentation(inputs)

    # MobileNetV2 preprocessing: scales inputs to [-1, 1]
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)

    # MobileNetV2 feature extractor
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = tf.keras.layers.Dropout(0.30, name="dropout")(x)
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="plant_part_probs"
    )(x)

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="Stage1_MobileNetV2_PlantPart")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model, base_model


def train_and_evaluate(dataset_dir: Path = DEFAULT_DATASET_DIR, epochs: int = DEFAULT_EPOCHS):
    set_seed()
    print("=" * 70)
    print("PlantScan AI: Stage 1 MobileNetV2 Plant-Part Classifier Retraining")
    print(f"Dataset Path:   {dataset_dir}")
    print(f"Classes ({len(CLASSES)}):  {CLASSES}")
    print("=" * 70)

    train_ds, train_labels, train_counts = load_dataset(dataset_dir, "train")
    val_ds, val_labels, val_counts = load_dataset(dataset_dir, "val")
    test_ds, test_labels, test_counts = load_dataset(dataset_dir, "test")

    print("\nDataset Class Counts:")
    print(f"  Train ({len(train_labels)}): {train_counts}")
    print(f"  Val   ({len(val_labels)}): {val_counts}")
    print(f"  Test  ({len(test_labels)}): {test_counts}")

    # Compute balanced class weights for training
    unique_classes = np.unique(train_labels)
    class_weights_arr = compute_class_weight(
        class_weight="balanced",
        classes=unique_classes,
        y=np.array(train_labels),
    )
    class_weight_dict = {int(c): float(w) for c, w in zip(unique_classes, class_weights_arr)}
    print(f"\nComputed Balanced Class Weights: {class_weight_dict}")

    model, base_model = build_plant_part_model()

    print("\n[Phase 1] Training classification head (backbone frozen)...")
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True
        )
    ]
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=callbacks,
        class_weight=class_weight_dict,
        verbose=1,
    )

    print("\n[Phase 2] Fine-tuning top 30 MobileNetV2 layers...")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=10,
        callbacks=callbacks,
        class_weight=class_weight_dict,
        verbose=1,
    )

    # Evaluation on independent held-out test split
    print("\n[Phase 3] Evaluating on untouched cleaned held-out test split...")
    y_true = []
    y_pred = []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy().tolist())
        y_pred.extend(np.argmax(preds, axis=1).tolist())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    w_prec, w_rec, w_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    m_prec, m_rec, m_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    report_dict = classification_report(
        y_true, y_pred, target_names=CLASSES, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASSES)))).tolist()

    print("\n" + "=" * 70)
    print("Held-out Cleaned Test Set Evaluation Results:")
    print(f"  Test Accuracy:       {test_acc * 100:.2f}% (Target: >=85.0%)")
    print(f"  Weighted F1-Score:   {w_f1:.4f}")
    print(f"  Macro F1-Score:      {m_f1:.4f}")
    print("=" * 70)
    print(classification_report(y_true, y_pred, target_names=CLASSES, zero_division=0))

    # Save artifacts
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    keras_path = WEIGHTS_DIR / "plant_part_model.keras"
    model.save(keras_path)
    print(f"\n[OK] Keras model saved: {keras_path}")

    # Export TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = WEIGHTS_DIR / "plant_part_model.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"[OK] TFLite model exported: {tflite_path} ({len(tflite_model)/1024/1024:.2f} MB)")

    # Save classes.json
    classes_path = WEIGHTS_DIR / "classes.json"
    with open(classes_path, "w", encoding="utf-8") as f:
        json.dump(CLASSES, f, indent=2)
    print(f"[OK] Class manifest saved: {classes_path}")

    # Save evaluation report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    eval_file = REPORTS_DIR / "evaluation_report.json"
    eval_data = {
        "model_name": "Stage1_MobileNetV2_PlantPart_Cleaned",
        "dataset": str(dataset_dir),
        "dataset_status": "CLEANED_VERIFIED_PHOTOGRAPHS",
        "sample_counts": {
            "train": train_counts,
            "val": val_counts,
            "test": test_counts,
            "total_test": len(test_labels),
        },
        "num_classes": len(CLASSES),
        "classes": CLASSES,
        "test_loss": float(test_loss),
        "test_accuracy": float(test_acc),
        "weighted_precision": float(w_prec),
        "weighted_recall": float(w_rec),
        "weighted_f1": float(w_f1),
        "macro_precision": float(m_prec),
        "macro_recall": float(m_rec),
        "macro_f1": float(m_f1),
        "classification_report": report_dict,
        "confusion_matrix": cm,
        "target_met_85": bool(test_acc >= 0.85),
    }
    with open(eval_file, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)
    print(f"[OK] Cleaned evaluation report saved: {eval_file}")

    # Save comparative analysis against contaminated baseline
    comparison_file = REPORTS_DIR / "comparison_report.json"
    comparison_data = {
        "title": "Plant-Part Classifier: Cleaned vs. Contaminated Dataset Comparative Analysis",
        "contaminated_baseline": CONTAMINATED_BASELINE,
        "cleaned_evaluation": {
            "dataset": str(dataset_dir),
            "test_accuracy": float(test_acc),
            "macro_f1": float(m_f1),
            "weighted_f1": float(w_f1),
            "per_class_f1": {c: report_dict[c]["f1-score"] for c in CLASSES},
            "test_sample_count": len(test_labels),
        },
        "accuracy_delta": float(test_acc - CONTAMINATED_BASELINE["test_accuracy"]),
        "scientific_conclusion": (
            "The previous 81.97% test accuracy was measured on an uncleaned test set containing "
            "botanical engravings, historical sketches, scanned patent text, and mislabeled leaves. "
            "The new evaluation is measured on verified photographic plant specimens only. "
            f"Current cleaned test accuracy is {test_acc*100:.2f}%. "
            "A sample shortage remains in Fruit and Stem which must be addressed before declaring Phase 1 benchmark completion."
        ),
    }
    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)
    print(f"[OK] Comparison report saved: {comparison_file}")

    return eval_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Stage 1 Plant-Part Classifier")
    parser.add_argument("--dataset_dir", type=str, default=str(DEFAULT_DATASET_DIR))
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    args = parser.parse_args()
    train_and_evaluate(dataset_dir=Path(args.dataset_dir), epochs=args.epochs)
