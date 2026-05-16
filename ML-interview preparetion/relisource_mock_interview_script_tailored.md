# ReliSource Junior ML Engineer - Mock Interview Script (Tailored)

This is a full mock interview script based on your background in ML/DL research, Bangla NLP, and applied CV projects. Use it for practice. Replace bracketed parts with your own details.

---

## Interviewer: Tell me about yourself.

**Your answer (model response):**
I am an ML researcher and engineer with about two years of hands-on work in machine learning, deep learning, and AI. My recent focus has been low-resource language NLP, especially Bangla. I have worked on multi-class sentiment analysis, real-time vision systems, and privacy-preserving CV for assistive use cases. I enjoy taking projects from data exploration to model evaluation and I am now looking to apply that experience in a production-focused ML engineer role with strong MLOps practices.

---

## Interviewer: Walk me through your best ML project.

**Your answer (model response):**
I would use my Bangla sentiment analysis project. I started by defining the task and evaluation metric, then performed data cleaning and addressed class imbalance. I compared sparse features like TF-IDF and character n-grams with embeddings, and evaluated several classical models and ensembles. I used cross-validation and careful error analysis to identify confusion between similar sentiment classes. If I were deploying it, I would version data and models, set up a pipeline, and monitor for drift in vocabulary or label distributions.

---

## Interviewer: How would you deploy and monitor a model?

**Your answer (model response):**
I would package preprocessing and the model into a reproducible pipeline, register the model with metadata, and deploy it as a batch job or a REST endpoint depending on latency needs. I would monitor input distributions, prediction stability, latency, and error rates. If labels are available later, I would track performance on a rolling window and define retraining triggers for drift.

---

## Interviewer: How do you handle imbalanced datasets?

**Your answer (model response):**
I would start by choosing appropriate metrics such as PR-AUC or F1. I would explore class weights and resampling, and tune decision thresholds based on business costs. The goal is not just high accuracy but correct behavior on minority classes.

---

## Interviewer: What is data leakage? Give an example.

**Your answer (model response):**
Data leakage happens when training data contains information that would not be available at inference time. A common example is fitting a scaler or encoder on the full dataset before splitting. Another is using features derived from future outcomes in time-series tasks.

---

## Interviewer: Explain bias-variance tradeoff.

**Your answer (model response):**
Bias is error from simplifying assumptions; variance is error from sensitivity to training data. A simple model can underfit with high bias, while a very complex model can overfit with high variance. The solution is to balance complexity with regularization and validation.

---

## Interviewer: Describe your approach to feature engineering.

**Your answer (model response):**
I start by understanding the domain and the target. For text, I compare TF-IDF, character n-grams, and embeddings. For structured data, I add time-based features, ratios, or interactions. I validate improvements with controlled experiments to ensure the features generalize.

---

## Interviewer: How do you communicate results to non-technical stakeholders?

**Your answer (model response):**
I focus on the business impact and use clear metrics, visuals, and examples. I translate model performance into expected outcomes, such as reduced false positives or improved coverage.

---

## Interviewer: What would you do in your first 90 days?

**Your answer (model response):**
I would understand the current data pipelines and model stack, establish baselines, and identify quick wins. Then I would help improve reproducibility and monitoring while collaborating with the team on a measurable model improvement.

---

## Interviewer: Why ReliSource?

**Your answer (model response):**
I want to work in a team that builds real-world ML solutions and values production readiness. The role emphasizes MLOps and collaboration, which aligns with how I want to grow as an ML engineer.

---

## Follow-up Drills (Practice Variants)

1) Explain a time you failed in a project and what you learned.
2) Compare two models and justify a choice with metrics.
3) How would you reduce model latency for a production service?
4) How would you detect concept drift?

---

## Quick Personalization Checklist

- Mention Bangla NLP and low-resource data challenges.
- Mention cross-validation and error analysis.
- Mention MLOps basics: versioning, pipelines, monitoring.
- Mention team collaboration and communication with clients.

