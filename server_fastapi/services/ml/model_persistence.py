"""
Model Persistence Service - Unified save/load for all ML models
"""

import json
import logging
import os
import pickle
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ModelMetadata(BaseModel):
    """Model metadata for persistence"""

    model_config = {"protected_namespaces": ()}

    model_type: str  # 'lstm', 'gru', 'transformer', 'xgboost', etc.
    model_version: str
    created_at: str
    updated_at: str
    config: dict[str, Any]
    performance_metrics: dict[str, Any] | None = None
    dataset_hash: str | None = None
    training_config: dict[str, Any] | None = None
    training_history: dict[str, Any] | None = None
    feature_count: int | None = None
    sequence_length: int | None = None


class ModelPersistence:
    """Unified model persistence service"""

    def __init__(self, base_dir: str = "models"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_model(
        self,
        model: Any,
        model_type: str,
        model_name: str,
        metadata: dict[str, Any] | None = None,
        version: str = "1.0.0",
    ) -> bool:
        """Save model with metadata"""
        try:
            model_dir = os.path.join(self.base_dir, model_type, model_name)
            os.makedirs(model_dir, exist_ok=True)

            # Save model
            model_path = os.path.join(model_dir, f"{model_name}_{version}.model")

            if model_type in ["lstm", "gru", "transformer"]:
                # TensorFlow/Keras models
                if hasattr(model, "save"):
                    model.save(model_path.replace(".model", ".h5"))
                else:
                    logger.error(f"Model {model_type} does not have save method")
                    return False

            elif model_type == "xgboost":
                # XGBoost models
                if hasattr(model, "save_model"):
                    model.save_model(model_path)
                else:
                    logger.error("XGBoost model does not have save_model method")
                    return False

            else:
                # Generic pickle for other models
                with open(model_path, "wb") as f:
                    pickle.dump(model, f)

            # Save metadata
            metadata_obj = ModelMetadata(
                model_type=model_type,
                model_version=version,
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
                config=metadata.get("config", {}) if metadata else {},
                performance_metrics=(
                    metadata.get("performance_metrics") if metadata else None
                ),
                dataset_hash=metadata.get("dataset_hash") if metadata else None,
                training_config=metadata.get("training_config") if metadata else None,
                training_history=metadata.get("training_history") if metadata else None,
                feature_count=metadata.get("feature_count") if metadata else None,
                sequence_length=metadata.get("sequence_length") if metadata else None,
            )

            metadata_path = os.path.join(
                model_dir, f"{model_name}_{version}_metadata.json"
            )
            with open(metadata_path, "w") as f:
                json.dump(metadata_obj.dict(), f, indent=2)

            # Save latest version pointer
            latest_path = os.path.join(model_dir, "latest.json")
            with open(latest_path, "w") as f:
                json.dump(
                    {
                        "version": version,
                        "model_path": model_path,
                        "metadata_path": metadata_path,
                        "updated_at": datetime.now(UTC).isoformat(),
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Model saved: {model_type}/{model_name} v{version}")
            return True

        except Exception as error:
            logger.error(f"Failed to save model: {error}")
            return False

    def load_model(
        self, model_type: str, model_name: str, version: str | None = None
    ) -> dict[str, Any] | None:
        """Load model with metadata"""
        try:
            model_dir = os.path.join(self.base_dir, model_type, model_name)

            # Determine version
            if version is None:
                latest_path = os.path.join(model_dir, "latest.json")
                if os.path.exists(latest_path):
                    with open(latest_path) as f:
                        latest_info = json.load(f)
                    version = latest_info["version"]
                    model_path = latest_info["model_path"]
                    metadata_path = latest_info["metadata_path"]
                else:
                    logger.error(
                        f"No latest version found for {model_type}/{model_name}"
                    )
                    return None
            else:
                model_path = os.path.join(model_dir, f"{model_name}_{version}.model")
                metadata_path = os.path.join(
                    model_dir, f"{model_name}_{version}_metadata.json"
                )

            # Load metadata
            if os.path.exists(metadata_path):
                with open(metadata_path) as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # Load model based on type
            if model_type in ["lstm", "gru", "transformer"]:
                import tensorflow as tf

                model_file = model_path.replace(".model", ".h5")
                if os.path.exists(model_file):
                    model = tf.keras.models.load_model(model_file)
                else:
                    logger.error(f"Model file not found: {model_file}")
                    return None

            elif model_type == "xgboost":
                import xgboost as xgb

                if os.path.exists(model_path):
                    model = xgb.XGBClassifier()
                    model.load_model(model_path)
                else:
                    logger.error(f"Model file not found: {model_path}")
                    return None

            else:
                # Generic pickle
                if os.path.exists(model_path):
                    with open(model_path, "rb") as f:
                        model = pickle.load(f)
                else:
                    logger.error(f"Model file not found: {model_path}")
                    return None

            return {
                "model": model,
                "metadata": metadata,
                "model_path": model_path,
                "metadata_path": metadata_path,
            }

        except Exception as error:
            logger.error(f"Failed to load model: {error}")
            return None

    def list_models(self, model_type: str | None = None) -> dict[str, Any]:
        """List all saved models"""
        models = {}

        if model_type:
            type_dir = os.path.join(self.base_dir, model_type)
            if os.path.exists(type_dir):
                models[model_type] = self._list_models_in_dir(type_dir)
        else:
            for type_name in os.listdir(self.base_dir):
                type_path = os.path.join(self.base_dir, type_name)
                if os.path.isdir(type_path):
                    models[type_name] = self._list_models_in_dir(type_path)

        return models

    def _list_models_in_dir(self, dir_path: str) -> list[dict[str, Any]]:
        """List models in a directory"""
        models = []

        for model_name in os.listdir(dir_path):
            model_dir = os.path.join(dir_path, model_name)
            if os.path.isdir(model_dir):
                latest_path = os.path.join(model_dir, "latest.json")
                if os.path.exists(latest_path):
                    with open(latest_path) as f:
                        latest_info = json.load(f)

                    metadata_path = latest_info.get("metadata_path")
                    metadata = {}
                    if metadata_path and os.path.exists(metadata_path):
                        with open(metadata_path) as f:
                            metadata = json.load(f)

                    models.append(
                        {
                            "name": model_name,
                            "version": latest_info["version"],
                            "updated_at": latest_info["updated_at"],
                            "metadata": metadata,
                        }
                    )

        return models
