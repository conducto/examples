"""
Implementation of the actual steps in the Predit Churn pipeline.
* `compute_features` does feature engineering
* `fit` runs a variety of machine learning methods
* `backtest` evaluates the model against the input data
* `analyze` aggregates all the models and shows the output.

Note that the pipeline calls the R script `analyze.R` instead of this file's
`analyze()` function. We use the R version in order to emphasize that Conducto
can run commands in any language. If you work exclusively in Python, you may
want to see the "analyze" step implemented in Python, so we've included it even
though it is unused.
"""

import conducto as co
import joblib
import numpy as np
import os
import pandas as pd
import pprint

# For visualization
import matplotlib.pyplot as plt
pd.options.display.max_rows = None
pd.options.display.max_columns = None

from sklearn.model_selection import RandomizedSearchCV

# Fit models
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from scipy.stats import loguniform, randint

# Scoring functions
from sklearn.metrics import classification_report
from sklearn.metrics import roc_auc_score
from sklearn.metrics import roc_curve

np.random.seed(314159)


def compute_features(input: str, output: str):
    """
    This step takes in raw data and outputs features suitable for an ML model.

    Modelling choices include:
    * One-hot encode categorical variables
    * Make some nonlinear combinations of certain variables
    * Scale continuous variables to be between 0 and 1.
    """
    co.nb.matplotlib_inline()

    df = pd.read_csv(input)

    # Show proportion of customers exited vs retained
    labels = 'Exited', 'Retained'
    sizes = [df.Exited[df['Exited'] == 1].count(), df.Exited[df['Exited'] == 0].count()]
    explode = (0, 0.1)
    fig1, ax1 = plt.subplots(figsize=(5, 4))
    ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
    ax1.axis('equal')
    plt.title("Proportion of customers churned vs retained", size=10)
    plt.show()

    # Drop meaningless index columns, as well as surname which would likely be
    # profiling.
    df.drop(["RowNumber", "CustomerId", "Surname"], axis=1, inplace=True)

    # Normalize balance by salary, and tenure and credit score by age.
    df["BalanceSalaryRatio"] = df.Balance / df.EstimatedSalary
    df["TenureByAge"] = df.Tenure / df.Age
    df["CreditScoreGivenAge"] = df.CreditScore / df.Age

    # Arrange columns by data type for easier manipulation
    continuous_vars = ['CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts', 'EstimatedSalary',
                       'BalanceSalaryRatio',
                       'TenureByAge', 'CreditScoreGivenAge']
    cat_vars = ['HasCrCard', 'IsActiveMember', 'Geography', 'Gender']
    df = df[['Exited'] + continuous_vars + cat_vars]

    # For the one hot variables, we change 0 to -1 so that the models can capture
    # a negative relation where the attribute is inapplicable instead of 0
    df.loc[df.HasCrCard == 0, 'HasCrCard'] = -1
    df.loc[df.IsActiveMember == 0, 'IsActiveMember'] = -1

    # One hot encode the categorical variables
    lst = ['Geography', 'Gender']
    remove = list()
    for i in lst:
        if df[i].dtype == np.str or df[i].dtype == np.object:
            for j in df[i].unique():
                df[i + '_' + j] = np.where(df[i] == j, 1, -1)
            remove.append(i)
    df = df.drop(remove, axis=1)

    # Scale continuous variables to go from 0 to 1.
    min_vec = df[continuous_vars].min().copy()
    max_vec = df[continuous_vars].max().copy()
    df[continuous_vars] = (df[continuous_vars] - min_vec) / (max_vec - min_vec)

    # Print results
    _df_pretty(df.head().transpose().round(2))

    os.makedirs(os.path.dirname(output), exist_ok=True)
    df.to_csv(output)


