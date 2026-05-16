# ReliSource Junior ML Engineer - Written Exam Prep (Expanded, Role-Aligned)

This guide is tailored to the Junior ML Engineer role details you provided. It focuses on fundamentals, ML pipelines, MLOps basics, and applied reasoning for a written exam. Answers are intentionally fuller so you can study the reasoning and rephrase during the exam.

## 1) Math + Stats Essentials (Expanded Q&A)

**Q1. Explain the bias-variance tradeoff with a concrete example.**
A. Bias is error from simplifying assumptions; variance is error from sensitivity to data fluctuations. A linear model on a complex non-linear dataset usually underfits (high bias, low variance). A deep model with many parameters might fit training data perfectly but generalize poorly (low bias, high variance). The goal is to choose model complexity and regularization that minimize total error.

**Q2. When do you use L1 vs L2 regularization?**
A. L1 adds absolute weight penalties, which can zero out many coefficients, so it is useful for feature selection and sparse models. L2 adds squared penalties, which shrink weights smoothly, so it is better when many correlated features matter and you want stability.

**Q3. What is a p-value and why is it often misunderstood?**
A. The p-value is the probability of observing data at least as extreme as what you saw, assuming the null hypothesis is true. It does not measure the probability that the hypothesis is true. Small p-values can indicate evidence against the null, but they do not prove practical significance.

**Q4. Define precision, recall, and F1, and explain when each matters.**
A. Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 is the harmonic mean of precision and recall. Precision matters when false positives are costly, recall matters when false negatives are costly. F1 is useful when you need a single metric for imbalanced classes.

**Q5. What does ROC-AUC measure and when is PR-AUC better?**
A. ROC-AUC measures ranking quality across thresholds and is robust to class imbalance in terms of ranking. PR-AUC focuses on precision and recall and is more informative when the positive class is rare.

**Q6. Standardization vs normalization: why and when?**
A. Standardization makes features zero-mean and unit-variance, which helps models that assume normality or are sensitive to feature scales (SVM, logistic regression, neural nets). Normalization scales to a fixed range and is useful when you need bounded values (distance-based methods like k-NN).

**Q7. What is ANOVA used for in ML?**
A. ANOVA tests if group means are significantly different. In ML, it can be used for feature selection or to compare model performance across groups.

**Q8. Explain Bayesian inference in one paragraph.**
A. Bayesian inference updates beliefs using evidence. You start with a prior distribution that represents belief before seeing data, combine it with the likelihood of the observed data, and obtain a posterior distribution that represents updated belief. This is useful when you want uncertainty estimates or when data is limited.

**Q9. What is the difference between Type I and Type II errors?**
A. Type I is a false positive (rejecting a true null). Type II is a false negative (failing to reject a false null). The balance depends on the cost of each error.

## 2) ML Fundamentals (Core Q&A)

**Q1. How do you choose a model for classification vs regression?**
A. The target type determines the task: categorical for classification, continuous for regression. Model selection then depends on interpretability, data size, nonlinearity, and latency constraints. A baseline model is essential before complex models.

**Q2. What is overfitting and how do you prevent it in practice?**
A. Overfitting is when a model learns noise instead of signal. Prevention includes train/validation splits, cross-validation, regularization, early stopping, data augmentation, and choosing a simpler model or fewer features.

**Q3. Why use cross-validation and when might it be misleading?**
A. Cross-validation estimates generalization performance and reduces variance. It can be misleading when data is time-ordered, grouped by user, or when leakage exists. In those cases, use time-based or group-aware splits.

**Q4. Difference between bagging and boosting with effect on bias/variance.**
A. Bagging reduces variance by averaging independent models (Random Forest). Boosting reduces bias by sequentially focusing on errors (XGBoost, LightGBM). Boosting can overfit if not regularized.

**Q5. Explain feature engineering with examples for tabular and text data.**
A. Tabular: scaling, interaction terms, aggregation features, time-based features. Text: n-grams, TF-IDF, character features, embeddings. The goal is to encode useful signal while avoiding leakage.

**Q6. How do you handle imbalanced classes?**
A. Use class weights, resampling (over/under/SMOTE), threshold tuning, and metrics like PR-AUC or F1. Always compare to a simple baseline.

**Q7. What is data leakage and a common real example?**
A. Leakage happens when the model sees information it would not have at inference. Example: using future data to create features (like including a label-derived feature) or fitting scalers on all data instead of only the training set.

**Q8. What is a baseline model and why is it important?**
A. A baseline is a simple model or heuristic (majority class, linear model). It provides a minimum expected performance and helps justify complexity.

**Q9. Explain precision-recall tradeoff and threshold selection.**
A. Increasing the threshold reduces false positives but can reduce recall. Threshold selection should consider business cost or constraints and can be optimized using validation metrics.

**Q10. What is calibration?**
A. Calibration means predicted probabilities match observed frequencies. It is important when probabilities are used for decisions or risk scoring.

## 3) Deep Learning Basics (Targeted Q&A)

