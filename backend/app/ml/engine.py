# pyright: reportOptionalCall=false, reportOptionalMemberAccess=false
"""ML model training and prediction engine.

Dependencies (optional):
    pip install scikit-learn joblib

If sklearn is not installed, a lightweight fallback implementation is provided.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date, timedelta
from typing import Any

import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# Optional sklearn import
try:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier  # type: ignore[import-untyped]
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
    from sklearn.metrics import accuracy_score, f1_score  # type: ignore[import-untyped]
    from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
    import joblib  # type: ignore[import-untyped]

    HAS_SKLEARN = True

    MODEL_TYPES = {
        "random_forest": lambda hp: RandomForestClassifier(  # type: ignore[operator]
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth", 10),
            min_samples_split=hp.get("min_samples_split", 5),
            random_state=42,
        ),
        "gradient_boosting": lambda hp: GradientBoostingClassifier(  # type: ignore[operator]
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth", 5),
            learning_rate=hp.get("learning_rate", 0.1),
            random_state=42,
        ),
        "logistic": lambda hp: LogisticRegression(  # type: ignore[operator]
            C=hp.get("C", 1.0),
            max_iter=hp.get("max_iter", 1000),
            random_state=42,
        ),
    }
except ImportError:
    HAS_SKLEARN = False
    RandomForestClassifier = None  # type: ignore[misc,assignment]
    GradientBoostingClassifier = None  # type: ignore[misc,assignment]
    LogisticRegression = None  # type: ignore[misc,assignment]
    accuracy_score = None  # type: ignore[misc,assignment]
    f1_score = None  # type: ignore[misc,assignment]
    train_test_split = None  # type: ignore[misc,assignment]
    joblib = None  # type: ignore[misc,assignment]
    MODEL_TYPES = {}  # type: ignore[misc,assignment]

MODEL_DIR = os.path.join(settings.DATA_DIR, "ml_models")
os.makedirs(MODEL_DIR, exist_ok=True)


class MLEngine:

    def __init__(self, db):
        self.db = db

    def prepare_features(
        self,
        instrument_id: int,
        feature_names: list[str],
        start_date: date,
        end_date: date,
        target_horizon: int = 5,
        target_type: str = "binary_up",
    ) -> tuple[np.ndarray, np.ndarray, list[date], list[str]]:
        from sqlalchemy import select
        from app.features.models import FeatureDefinition, FeatureValue
        from app.data.models import DailyBar

        fdefs = list(
            self.db.execute(
                select(FeatureDefinition).where(FeatureDefinition.name.in_(feature_names))
            ).scalars().all()
        )
        if not fdefs:
            raise ValueError(f"No feature definitions found for: {feature_names}")

        fdef_map = {fd.name: fd.id for fd in fdefs}
        valid_names = [n for n in feature_names if n in fdef_map]

        all_fvs: dict[tuple[str, date], float] = {}
        for fd in fdefs:
            fvs = list(
                self.db.execute(
                    select(FeatureValue).where(
                        FeatureValue.instrument_id == instrument_id,
                        FeatureValue.feature_definition_id == fd.id,
                        FeatureValue.date >= start_date,
                        FeatureValue.date <= end_date,
                    ).order_by(FeatureValue.date)
                ).scalars().all()
            )
            for fv in fvs:
                all_fvs[(fd.name, fv.date)] = fv.value

        bars = list(
            self.db.execute(
                select(DailyBar).where(
                    DailyBar.instrument_id == instrument_id,
                    DailyBar.trade_date >= start_date,
                    DailyBar.trade_date <= end_date + timedelta(days=target_horizon + 5),
                ).order_by(DailyBar.trade_date)
            ).scalars().all()
        )
        price_map = {b.trade_date: b.close for b in bars}

        dates = sorted(set(d for _, d in all_fvs.keys()))
        X_rows, y_rows, dates_used = [], [], []

        for dt in dates:
            row = []
            missing = False
            for fname in valid_names:
                val = all_fvs.get((fname, dt))
                if val is None:
                    missing = True
                    break
                row.append(val)
            if missing:
                continue

            future_date = dt + timedelta(days=int(target_horizon * 1.5))
            future_price = None
            for offset in range(target_horizon, target_horizon + 10):
                check = dt + timedelta(days=offset)
                if check in price_map:
                    future_price = price_map[check]
                    break
            current_price = price_map.get(dt)
            if current_price is None or future_price is None:
                continue

            if target_type == "binary_up":
                target = 1 if future_price > current_price else 0
            elif target_type == "binary_down":
                target = 1 if future_price < current_price else 0
            else:  # regression
                target = (future_price - current_price) / current_price

            X_rows.append(row)
            y_rows.append(target)
            dates_used.append(dt)

        if not X_rows:
            return np.array([]), np.array([]), [], valid_names

        return np.array(X_rows), np.array(y_rows), dates_used, valid_names

    def train(
        self,
        config: dict[str, Any],
        instrument_id: int | None = None,
    ) -> dict[str, Any]:
        if not HAS_SKLEARN:
            return self._fallback_train(config, instrument_id)

        assert train_test_split is not None
        assert accuracy_score is not None
        assert f1_score is not None
        assert joblib is not None

        model_type = config.get("model_type", "random_forest")
        feature_names = config.get("feature_set", [])
        hyperparameters = config.get("hyperparameters", {})
        target_horizon = config.get("target_horizon", 5)
        target_type = config.get("target_type", "binary_up")
        train_start = date.fromisoformat(config["train_start"])
        train_end = date.fromisoformat(config["train_end"])
        test_split = config.get("test_split", 0.2)

        if model_type not in MODEL_TYPES:
            raise ValueError(f"Unknown model type: {model_type}. Choose from {list(MODEL_TYPES.keys())}")

        if instrument_id is None:
            from sqlalchemy import select
            from app.data.models import Instrument
            instruments = list(self.db.execute(select(Instrument.id)).scalars().all())
        else:
            instruments = [instrument_id]

        all_X, all_y = [], []
        feature_names_used: list[str] = list(feature_names)
        for ins_id in instruments:
            X, y, _, feature_names_used = self.prepare_features(
                ins_id, feature_names, train_start, train_end, target_horizon, target_type
            )
            if len(X) > 0:
                all_X.append(X)
                all_y.append(y)

        if not all_X:
            return {"error": "No training data available", "status": "failed"}

        X = np.vstack(all_X)
        y = np.concatenate(all_y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_split, shuffle=False
        )

        model = MODEL_TYPES[model_type](hyperparameters)
        model.fit(X_train, y_train)

        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)

        metrics = {
            "train_accuracy": float(accuracy_score(y_train, train_pred)),
            "test_accuracy": float(accuracy_score(y_test, test_pred)),
            "train_f1": float(f1_score(y_train, train_pred, zero_division=0)),
            "test_f1": float(f1_score(y_test, test_pred, zero_division=0)),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }

        feature_importance = {}
        if hasattr(model, "feature_importances_"):
            for fname, imp in zip(feature_names_used, model.feature_importances_):
                feature_importance[fname] = float(imp)
        elif hasattr(model, "coef_"):
            for fname, coef in zip(feature_names_used, model.coef_[0]):
                feature_importance[fname] = float(coef)

        config_hash = hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()[:12]
        model_filename = f"model_{config_hash}_{train_end.isoformat()}.joblib"
        model_path = os.path.join(MODEL_DIR, model_filename)
        joblib.dump(model, model_path)

        return {
            "status": "completed",
            "metrics": metrics,
            "feature_importance": feature_importance,
            "model_path": model_path,
            "feature_names": feature_names_used,
        }

    def predict(
        self,
        model_path: str,
        instrument_id: int,
        as_of_date: date,
        feature_names: list[str],
    ) -> dict[str, Any]:
        if not HAS_SKLEARN:
            return self._fallback_predict()

        assert joblib is not None

        if not os.path.exists(model_path):
            return {"error": f"Model file not found: {model_path}"}

        model = joblib.load(model_path)

        from sqlalchemy import select
        from app.features.models import FeatureDefinition, FeatureValue

        fdefs = list(
            self.db.execute(
                select(FeatureDefinition).where(FeatureDefinition.name.in_(feature_names))
            ).scalars().all()
        )

        row = []
        features_used = {}
        for fd in fdefs:
            fv = self.db.execute(
                select(FeatureValue).where(
                    FeatureValue.instrument_id == instrument_id,
                    FeatureValue.feature_definition_id == fd.id,
                    FeatureValue.date <= as_of_date,
                ).order_by(FeatureValue.date.desc()).limit(1)
            ).scalar_one_or_none()
            if fv is None:
                return {"error": f"Missing feature value for {fd.name} on {as_of_date}"}
            row.append(fv.value)
            features_used[fd.name] = fv.value

        X = np.array([row])
        prediction = model.predict(X)[0]

        confidence = 0.5
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
            confidence = float(max(proba))

        return {
            "predicted_value": float(prediction),
            "confidence": confidence,
            "features_used": features_used,
            "model_path": model_path,
        }

    def _fallback_train(self, config: dict, instrument_id: int | None) -> dict:
        logger.warning("sklearn not installed – using fallback mean predictor")
        return {
            "status": "completed_fallback",
            "metrics": {"note": "Install scikit-learn for real ML training"},
            "feature_importance": {},
            "model_path": None,
        }

    def _fallback_predict(self) -> dict:
        return {
            "predicted_value": 0.5,
            "confidence": 0.5,
            "features_used": {},
            "model_path": None,
            "note": "Install scikit-learn for real predictions",
        }
