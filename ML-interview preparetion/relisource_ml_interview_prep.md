# ReliSource ML Engineer - Interview Prep (Junior + Lead Coverage, Expanded)

This guide reflects the role details you shared and typical ML engineer interview formats. It avoids any unverified company-specific claims.

## 1) Core Interview Questions (Full-Length Answers)

**Q1. Walk me through an ML project end-to-end.**
A. I start by framing the business problem and agreeing on a metric. Then I profile the data, check quality issues, and design a baseline model. I iterate on feature engineering and model selection with proper cross-validation, keeping track of experiments. I do error analysis to understand failure modes. For deployment, I package the model with input validation, version the model and data, and set up monitoring for drift and performance decay. Retraining is triggered by metric thresholds or data shift.

**Q2. How do you evaluate a classifier on imbalanced data?**
A. Accuracy is often misleading, so I focus on precision, recall, F1, and PR-AUC. I analyze the confusion matrix to understand error types. I might use class weights, resampling, or threshold tuning based on business costs. If the positive class is rare, I prioritize recall or PR-AUC depending on the objective.

**Q3. What is data leakage and how do you avoid it?**
A. Leakage happens when the model sees information at training time that will not exist at inference. I prevent it by splitting data early, fitting scalers or encoders only on the training set, and using time-based splits when data is sequential. I also check feature definitions to ensure they do not use future outcomes.

**Q4. How do you choose between models?**
A. I start with a baseline and then compare models using the correct metric and a consistent validation strategy. I consider interpretability, latency, memory, data size, and robustness. If the performance gain is small, I choose the simpler model to reduce operational risk.

**Q5. Explain bias-variance tradeoff with an example.**
A. A simple linear model can underfit a non-linear dataset, producing high bias. A deep model may overfit the training data, producing high variance. I balance this by selecting the right complexity, regularization, and by validating on unseen data.

**Q6. How do you handle missing data?**
A. I analyze the missingness pattern and decide whether it is MCAR, MAR, or MNAR. I then choose imputation (median, mode, model-based) or removal if the fraction is small and random. I evaluate whether imputation introduces bias and document the decision.

**Q7. What MLOps practices would you implement as a junior engineer?**
A. I would start with versioning data and models, simple experiment tracking, and building reproducible training pipelines. I would set up a basic model registry and add monitoring for drift and performance. As the system matures, I would introduce CI/CD for training and deployment.

**Q8. How do you monitor models in production?**
A. I monitor input distributions, latency, error rates, and output stability. When labels are available, I track performance on a rolling window. I set thresholds for drift and performance decay and define retraining triggers or rollback rules.

**Q9. Explain feature engineering for text data.**
A. I start with tokenization and normalization. I compare sparse features like n-grams and TF-IDF with embeddings. I evaluate which representation works best for the dataset size and task. For low-resource languages, I often test character-level features and subword models.

**Q10. Tell me about a time you improved model performance.**
A. I would describe a specific improvement, such as better features, hyperparameter tuning, or a model switch, and quantify the change. I would also mention how I validated the improvement and ensured it generalized.

## 2) System Design / ML Architecture Questions

**Q1. Design a pipeline for training and deploying a model.**
A. Ingestion -> validation -> feature engineering -> training -> evaluation -> model registry -> deployment -> monitoring -> retraining triggers. I would keep data and model versions linked for traceability.

**Q2. Batch vs real-time inference: when and why?**
A. Batch is ideal for periodic scoring and cost savings. Real-time is required when decisions need low latency. The choice depends on SLA, data freshness, and infrastructure cost.

**Q3. How would you make a model scalable?**
A. Use efficient architectures, optimize preprocessing, batch inputs, use caching, and scale horizontally for inference. I also consider distillation or pruning if needed.

## 3) Questions Tailored to Your Background (Suggested Answers)

**Q1. Tell me about your research on low-resource Bangla NLP.**
A. Emphasize the challenge of data scarcity and morphology, the features and models you tried, and how you evaluated improvements. Highlight how the approach generalizes to other low-resource languages.

**Q2. How do you balance research creativity with production constraints?**
A. Explain that you explore advanced models in research but choose the simplest model that meets requirements for deployment due to latency, maintenance, and reliability concerns.

**Q3. What is your most relevant project to this role?**
A. Pick one project and present it as an ML pipeline: data, modeling, evaluation, and what you would do for productionization.

## 4) Behavioral + Communication

**Q1. Describe a challenge you faced in an ML project.**
A. Use STAR: Situation, Task, Action, Result. Include measurable results and what you learned.

**Q2. How do you communicate results to non-technical stakeholders?**
A. Use simple visuals, a clear metric, and link improvements to business outcomes. Avoid jargon and emphasize tradeoffs.

**Q3. How do you handle feedback or disagreement about model choices?**
A. I compare alternatives with data and metrics, explain tradeoffs, and align with project constraints.

## 5) Junior vs Lead Expectations (How to Answer)

- Junior focus: correct fundamentals, clear reasoning, eagerness to learn, ability to ship a clean baseline and iterate.
- Lead focus: system design, risk management, monitoring strategy, mentoring, and delivery ownership.

## 6) Questions You Can Ask Them

- What types of ML problems does the team solve most often?
- What is the current MLOps stack and release process?
- How is success measured for this role in the first 3-6 months?

---
If you want, I can provide a full mock interview script tailored to your experience with model answers.
