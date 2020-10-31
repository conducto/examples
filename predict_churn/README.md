# Predict Churn

This creates an example pipeline to predict customer churn given some customer records and transaction data. Pipeline steps:
* Load in customer and transaction data
* Join them
* Compute features
* Fit and backtest several different ML models
* Analyze all the results and pick the best one.

### To Run

    python ./pipeline.py --local

### Concepts

- [pipeline-structure](https://conducto.com/docs/basics/controlling-a-pipeline)
- [data](https://conducto.com/api/data)
- [lazy-pipeline-creation](https://conducto.com/api/pipelines/#lazy-pipeline-creation)

