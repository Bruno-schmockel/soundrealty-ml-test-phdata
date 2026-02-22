import json
import pathlib
import pickle
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

SALES_PATH = "data/kc_house_data.csv"  # path to CSV with home sale data
DEMOGRAPHICS_PATH = "data/zipcode_demographics.csv"  # path to CSV with demographics
# List of columns (subset) that will be taken from home sale data
SALES_COLUMN_SELECTION = [
    'price', 'bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors',
    'sqft_above', 'sqft_basement', 'zipcode'
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


def main():
    """Load data, train model, evaluate, and export artifacts."""
    x, y = load_data(SALES_PATH, DEMOGRAPHICS_PATH, SALES_COLUMN_SELECTION)
    x_train, x_test, y_train, y_test = model_selection.train_test_split(
        x, y, random_state=42)

    model = pipeline.make_pipeline(preprocessing.RobustScaler(),
                                   neighbors.KNeighborsRegressor()).fit(
                                       x_train, y_train)

    output_dir = pathlib.Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    # Evaluate the model
    evaluate_model(model, x_train, y_train, x_test, y_test, output_dir)

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
