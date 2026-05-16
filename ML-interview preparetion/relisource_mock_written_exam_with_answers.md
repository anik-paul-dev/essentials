# ReliSource Junior ML Engineer - Timed Mock Written Exam

**Total time:** 90 minutes
**Total marks:** 100

## Instructions
- Attempt all sections.
- Show brief reasoning for short answers.
- Use clear steps for any calculations.

---

## Section A: Multiple Choice (10 x 2 = 20)

1) Which metric is most informative for rare positive classes?
   A) Accuracy  B) PR-AUC  C) MSE  D) R2

2) L1 regularization tends to:
   A) Increase variance  B) Produce sparse weights  C) Increase bias  D) Remove nonlinearity

3) Data leakage is most likely when:
   A) Using cross-validation  B) Scaling using the full dataset  C) Using a baseline model  D) Early stopping

4) Which split is correct for time series?
   A) Random shuffle split  B) Stratified split  C) Chronological split  D) K-fold shuffle

5) A model with high bias typically:
   A) Overfits  B) Underfits  C) Has low training error  D) Is too complex

6) Which is a boosting method?
   A) Random Forest  B) XGBoost  C) Bagging  D) KNN

7) A confusion matrix contains:
   A) TP, FP, TN, FN  B) AUC, F1, Precision  C) RMSE, MAE  D) Log loss only

8) Which is most suitable for image tasks?
   A) CNN  B) RNN  C) k-NN  D) Naive Bayes

9) Concept drift means:
   A) Input distribution changes  B) Relationship between features and target changes  C) Model size grows  D) Metrics do not exist

10) A model registry is used to:
   A) Collect raw data  B) Track and version models  C) Visualize data  D) Deploy web UI

---

## Section B: Short Answer (10 x 4 = 40)

1) Explain why accuracy can be misleading in imbalanced datasets. Provide a real example.
2) Define precision, recall, and F1. When is F1 preferred?
3) What is the difference between bagging and boosting? Mention effect on bias/variance.
4) What is data leakage and one concrete way it happens in preprocessing?
5) Explain standardization vs normalization and when you use each.
6) Describe a basic ML pipeline from raw data to deployment.
7) Explain data drift vs concept drift with a practical example.
8) What is cross-validation and when should you avoid random k-fold CV?
9) How do you select a decision threshold for a classifier?
10) Describe one feature engineering approach for text data and why it helps.

---

## Section C: Problem Solving (2 x 10 = 20)

1) You have the following confusion matrix values: TP=45, FP=15, TN=900, FN=40.
   - Compute precision, recall, and F1.
   - Interpret the result in one sentence.

2) A dataset has timestamps. The current pipeline performs scaling before splitting.
   - Explain what is wrong and how you will fix it.
   - Provide a correct split strategy for this dataset.

---

## Section D: Applied Case (1 x 20 = 20)

You are given a binary classification task for predicting customer churn. The dataset has 100,000 rows and 200 features. The churn rate is 5%.

Answer the following:
1) What baseline model would you start with and why?
2) Which metrics would you prioritize and why?
3) How would you handle class imbalance?
4) Outline an MLOps plan to monitor this model after deployment.

---

# Answer Key + Scoring Guide

## Section A Answers
1) B  2) B  3) B  4) C  5) B  6) B  7) A  8) A  9) B  10) B

## Section B Expected Answers (Key Points)

1) Accuracy ignores minority class; a 95% non-churn model can score 95% accuracy but has 0% recall for churn.
2) Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = harmonic mean. F1 preferred when balancing precision and recall in imbalanced data.
3) Bagging reduces variance via parallel models; boosting reduces bias via sequential error correction.
4) Leakage occurs when training uses info from test/future. Example: scaling on full data or using future labels in features.
5) Standardization: zero mean, unit variance for scale-sensitive models. Normalization: rescale to a range, useful for distance-based models.
6) Ingestion -> validation -> feature engineering -> training -> evaluation -> registry -> deployment -> monitoring -> retraining.
7) Data drift: input distributions change. Concept drift: relationship between features and target changes.
8) Cross-validation estimates generalization. Avoid random CV for time series or grouped data; use time-based or group splits.
9) Use validation to optimize F1 or cost; align with business costs of FP/FN.
10) TF-IDF or n-grams capture term importance; embeddings capture semantic similarity.

## Section C Suggested Answers

1) Precision = 45/(45+15) = 0.75
   Recall = 45/(45+40) = 0.5294
   F1 = 2*(0.75*0.5294)/(0.75+0.5294) = 0.62 (approx)
   Interpretation: high precision but moderate recall; model misses many positives.

2) Scaling before splitting leaks information. Fix by splitting first, then fitting scalers on training only. For time series, use chronological split and avoid shuffling.

## Section D Suggested Answers (Key Points)

1) Start with logistic regression or a simple tree as baseline for interpretability and speed.
2) Use PR-AUC, recall, F1, and confusion matrix due to 5% churn rate.
3) Use class weights, resampling, threshold tuning, or focal loss.
4) Track input drift, performance on labeled data, latency, error rates; set retraining triggers and rollback plan.

---

**Scoring:** Section A (20), Section B (40), Section C (20), Section D (20). A score above 75 is strong.