**Q1. Why use ReLU and what are its downsides?**
A. ReLU is simple and avoids vanishing gradients. Downside: dead neurons if large negative inputs dominate; variants like Leaky ReLU can help.

**Q2. What does batch normalization do?**
A. It normalizes activations to stabilize training, allow higher learning rates, and add slight regularization due to batch noise.

**Q3. What is dropout and why does it help?**
A. Dropout randomly zeros activations, which reduces co-adaptation and helps generalization, especially for dense layers.

**Q4. When do you use CNN vs RNN vs Transformer?**
A. CNN for spatial patterns (images); RNN for sequential dependencies when sequence length is moderate; Transformer for long-range dependencies and parallel training on large datasets.

**Q5. What is transfer learning and why is it useful for limited data?**
A. It leverages pretrained features from large datasets, allowing better generalization with less data and faster training.

## 4) MLOps and Deployment (Must-Know for This Role)

**Q1. What is MLOps and what are its core components?**
A. MLOps is the practice of managing the ML lifecycle: data versioning, experiment tracking, reproducible training, model registry, deployment, monitoring, and retraining. It aligns ML with DevOps principles.

**Q2. What is a model registry and why do teams use it?**
A. A model registry stores versions of models with metadata, metrics, and lineage. It enables controlled promotion to production and rollback when needed.

**Q3. What is data drift vs concept drift?**
A. Data drift is when input distributions change; concept drift is when the relationship between inputs and labels changes. Both can reduce performance and require monitoring and retraining.

**Q4. What do you monitor in production?**
A. Performance on labeled data (if available), input distributions, latency, error rates, and out-of-range features. Alerts should trigger investigation and possible retraining.

**Q5. Why use pipelines?**
A. Pipelines standardize training and deployment steps, enforce reproducibility, and reduce manual errors.

**Q6. Batch vs online inference: key tradeoffs?**
A. Batch is cost-effective for periodic predictions; online is needed for low-latency decisions but requires more infrastructure and monitoring.

## 5) Azure ML (Basic Expected Questions)

**Q1. What is Azure Machine Learning used for?**
A. It is a cloud platform to train, track, deploy, and manage models with integrated pipelines, registries, and endpoints.

**Q2. What is an Azure ML pipeline?**
A. A pipeline orchestrates data prep, training, evaluation, and deployment steps as a repeatable workflow.

**Q3. What is an endpoint?**
A. A deployed service that receives input and returns predictions, typically via a REST API.

## 6) Data Engineering + ETL (Nice-to-Have)

**Q1. What is ETL and where can errors occur?**
A. ETL is Extract, Transform, Load. Errors often occur in schema drift, missing fields, wrong data types, or silent parsing failures.

**Q2. Why do we validate data and what do we validate?**
A. Validation ensures data quality. We check schema, missingness, range constraints, unique keys, and distribution shifts.

## 7) Written Exam Style Questions (Short Answer + Sample Responses)

1. **Why can accuracy be misleading for imbalanced data?**
	- A model predicting only the majority class can achieve high accuracy but zero recall for the minority class. Use metrics like F1 or PR-AUC.
2. **Describe a feature selection technique and its benefit.**
	- Chi-square tests for association between categorical features and target, helping remove irrelevant features and reduce overfitting.
3. **Compare logistic regression and SVM.**
	- Logistic regression outputs calibrated probabilities and is interpretable; SVM can handle complex boundaries with kernels but is less interpretable.
4. **How do you choose a decision threshold?**
	- Use validation data to optimize a metric or cost function; consider business costs of false positives vs false negatives.
5. **Explain early stopping and when to use it.**
	- Stop training when validation performance stops improving; it reduces overfitting and saves compute.
6. **Macro vs micro F1: when to use each?**
	- Macro averages treat all classes equally; micro averages weight by frequency. Use macro for class balance, micro for overall accuracy.
7. **What is a confusion matrix used for?**
	- It shows counts of TP, FP, TN, FN to analyze error types and compute metrics.
8. **Handle missing values: one method and risk.**
	- Impute with median for numeric features; risk is bias if missingness is not random.
9. **Define train, validation, test split.**
	- Train for fitting, validation for tuning, test for final unbiased evaluation.
10. **What does the learning rate do?**
	- It controls step size during optimization; too high can diverge, too low slows learning.

## 8) High-Probability Topics Checklist

- Classification vs regression metrics and calibration
- Overfitting prevention and error analysis
- Feature engineering for text and tabular data
- Ensemble methods and tradeoffs
- MLOps basics: pipelines, monitoring, registry
- Cloud ML basics (Azure ML)
- Data drift and concept drift
- Time-based splits and leakage prevention

## 9) Quick Revision One-Liners

- Precision is about false positives; recall is about false negatives.
- L1 yields sparse weights; L2 yields small weights.
- Boosting reduces bias; bagging reduces variance.
- Leakage often comes from preprocessing done before splitting.

If you want, I can also generate a timed mock exam with answers and scoring, plus a personalized interview script and study plan.
