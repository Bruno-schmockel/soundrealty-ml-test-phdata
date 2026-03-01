
# Model Explainability Report

## Model Overview
- **Type**: KNeighborsRegressor with RobustScaler preprocessing
- **Total Features**: 35
- **Test Set Size**: 5404

## Feature Importance Summary

### Top 10 Most Important Features:

grade                          | Importance: 0.130330 ± 0.007549
farm_ppltn_qty                 | Importance: 0.108860 ± 0.013111
per_non_farm                   | Importance: 0.093664 ± 0.010383
per_urbn                       | Importance: 0.093533 ± 0.011245
non_farm_qty                   | Importance: 0.069637 ± 0.009809
sqft_living                    | Importance: 0.056146 ± 0.004166
sqft_lot                       | Importance: 0.052006 ± 0.010726
sqft_above                     | Importance: 0.050314 ± 0.005425
sqft_living15                  | Importance: 0.044455 ± 0.002981
per_less_than_9                | Importance: 0.028904 ± 0.002988

## Key Insights

### Feature Coverage
- **Features Contributing to Predictions**: 29
- **High Importance Features**: 11 (above average)
- **Feature Coverage**: 82.9%

### Model Complexity
- Model uses 35 features
- Top 5 features account for 57.6% of importance
- Feature importance is concentrated

### Feature Category Statistics

- **Geography**: 12 features, total importance: 0.305698
- **Housing**: 1 features, total importance: 0.025878
- **Income**: 2 features, total importance: 0.013987
- **Other**: 16 features, total importance: 0.383324
- **Population**: 4 features, total importance: 0.131715

## Recommendations

1. **Feature Engineering**: Consider creating interaction terms between high-importance features
2. **Model Focus**: The model relies primarily on demographic and population features
3. **Data Quality**: Ensure accuracy of top-importance features for better predictions
4. **Feature Reduction**: Majority of model behavior driven by fewer than 20% of features
