import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TreatmentRepository:
    """
    Repository for loading, caching, and querying plant disease treatment records,
    organic remedies, chemical protocols, prevention measures, and safety disclaimers.
    """

    def __init__(self, db_dir: Optional[Path] = None):
        if db_dir is None:
            self.db_dir = Path(__file__).resolve().parent
        else:
            self.db_dir = Path(db_dir)

        self._disclaimers: Dict[str, str] = {}
        self._default_unknown: Dict[str, Any] = {}
        self._crop_data: Dict[str, Dict[str, Any]] = {}
        self._class_to_treatment: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self.load_database()

    def load_database(self) -> None:
        """Loads all treatment JSON files and indexes them for fast lookup."""
        # Load Disclaimers
        disclaimers_path = self.db_dir / "disclaimers.json"
        if disclaimers_path.exists():
            with open(disclaimers_path, "r", encoding="utf-8") as f:
                self._disclaimers = json.load(f)

        # Load Default Unknown Record
        unknown_path = self.db_dir / "default_unknown.json"
        if unknown_path.exists():
            with open(unknown_path, "r", encoding="utf-8") as f:
                self._default_unknown = json.load(f)

        # Load Crop JSON Files
        json_files = list(self.db_dir.glob("*.json"))
        for file in json_files:
            if file.name in {"disclaimers.json", "default_unknown.json"}:
                continue

            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    crop_name = data.get("crop", file.stem.capitalize())
                    self._crop_data[crop_name.lower()] = data

                    diseases = data.get("diseases", {})
                    for disease_key, disease_info in diseases.items():
                        disease_info_with_crop = dict(disease_info)
                        disease_info_with_crop["crop"] = crop_name
                        self._class_to_treatment[disease_key.lower()] = disease_info_with_crop

                        # Also index by class_name if specified
                        canonical = disease_info.get("class_name", "").lower()
                        if canonical:
                            self._class_to_treatment[canonical] = disease_info_with_crop
            except Exception as e:
                print(f"Warning: Failed to parse {file}: {e}")

        self._loaded = True

    @property
    def disclaimers(self) -> Dict[str, str]:
        return self._disclaimers

    @property
    def default_unknown(self) -> Dict[str, Any]:
        return self._default_unknown

    def get_by_class(self, canonical_class: str) -> Optional[Dict[str, Any]]:
        """
        Lookup treatment by canonical class name (e.g., 'tomato_early_blight', 'cordana', etc.).
        """
        if not canonical_class:
            return None

        normalized = canonical_class.strip().lower()
        if normalized in self._class_to_treatment:
            return self._class_to_treatment[normalized]

        # Try prefix matching or underscore replacement
        norm_clean = normalized.replace("-", "_").replace(" ", "_")
        if norm_clean in self._class_to_treatment:
            return self._class_to_treatment[norm_clean]

        for key, record in self._class_to_treatment.items():
            if norm_clean in key or key in norm_clean:
                return record

        return None

    def get_by_crop_and_disease(self, crop: str, disease: str) -> Optional[Dict[str, Any]]:
        """
        Lookup treatment by crop name and disease name.
        """
        crop_lower = crop.strip().lower()
        disease_lower = disease.strip().lower().replace(" ", "_").replace("-", "_")

        # Try direct class key
        direct_key = f"{crop_lower}_{disease_lower}"
        if direct_key in self._class_to_treatment:
            return self._class_to_treatment[direct_key]

        # Try searching within the specific crop dataset
        if crop_lower in self._crop_data:
            diseases = self._crop_data[crop_lower].get("diseases", {})
            for key, info in diseases.items():
                if key.lower() == disease_lower or info.get("display_name", "").lower() == disease.lower():
                    info_with_crop = dict(info)
                    info_with_crop["crop"] = self._crop_data[crop_lower].get("crop", crop)
                    return info_with_crop

        return self.get_by_class(disease_lower)

    def list_supported_crops(self) -> List[str]:
        """Returns list of crops that have structured treatment data."""
        return [data.get("crop", name.capitalize()) for name, data in self._crop_data.items()]

    def list_all_canonical_classes(self) -> List[str]:
        """Returns list of all canonical disease classes available in the repository."""
        return sorted(list(self._class_to_treatment.keys()))
