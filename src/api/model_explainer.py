"""Model explanation and interpretation utilities."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np
import pandas as pd


class ModelExplainer:
    """Provides explanations for model predictions."""
    
    def __init__(self, model_dir: str = "model"):
        """Initialize the model explainer.
        
        Args:
            model_dir: Directory containing model artifacts
        """
        self.model_dir = Path(model_dir)
        self.explanation_cache: Dict[str, Any] = {}
        self._load_explanations()
    
    def _load_explanations(self):
        """Load pre-computed explanation artifacts."""
        for model_path in self.model_dir.glob("*/model_explanation.json"):
            model_name = model_path.parent.name
            try:
                with open(model_path) as f:
                    self.explanation_cache[model_name] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass
    
    def get_feature_importance(self, model_name: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get the most important features for a model.
        
        Args:
            model_name: Name of the model
            top_n: Number of top features to return
            
        Returns:
            List of feature importance dictionaries
        """
        if model_name not in self.explanation_cache:
            return []
        
        explanation = self.explanation_cache[model_name]
        ranking = explanation.get('feature_importance_ranking', [])
        return ranking[:top_n]
    
    def get_prediction_explanation(
        self,
        model_name: str,
        input_dict: Dict[str, Any],
        prediction: float
    ) -> Dict[str, Any]:
        """Generate an explanation for a specific prediction.
        
        Args:
            model_name: Name of the model
            input_dict: Input features used for prediction
            prediction: The predicted value
            
        Returns:
            Dictionary containing prediction explanation
        """
        if model_name not in self.explanation_cache:
            return {"error": f"No explanation available for model {model_name}"}
        
        explanation = self.explanation_cache[model_name]
        feature_stats = explanation.get('feature_statistics', {})
        feature_importance = {
            item['feature']: item['importance'] 
            for item in explanation.get('feature_importance_ranking', [])
        }
        
        # Analyze input relative to feature statistics
        feature_analysis = []
        for feature, value in input_dict.items():
            if feature in feature_stats:
                stats = feature_stats[feature]
                z_score = (value - stats['mean']) / stats['std'] if stats['std'] > 0 else 0
                importance = feature_importance.get(feature, 0)
                
                feature_analysis.append({
                    'feature': feature,
                    'value': float(value),
                    'mean': stats['mean'],
                    'std': stats['std'],
                    'z_score': float(z_score),
                    'importance': float(importance),
                    'analysis': self._analyze_feature_value(z_score, importance)
                })
        
        # Sort by importance
        feature_analysis.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            'model_name': model_name,
            'prediction': float(prediction),
            'feature_analysis': feature_analysis[:10],  # Top 10 important features
            'prediction_confidence': self._estimate_confidence(feature_analysis),
            'key_drivers': [
                f['feature'] for f in feature_analysis[:5]
            ]
        }
    
    def _analyze_feature_value(self, z_score: float, importance: float) -> str:
        """Generate a natural language description of a feature value.
        
        Args:
            z_score: Standard deviation from mean
            importance: Feature importance score
            
        Returns:
            Descriptive string
        """
        magnitude = ""
        if abs(z_score) < 0.5:
            magnitude = "typical"
        elif abs(z_score) < 1:
            magnitude = "slightly unusual"
        elif abs(z_score) < 2:
            magnitude = "unusual"
        else:
            magnitude = "very unusual"
        
        direction = ""
        if z_score > 0:
            direction = f"above average (z={z_score:.2f})"
        elif z_score < 0:
            direction = f"below average (z={z_score:.2f})"
        else:
            direction = "at average"
        
        impact = ""
        if importance > 0.01:
            impact = " - HIGH IMPACT"
        elif importance > 0.005:
            impact = " - moderate impact"
        else:
            impact = " - low impact"
        
        return f"{magnitude}, {direction}{impact}"
    
    def _estimate_confidence(self, feature_analysis: List[Dict[str, Any]]) -> float:
        """Estimate prediction confidence based on feature analysis.
        
        Args:
            feature_analysis: List of analyzed features
            
        Returns:
            Confidence score between 0 and 1
        """
        if not feature_analysis:
            return 0.5
        
        # High confidence when important features are typical
        importance_weights = [f['importance'] for f in feature_analysis]
        z_scores = [abs(f['z_score']) for f in feature_analysis]
        
        if sum(importance_weights) == 0:
            return 0.5
        
        # Weighted average of how typical the features are
        weighted_z = sum(z * w for z, w in zip(z_scores, importance_weights)) / sum(importance_weights)
        confidence = 1.0 / (1.0 + weighted_z)  # Sigmoid-like function
        return float(np.clip(confidence, 0.0, 1.0))
    
    def get_model_summary(self, model_name: str) -> Dict[str, Any]:
        """Get a summary of a model's characteristics.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model summary
        """
        if model_name not in self.explanation_cache:
            return {"error": f"Model {model_name} not found"}
        
        explanation = self.explanation_cache[model_name]
        return {
            'model_name': model_name,
            'model_type': explanation.get('model_type'),
            'total_features': explanation.get('total_features'),
            'top_5_features': [
                item['feature'] 
                for item in explanation.get('feature_importance_ranking', [])[:5]
            ],
            'explanation_generated': explanation.get('explanation_date')
        }
