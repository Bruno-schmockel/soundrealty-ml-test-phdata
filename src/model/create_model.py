import json
import pathlib
import pickle
import random
import string
from typing import List
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas
from sklearn import metrics
from sklearn import model_selection
from sklearn import neighbors
from sklearn import pipeline
from sklearn import preprocessing
from sklearn.inspection import permutation_importance

SALES_PATH = "data/kc_house_data.csv"  # path to CSV with home sale data
DEMOGRAPHICS_PATH = "data/zipcode_demographics.csv"  # path to CSV with demographics
# List of columns (subset) that will be taken from home sale data
SALES_COLUMN_SELECTION = [
    'price', 'bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors',
    'sqft_above', 'sqft_basement', 'grade', 'sqft_living15', 'zipcode'
]
OUTPUT_DIR = "model"  # Directory where output artifacts will be saved


def load_data(
    sales_path: str, demographics_path: str, sales_column_selection: List[str]
) -> Tuple[pandas.DataFrame, pandas.Series]:
    """Load the target and feature data by merging sales and demographics.

    Args:
        sales_path: path to CSV file with home sale data
        demographics_path: path to CSV file with demographics data
        sales_column_selection: list of columns from sales data to be used as
            features

    Returns:
        Tuple containg with two elements: a DataFrame and a Series of the same
        length.  The DataFrame contains features for machine learning, the
        series contains the target variable (home sale price).

    """
    data = pandas.read_csv(sales_path,
                           usecols=sales_column_selection, # pyright: ignore[reportArgumentType]
                           dtype={'zipcode': str})
    demographics = pandas.read_csv(demographics_path,
                                   dtype={'zipcode': str})

    merged_data = data.merge(demographics, how="left",
                             on="zipcode").drop(columns="zipcode")
    # Remove the target variable from the dataframe, features will remain
    y = merged_data.pop('price')
    x = merged_data

    return x, y


