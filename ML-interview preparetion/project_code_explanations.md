# Project Code Explanations (Line-by-Line, High-Level)

This document explains what each project script does by walking through the code structure and key blocks in order. It is intended for interview preparation.

---

## 1) chair_detect_best_privacy.py

**Cell 1 (install and setup)**
- Installs required libraries for detection, speech, audio, and depth estimation (YOLO, MediaPipe, PyTorch, MiDaS, gTTS, pyaudio, etc.).
- Ensures compatible OpenCV and MediaPipe versions for Colab runtime.

**Cell 2 (imports and mounting drive)**
- Imports vision, ML, audio, and web utilities.
- Mounts Google Drive to load or store assets.

**Cell 3 (model initialization)**
- Loads YOLOv8 segmentation for chair/person detection.
- Loads MiDaS depth estimation model for distance measurement.
- Initializes MediaPipe pose and face detection.
- Sets up a text-generation pipeline for guidance text.
- Defines global variables for timing and audio guidance cooldowns.

**Cell 4 (utility functions)**
- `calculate_iou`: computes box overlap (intersection-over-union) for chairs and persons.
- `apply_mask`: crops chair region and applies the segmentation mask to focus on chair pixels.

**Cell 5 (chair occupancy logic)**
- Detects chairs and persons from YOLO output, filters by confidence.
- Determines if a chair is occupied primarily via bounding box overlap.
- Uses pose detection as a secondary confirmation based on hip landmarks.
- Returns occupied and empty chair counts.

**Cell 6 (distance estimation)**
- Runs MiDaS on frames to get depth maps.
- Calibrates depth values and estimates chair distance based on masked regions.

**Cell 7 (tracking)**
- Defines a `ChairTracker` with Kalman filters to keep consistent IDs across frames.
- Matches detections to existing tracks by center distance.

**Cell 8 (locking and guidance)**
- Defines speech function and lock state for “best chair”.
- Implements re-anchoring logic when the camera moves.
- Prepares user confirmation logic and navigation flow.

**Overall purpose**
- A full assistive system: detect chairs, decide occupancy, estimate distance, track across frames, and provide guidance through audio for blind users.

---

## 2) efficientnet_b1_b4.py

**Cell 1 (install dependencies)**
- Installs PyTorch, OpenCV, scikit-learn, and visualization libraries.

**Cell 2 (imports + drive)**
- Imports PyTorch, torchvision, metrics, and plotting utilities.
- Mounts Google Drive for dataset access.

**Cell 3 (paths and transforms)**
- Defines dataset path.
- Builds training and testing transforms with augmentation (rotation, flip, color jitter, erase).

**Cell 4 (datasets and loaders)**
- Loads train/val/test datasets using `ImageFolder`.
- Builds DataLoaders and identifies class labels.

**Cell 5 (model definitions)**
- Selects EfficientNet variant (b0–b4).
- Defines two models: one with spatial attention and one without.
- Replaces classifier layers and enables partial fine-tuning.

**Cell 6 (loss, optimizers, schedulers)**
- Cross-entropy loss for classification.
- Adam optimizers with weight decay.
- ReduceLROnPlateau schedulers for learning rate control.

**Cell 7 (training loop)**
- Trains and validates per epoch.
- Tracks loss and accuracy.
- Saves best-performing model checkpoint.

**Cell 8 (training and plotting)**
- Trains both attention and no-attention models.
- Plots training/validation curves.

**Cell 9 (test evaluation)**
- Loads saved models and evaluates on test set.
- Prints classification reports.

**Cell 10 (confusion matrices)**
- Sets Bengali fonts for plotting.
- Plots confusion matrices for both models.

**Cell 11–12 (Grad-CAM explainability)**
- Implements Grad-CAM to visualize model attention.
- Generates a grid of heatmaps for interpretability.

**Overall purpose**
- A full sign-language recognition pipeline with EfficientNet variants, optional attention, and explainability visualizations.

---

## 3) Multi-class-sentiment-Analysis.py

**Setup and imports**
- Installs and pins versions of NLP and ML libraries.
- Imports pandas, scikit-learn, bnltk, xgboost, lightgbm, and visualization tools.

**Data loading and cleaning**
- Loads Bangla dataset from Google Drive.
- Renames columns and checks schema.
- Removes missing values and duplicates.

**EDA and distribution analysis**
- Computes sentiment distribution, text length histograms, and co-occurrence statistics.
- Builds co-occurrence matrices and heatmaps.

**Advanced overlap and dependency analysis**
- Computes Jaccard overlap, chi-square tests, and correlation matrices for multi-label overlap.
- Visualizes pair dependencies and overlap density.

**Lexicon analysis**
- Defines sentiment lexicon for Bangla.
- Tokenizes text and matches lexicon words.
- Analyzes lexicon word overlap across sentiments.

**Text preprocessing**
- Normalizes text, removes URLs/special tokens, applies stemming.
- Prepares text for feature extraction.

**Feature extraction and modeling (later in file)**
- Uses sparse features like BoW/TF-IDF and statistical selectors.
- Trains classical ML models for multi-label sentiment.
- Evaluates with accuracy, F1, and other metrics.

**Overall purpose**
- A full multi-label Bangla sentiment analysis pipeline with deep EDA, feature exploration, and classical ML modeling.

---

## 4) spam_detection_final.py

**Data loading**
- Loads spam dataset from Google Drive and checks shape.

**Cleaning and labeling**
- Drops unnecessary columns and renames fields.
- Encodes labels (ham/spam) into numeric values.
- Removes duplicates.

**EDA**
- Summarizes class distribution and text statistics.
- Visualizes character/word/sentence counts by class.

**Text preprocessing**
- Lowercasing, tokenization, stopword removal, punctuation removal, and stemming.
- Produces a cleaned text field.

**Vectorization**
- Builds TF-IDF features.

**Modeling**
- Trains Naive Bayes variants (Gaussian, Multinomial, Bernoulli).
- Evaluates accuracy and precision, and plots confusion matrix.
- Builds ROC-AUC comparison plot.

**Inference demo**
- Accepts an input message and predicts spam or ham.

**Overall purpose**
- A complete spam classification pipeline from preprocessing to evaluation with classical ML baselines.
