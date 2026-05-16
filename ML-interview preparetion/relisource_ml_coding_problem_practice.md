# ML Engineer Coding + Problem Solving Prep (Expanded, Role-Aligned)

This file lists likely coding tasks for a junior ML engineer role. It includes the expected approach, what interviewers evaluate, and practice prompts you can rehearse.

## 1) Most Likely Coding Tasks (Practical)

1) **Data cleaning and preprocessing**
   - Task: handle missing values, encode categories, scale numeric features.
   - What they evaluate: correct preprocessing order, train/test split discipline, no leakage, readable code.
   - Expected approach: split first, fit preprocessors on training only, apply to validation/test.

2) **Implement a simple model pipeline**
   - Task: load data, train a classifier/regressor, evaluate metrics.
   - What they evaluate: correct metric choice, clean pipeline, reproducibility.
   - Expected approach: baseline model, then one improved model, report metrics and errors.

3) **Feature engineering**
   - Task: create new features from time columns or text.
   - What they evaluate: justification of features and how they help prediction.
   - Expected approach: create features that capture seasonality, trends, or domain signals.

4) **Basic ML from scratch (possible)**
   - Task: implement linear regression or k-means in Python.
   - What they evaluate: correct math, clear steps, stopping conditions.
   - Expected approach: simple loops, gradient descent, convergence criteria.

5) **Evaluation metrics coding**
   - Task: compute precision, recall, F1, confusion matrix.
   - What they evaluate: correctness and edge-case handling.
   - Expected approach: count TP/FP/TN/FN and compute metrics carefully.

6) **Data leakage diagnosis**
   - Task: given a pipeline or feature list, identify leakage.
   - What they evaluate: ability to reason about training vs inference data.

## 2) Short Problem-Solving Questions (Likely)

1) Given predictions and labels, compute precision/recall/F1.
2) Explain why accuracy is misleading in an imbalanced dataset.
3) Compare two models using ROC-AUC vs F1; decide which to deploy.
4) When does cross-validation fail or give misleading results?
5) Show how you prevent leakage when doing target encoding.
6) Explain the effect of class weighting on decision boundary.

## 3) Light Algorithmic Practice (No Hard LeetCode)

Focus on problems that align with ML work:
- Sorting and grouping, frequency counts
- Sliding window for time-series features
- Hash maps for category lookup
- Basic dynamic programming as a bonus
- String processing for tokenization or n-grams

## 4) Mock Coding Prompts (Ready to Practice)

**Prompt A: Data cleaning**
- Input: a CSV with missing values and categorical columns
- Output: clean dataset with imputed values and encoded categories
- Expected: train/test split, fit preprocessors on train only, avoid leakage

**Prompt B: Metrics by hand**
- Input: y_true and y_pred arrays
- Output: precision, recall, F1, confusion matrix
- Expected: correct TP/FP/TN/FN counts

**Prompt C: Simple regression from scratch**
- Implement linear regression using gradient descent
- Show loss decreasing and explain learning rate choice

**Prompt D: Feature engineering**
- From a datetime column, create day-of-week and hour-of-day features
- Explain why these features help in forecasting

**Prompt E: Data split for time series**
- Given a dataset with timestamps, show a correct train/validation/test split
- Explain why random shuffle is incorrect

**Prompt F: Simple text feature pipeline**
- Convert a list of sentences into TF-IDF vectors
- Train a simple classifier and report F1

## 5) What To Say If Stuck

- Clarify assumptions and constraints
- Start with a simple baseline and iterate
- Explain tradeoffs and what you would improve with more time

## 6) Scoring Rubric (Typical)

- Correctness: 40%
- Clean structure and readability: 20%
- Proper evaluation and metrics: 20%
- Reasoning and tradeoffs: 20%

---
If you want, I can create timed coding drills with solutions and a scoring rubric.