def evaluate_model(model, x_train, y_train, x_test, y_test, output_dir: pathlib.Path):
    """Evaluate the KNN model using multiple metrics and create visualizations.

    Args:
        model: Trained sklearn model pipeline
        x_train: Training features
        y_train: Training target values
        x_test: Test features
        y_test: Test target values
        output_dir: Directory to save evaluation plots
    """
    # Make predictions
    y_train_pred = model.predict(x_train)
    y_test_pred = model.predict(x_test)

    # Calculate metrics
    train_rmse = np.sqrt(metrics.mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(metrics.mean_squared_error(y_test, y_test_pred))
    train_mae = metrics.mean_absolute_error(y_train, y_train_pred)
    test_mae = metrics.mean_absolute_error(y_test, y_test_pred)
    train_r2 = metrics.r2_score(y_train, y_train_pred)
    test_r2 = metrics.r2_score(y_test, y_test_pred)
    test_mape = metrics.mean_absolute_percentage_error(y_test, y_test_pred)
    
    # Calculate bias-aware metric (penalizes underpricing 2x more than overpricing)
    def weighted_rmse_with_bias(y_true, y_pred, bias_weight=2.0):
        """RMSE that penalizes negative bias (underprediction) more heavily."""
        errors = y_true - y_pred
        weighted_errors = np.where(errors > 0, errors * bias_weight, errors)
        return np.sqrt(np.mean(weighted_errors ** 2))
    
    test_weighted_rmse = weighted_rmse_with_bias(y_test, y_test_pred)
    
    # Calculate percentage of underpredictions
    underpriced = (y_test_pred < y_test).sum()
    underpriced_pct = (underpriced / len(y_test)) * 100

    # Print metrics
    print("\n" + "="*60)
    print("MODEL EVALUATION METRICS")
    print("="*60)
    print(f"Training RMSE: ${train_rmse:,.2f}")
    print(f"Test RMSE:     ${test_rmse:,.2f}")
    print(f"\nTraining MAE:  ${train_mae:,.2f}")
    print(f"Test MAE:      ${test_mae:,.2f}")
    print(f"\nTraining R²:   {train_r2:.4f}")
    print(f"Test R²:       {test_r2:.4f}")
    print(f"Test MAPE:     {test_mape:.4f} ({test_mape*100:.2f}%)")    
    print("\n--- BIAS ANALYSIS (penalizes underpricing 2x) ---")
    print(f"Weighted RMSE: ${test_weighted_rmse:,.2f}")
    print(f"Underpriced:   {underpriced}/{len(y_test)} ({underpriced_pct:.1f}%)")    
    print("="*60 + "\n")

    # Save metrics to file
    metrics_data = {
        "train_rmse": float(train_rmse),
        "test_rmse": float(test_rmse),
        "train_mae": float(train_mae),
        "test_mae": float(test_mae),
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "test_mape": float(test_mape),
        "test_weighted_rmse": float(test_weighted_rmse),
        "underpriced_count": int(underpriced),
        "underpriced_percentage": float(underpriced_pct)
    }
    with open(output_dir / "metrics.json", 'w') as f:
        json.dump(metrics_data, f, indent=2)

    # Create visualizations
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('KNN Model Evaluation', fontsize=14, fontweight='bold')

    # 1. Actual vs Predicted (Test set)
    ax = axes[0, 0]
    ax.scatter(y_test, y_test_pred, alpha=0.5, edgecolors='k', linewidth=0.5)
    min_val = min(y_test.min(), y_test_pred.min())
    max_val = max(y_test.max(), y_test_pred.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
    ax.set_xlabel('Actual Price ($)')
    ax.set_ylabel('Predicted Price ($)')
    ax.set_title('Actual vs Predicted (Test Set)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Residuals vs Predicted
    ax = axes[0, 1]
    residuals = y_test - y_test_pred
    ax.scatter(y_test_pred, residuals, alpha=0.5, edgecolors='k', linewidth=0.5)
    ax.axhline(y=0, color='r', linestyle='--', lw=2)
    ax.set_xlabel('Predicted Price ($)')
    ax.set_ylabel('Residuals ($)')
    ax.set_title('Residual Plot (Test Set)')
    ax.grid(True, alpha=0.3)

    # 3. Error Distribution
    ax = axes[0, 2]
    errors = np.abs(y_test - y_test_pred)
    ax.hist(errors, bins=30, edgecolor='black', alpha=0.7)
    ax.axvline(test_mae, color='r', linestyle='--', lw=2, label=f'MAE: ${test_mae:,.0f}')
    ax.set_xlabel('Absolute Error ($)')
    ax.set_ylabel('Frequency')
    ax.set_title('Error Distribution (Test Set)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 4. Train vs Test Metrics
    ax = axes[1, 0]
    metrics_names = ['RMSE', 'MAE', 'R²']
    train_vals = [train_rmse, train_mae, train_r2]
    test_vals = [test_rmse, test_mae, test_r2]
    x_pos = np.arange(len(metrics_names))
    width = 0.35
    ax.bar(x_pos - width/2, train_vals, width, label='Train', alpha=0.8)
    ax.bar(x_pos + width/2, test_vals, width, label='Test', alpha=0.8)
    ax.set_ylabel('Value')
    ax.set_title('Train vs Test Metrics')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(metrics_names)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Bias Distribution (Over/Under pricing)
    ax = axes[1, 1]
    overpredicted = (y_test_pred > y_test).sum()
    correctly_balanced = len(y_test) - underpriced - overpredicted
    bias_counts = [underpriced, correctly_balanced, overpredicted]
    bias_labels = [f'Underpriced\n({underpriced_pct:.1f}%)', 
                   f'Balanced\n({correctly_balanced/len(y_test)*100:.1f}%)',
                   f'Overpriced\n({overpredicted/len(y_test)*100:.1f}%)']
    colors = ['#d62728', '#7f7f7f', '#2ca02c']
    ax.bar(bias_labels, bias_counts, color=colors, alpha=0.8, edgecolor='black')
    ax.set_ylabel('Count')
    ax.set_title('Prediction Bias Distribution')
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Bias Error (Negative bias penalty)
    ax = axes[1, 2]
    bias_errors = y_test - y_test_pred  # positive = underpriced, negative = overpriced
    underpriced_errors = bias_errors[bias_errors > 0]
    overpriced_errors = bias_errors[bias_errors < 0]
    ax.hist([underpriced_errors, overpriced_errors], bins=20, 
            label=['Underpriced', 'Overpriced'], color=['#d62728', '#2ca02c'], alpha=0.7, edgecolor='black')
    ax.set_xlabel('Bias Error ($)')
    ax.set_ylabel('Frequency')
    ax.set_title('Bias Error Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_dir / "model_evaluation.png", dpi=300, bbox_inches='tight')
    print(f"Evaluation plots saved to {output_dir / 'model_evaluation.png'}")
    plt.close()


def generate_model_explanations(model, x_test, y_test, output_dir: pathlib.Path):
    """Generate explainability artifacts for the model including feature importance.

    Args:
        model: Trained sklearn model pipeline
        x_test: Test features
        y_test: Test target values
        output_dir: Directory to save explanation artifacts
    """
    print("\n" + "="*60)
    print("GENERATING MODEL EXPLAINABILITY ANALYSIS")
    print("="*60)
    
    try:
        # Calculate permutation importance
        print("\nCalculating permutation importance...")
        perm_importance = permutation_importance(
            model, x_test, y_test, 
            n_repeats=10, 
            random_state=42,
            n_jobs=-1
        )
        
        # Create feature importance dataframe
        feature_importance_df = pandas.DataFrame({
            'feature': x_test.columns,
            'importance': perm_importance.importances_mean,
            'std': perm_importance.importances_std
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Most Important Features:")
        print(feature_importance_df.head(10).to_string(index=False))
        
        # Calculate feature contributions to predictions
        print("\nAnalyzing feature statistical properties...")
        feature_stats = {
            col: {
                'mean': float(x_test[col].mean()),
                'std': float(x_test[col].std()),
                'min': float(x_test[col].min()),
                'max': float(x_test[col].max()),
                'importance_score': float(feature_importance_df[
                    feature_importance_df['feature'] == col
                ]['importance'].values[0])
            }
            for col in x_test.columns
        }
        
        # Save explainability artifacts
        explanation_data = {
            "model_type": "KNeighborsRegressor with RobustScaler",
            "total_features": len(x_test.columns),
            "feature_importance_ranking": feature_importance_df.to_dict('records'),
            "feature_statistics": feature_stats,
            "explanation_date": pandas.Timestamp.now().isoformat()
        }
        
        print(f"\nWriting explanation data to {output_dir / 'model_explanation.json'}...")
        with open(output_dir / "model_explanation.json", 'w') as f:
            json.dump(explanation_data, f, indent=2)
        print("✓ Explanation JSON saved successfully")
        
        # Create explainability visualizations
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Model Explainability Analysis', fontsize=14, fontweight='bold')
        
        # 1. Feature Importance (Top 15)
        ax = axes[0, 0]
        top_features = feature_importance_df.head(15)
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top_features)))
        bars = ax.barh(range(len(top_features)), top_features['importance'], 
                        xerr=top_features['std'], color=colors, edgecolor='black', alpha=0.8)
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['feature'])
        ax.set_xlabel('Permutation Importance')
        ax.set_title('Feature Importance (Top 15)')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis='x')
        
        # 2. Feature Count vs Importance Threshold
        ax = axes[0, 1]
        cumsum_importance = np.cumsum(feature_importance_df['importance'].values)
        cumsum_importance = cumsum_importance / cumsum_importance[-1] * 100
        ax.plot(range(1, len(cumsum_importance) + 1), cumsum_importance, 'b-o', linewidth=2, markersize=4)
        ax.axhline(y=80, color='r', linestyle='--', label='80% Threshold')
        ax.axhline(y=90, color='orange', linestyle='--', label='90% Threshold')
        ax.set_xlabel('Number of Features')
        ax.set_ylabel('Cumulative Importance (%)')
        ax.set_title('Cumulative Feature Importance')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. Feature Importance Distribution
        ax = axes[1, 0]
        ax.hist(feature_importance_df['importance'], bins=20, edgecolor='black', alpha=0.7, color='steelblue')
        ax.axvline(feature_importance_df['importance'].mean(), color='r', linestyle='--', 
                   linewidth=2, label=f"Mean: {feature_importance_df['importance'].mean():.4f}")
        ax.set_xlabel('Importance Score')
        ax.set_ylabel('Frequency')
        ax.set_title('Feature Importance Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. Model Complexity Indicator
        ax = axes[1, 1]
        relevant_features = (feature_importance_df['importance'] > 0).sum()
        high_importance = (feature_importance_df['importance'] > feature_importance_df['importance'].mean()).sum()
        ax.text(0.5, 0.7, f"Total Features: {len(x_test.columns)}", 
                ha='center', fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax.text(0.5, 0.5, f"Relevant Features: {relevant_features}", 
                ha='center', fontsize=12, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax.text(0.5, 0.3, f"High Importance: {high_importance}", 
                ha='center', fontsize=12, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        ax.axis('off')
        ax.set_title('Model Complexity Summary')
        
        plt.tight_layout()
        plt.savefig(output_dir / "model_explanation.png", dpi=300, bbox_inches='tight')
        print(f"\nExplanation visualizations saved to {output_dir / 'model_explanation.png'}")
        plt.close()
        
        # Create a detailed explanation report
        explanation_report = f"""
# Model Explainability Report

## Model Overview
- **Type**: KNeighborsRegressor with RobustScaler preprocessing
- **Total Features**: {len(x_test.columns)}
- **Test Set Size**: {len(y_test)}

## Feature Importance Summary

### Top 10 Most Important Features:
"""
        
        for idx, row in feature_importance_df.head(10).iterrows():
            explanation_report += f"\n{row['feature']:30s} | Importance: {row['importance']:.6f} ± {row['std']:.6f}"
        
        explanation_report += f"""

## Key Insights

### Feature Coverage
- **Features Contributing to Predictions**: {relevant_features}
- **High Importance Features**: {high_importance} (above average)
- **Feature Coverage**: {(relevant_features / len(x_test.columns) * 100):.1f}%

### Model Complexity
- Model uses {len(x_test.columns)} features
- Top 5 features account for {(feature_importance_df.head(5)['importance'].sum() / feature_importance_df['importance'].sum() * 100):.1f}% of importance
- Feature importance is {'balanced' if feature_importance_df['importance'].std() < feature_importance_df['importance'].mean() else 'concentrated'}

### Feature Category Statistics
"""
        
        # Organize features by category (inferred from naming)
        feature_categories = {}
        for col in x_test.columns:
            if 'ppl' in col.lower() or 'popul' in col.lower():
                category = 'Population'
            elif 'incm' in col.lower() or 'income' in col.lower():
                category = 'Income'
            elif 'hous' in col.lower():
                category = 'Housing'
            elif 'educ' in col.lower():
                category = 'Education'
            elif 'urbn' in col.lower() or 'farm' in col.lower() or 'per_' in col.lower():
                category = 'Geography'
            else:
                category = 'Other'
            
            if category not in feature_categories:
                feature_categories[category] = []
            feature_categories[category].append(col)
        
        for category, features in sorted(feature_categories.items()):
            category_importance = feature_importance_df[
                feature_importance_df['feature'].isin(features)
            ]['importance'].sum()
            explanation_report += f"\n- **{category}**: {len(features)} features, total importance: {category_importance:.6f}"
        
        explanation_report += """

## Recommendations

1. **Feature Engineering**: Consider creating interaction terms between high-importance features
2. **Model Focus**: The model relies primarily on demographic and population features
3. **Data Quality**: Ensure accuracy of top-importance features for better predictions
4. **Feature Reduction**: Majority of model behavior driven by fewer than 20% of features
"""
        
        with open(output_dir / "EXPLANATION_REPORT.md", 'w') as f:
            f.write(explanation_report)
        
        print(f"Detailed explanation report saved to {output_dir / 'EXPLANATION_REPORT.md'}")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"✗ Error generating explanations: {e}")
        import traceback
        traceback.print_exc()



def main():
    """Load data, train model, evaluate, and export artifacts."""
    # Get model name from user
    model_name = input("Enter the name for this model: ").strip()
    if not model_name:
        # Generate a random 4-letter name
        model_name = ''.join(random.choices(string.ascii_lowercase, k=4))
        print(f"No name provided. Generated random model name: {model_name}")
    
    x, y = load_data(SALES_PATH, DEMOGRAPHICS_PATH, SALES_COLUMN_SELECTION)
    x_train, x_test, y_train, y_test = model_selection.train_test_split(
        x, y, random_state=42)

    model = pipeline.make_pipeline(preprocessing.RobustScaler(),
                                   neighbors.KNeighborsRegressor()).fit(
                                       x_train, y_train)

    output_dir = pathlib.Path(OUTPUT_DIR) / model_name
    output_dir.mkdir(parents=True, exist_ok=True)

    # Evaluate the model
    evaluate_model(model, x_train, y_train, x_test, y_test, output_dir)
    
    # Generate explainability analysis
    generate_model_explanations(model, x_test, y_test, output_dir)

    # Output model artifacts: pickled model and JSON list of features with datatypes
    pickle.dump(model, open(output_dir / "model.pkl", 'wb'))
    
    # Save features as a list for model prediction order, and include datatypes
    features_list = list(x_train.columns)
    features_with_types = {
        col: str(x_train[col].dtype) for col in features_list
    }
    
    json.dump(features_with_types, open(output_dir / "model_features.json", 'w'), indent=2)


if __name__ == "__main__":
    main()