def fit(model, input: str, output: str):
    """
    Fit a machine learning model.
    """
    print(f"Fitting model of type: {model}")

    # Define the model. Use a randomized search to efficiently explore the
    # hyperparameter space in a limited time.
    if model == "logistic":
        # Primal logistic regression
        param_dist = {
            'C': loguniform(0.1, 100), 'max_iter': [250], 'fit_intercept': [True],
            'intercept_scaling': [1], 'penalty': ['l2'], 'tol': loguniform(1e-6, 1e-4)
        }
        mdl_cv = RandomizedSearchCV(LogisticRegression(solver='lbfgs'), param_dist, cv=3, refit=True, verbose=2, n_iter=10)
    elif model == "rand_forest":
        # Random Forest classifier
        param_dist = {'max_depth': randint(3,8), 'max_features': randint(2,9), 'n_estimators': randint(50, 100),
                      'min_samples_split': randint(3, 7)}
        mdl_cv = RandomizedSearchCV(RandomForestClassifier(), param_dist, cv=3, refit=True, verbose=2, n_iter=10)
    elif model == "gradient_boost":
        # Extreme Gradient Boost classifier
        param_dist = {'max_depth': [3, 4], 'gamma': loguniform(1e-3, 1e-2), 'min_child_weight': randint(1, 10),
                      'learning_rate': loguniform(0.05, 0.3), 'n_estimators': randint(10, 40)}
        mdl_cv = RandomizedSearchCV(XGBClassifier(), param_dist, cv=3, refit=True, verbose=2, n_iter=10)
    else:
        raise NotImplementedError(f"Don't know how to train model of type: {model}.\nValid options are: logistic, rand_forest, gradient_boost.")

    # Define x (input data) and y (target data)
    df = pd.read_csv(input)
    x = df.loc[:, df.columns != 'Exited']
    y = df.Exited
    print(f"Data has x.shape = {x.shape} and y.shape = {y.shape}")

    # Fit the model with randomized search
    mdl_cv.fit(x, y)

    # Print some results
    print("Best score:", mdl_cv.best_score_)
    print("Best params:", pprint.pformat(mdl_cv.best_params_))

    # Save to data store
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "wb") as f:
        joblib.dump(mdl_cv.best_estimator_, f)


def backtest(features: str, model: str, output: str):
    """
    Backtest the model against the given features. Output a DataFrame that
    records, for each observation:
    * The true value (column name `true`)
    * The probability of correctness (column name `proba`)
    * The predicted truth value, i.e., whether `proba` exceeds the threshold
      (column name `pred`).
    """
    # Load model from data store
    with open(model, "rb") as f:
        mdl = joblib.load(f)

    # Load feature data. In a true pipeline there would be a split between
    # training and testing data, but this was omitted for clarity.
    #
    # ** Never run a real backtest on in-sample data!! **
    df = pd.read_csv(features)
    x = df.loc[:, df.columns != 'Exited']
    y_true = df.Exited
    y_pred = mdl.predict(x)
    y_proba = mdl.predict_proba(x)[:,1]
    print(classification_report(y_true, y_pred))

    # Write predictions to output file
    res = pd.DataFrame(data={"true": y_true, "proba": y_proba, "pred": y_pred})

    os.makedirs(os.path.dirname(output), exist_ok=True)
    res.to_csv(output)


def analyze(results: str):
    """
    Plot the true positive rate vs false positive rate for each model.
    """
    # Initialize plot
    co.nb.matplotlib_inline()
    plt.figure(figsize=(5, 4), linewidth=1)

    for model in os.listdir(results):
        # For each model, read in the results DataFrame
        df = pd.read_csv(os.path.join(results, model))

        # Compute statistics
        auc = roc_auc_score(df.true, df.pred)
        fpr, tpr, _ = roc_curve(df.true, df.proba)

        # Plot the stats
        plt.plot(fpr, tpr, label=f'{model} Score: ' + str(round(auc, 5)))

    # Finish up the plot and print it
    plt.plot([0, 1], [0, 1], 'k--', label='Random: 0.5')
    plt.xlabel('False positive rate')
    plt.ylabel('True positive rate')
    plt.title('ROC Curve')
    plt.legend(loc='best')
    plt.show()


def _df_pretty(df):
    # Print out results as markdown
    print(f"""
<ConductoMarkdown>
{df.to_markdown()}
</ConductoMarkdown>
""")


if __name__ == "__main__":
    co.main()