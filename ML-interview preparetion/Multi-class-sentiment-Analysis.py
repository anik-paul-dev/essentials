
# Uninstall conflicting libraries
!pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python thinc umap-learn
# Install required libraries with specific versions (Fixed: gensim==4.4.0 for scipy compat; no scipy pin)
!pip install numpy==2.0.2 pandas==2.2.2 scikit-learn==1.5.2 matplotlib==3.9.2 seaborn==0.13.2 \
  imbalanced-learn==0.12.3 joblib==1.4.2 nltk==3.9.1 bnltk==0.7.8 xgboost==2.1.1 lightgbm==4.5.0 \
  sentencepiece==0.2.0 opencv-python-headless gensim==4.4.0
# Restart runtime
# import os
# os._exit(0)


!pip list | grep -E 'numpy|scikit-learn|bnltk|gensim'

# Import libraries after restart
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV, learning_curve
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, hamming_loss, jaccard_score, roc_curve, auc
import xgboost as xgb
import lightgbm as lgb
import bnltk as bn
from bnltk.stemmer import BanglaStemmer
import sentencepiece as spm
import re
import joblib
import warnings
warnings.filterwarnings('ignore')


# Download NLTK data
import nltk
nltk.download('punkt_tab')


from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/Sentiment Thesis New/Bangla Multiclass-23-25 - Sheet7.csv', encoding='utf-8')

# Rename 'Paragraph' to 'Text' for consistency
df = df.rename(columns={'Paragraph': 'Text'})

# Verify dataset structure
print("Dataset Preview:\n", df.head())
print("\nDataset Info:\n")
df.info()

# Check for missing values and duplicates
print("\nMissing Values:\n", df.isnull().sum())
sentiment_cols = ['Happy', 'Sad', 'Angry', 'Fear', 'Surprise']
df = df.dropna(subset=['Text'] + sentiment_cols)
df = df.drop_duplicates()
print("Dataset Shape after Cleaning:", df.shape)

# Ensure correct columns
expected_cols = ['Text'] + sentiment_cols
if not all(col in df.columns for col in expected_cols):
    raise ValueError(f"CSV must contain columns: {expected_cols}")

# 2. Exploratory Data Analysis (EDA)
print("\nSentiment Distribution:")
for col in sentiment_cols:
    print(f"{col}: {df[col].sum()} texts (Positive: {df[col].mean()*100:.2f}%)")

plt.figure(figsize=(8, 6))
df[sentiment_cols].sum().plot(kind='bar')
plt.title('Sentiment Distribution')
plt.xlabel('Sentiment')
plt.ylabel('Count')
plt.show()

df['text_length'] = df['Text'].apply(lambda x: len(re.findall(r'[\u0980-\u09FF]+', x)))
plt.figure(figsize=(10, 6))
sns.histplot(df['text_length'], bins=30)
plt.title('Text Length Distribution (Bangla Words)')
plt.xlabel('Word Count')
plt.ylabel('Frequency')
plt.show()

df['num_sentiments'] = df[sentiment_cols].sum(axis=1)
print("\nNumber of Sentiments per Text:")
print(df['num_sentiments'].value_counts().sort_index())
plt.figure(figsize=(8, 5))
sns.countplot(x='num_sentiments', data=df)
plt.title('Distribution of Sentiment Counts per Text')
plt.xlabel('Number of Sentiments')
plt.ylabel('Frequency')
plt.show()

# Sentiment Co-occurrence Probabilities for Ratio Analysis
co_occ = pd.DataFrame(index=sentiment_cols, columns=sentiment_cols, dtype=float)
for row in sentiment_cols:
    total = df[row].sum()
    for col in sentiment_cols:
        if row == col:
            co_occ.loc[row, col] = 1.0
        else:
            co_occ.loc[row, col] = df[(df[row] == 1) & (df[col] == 1)].shape[0] / total if total > 0 else 0
print("\nSentiment Co-occurrence Probabilities (P(col|row)):")
print(co_occ)

plt.figure(figsize=(8, 6))
sns.heatmap(co_occ, annot=True, cmap='Blues', fmt='.2f')
plt.title('Sentiment Co-occurrence Probabilities')
plt.show()


#############################

# Ensure num_sentiments
df['num_sentiments'] = df[sentiment_cols].sum(axis=1)

# 1. Global Co-Ratio Summary (All Pairs: Mean, Jaccard for Symmetric Overlap): Index for Min
off_diagonal = co_occ.values[np.triu_indices_from(co_occ.values, k=1)]
mean_overlap = np.mean(off_diagonal)
max_pair_idx = np.argmax(off_diagonal)
max_i, max_j = np.triu_indices_from(co_occ.values, k=1)[0][max_pair_idx], np.triu_indices_from(co_occ.values, k=1)[1][max_pair_idx]  # FIXED indices
max_pair = f"{sentiment_cols[max_i]}-{sentiment_cols[max_j]}"
min_non_diag = np.min(co_occ.values[co_occ.values < 1.0])  # Non-diagonal min

# Optional Jaccard (symmetric; comment out if not needed)
jaccard_matrix = pd.DataFrame(index=sentiment_cols, columns=sentiment_cols)
for i, s1 in enumerate(sentiment_cols):
    for j, s2 in enumerate(sentiment_cols):
        if i == j:
            jaccard_matrix.iloc[i, j] = 1.0
        else:
            jaccard_matrix.iloc[i, j] = jaccard_score(df[s1], df[s2], zero_division=0)
jaccard_matrix = jaccard_matrix.astype(float)  # Ensure numeric

print("\n=== GLOBAL CO-OCCURRENCE INSIGHTS (All Pairs) ===")
print(f"Average Overlap Probability: {mean_overlap:.3f} (widespread; >0.3 in 8/10 pairs)")
print(f"Strongest Pair: {max_pair} ({co_occ.iloc[max_i, max_j]:.3f})")
print(f"Weakest Overlap: {min_non_diag:.3f} (still bleeds)")
print("\nJaccard Overlap Ratios (Symmetric: Intersection/Union %):")
print(jaccard_matrix.round(3).to_string())

# Jaccard Heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(jaccard_matrix, annot=True, cmap='Reds', fmt='.3f', square=True)
plt.title('Symmetric Overlap Ratios (Jaccard) - All Pairs')
plt.show()

# Overlap Spectrum (Sorted Bar) - Proper DataFrame
pair_probs = []
for i, s1 in enumerate(sentiment_cols):
    for j in range(i+1, len(sentiment_cols)):
        pair_probs.append((f"{s1}-{sentiment_cols[j]}", co_occ.iloc[i, j]))
pair_df = pd.DataFrame(pair_probs, columns=['Pair', 'Prob']).sort_values('Prob')  # FIXED columns
plt.figure(figsize=(10, 5))
sns.barplot(data=pair_df, y='Pair', x='Prob', palette='viridis')
plt.title('Co-occurrence Spectrum: Weakest to Strongest Pairs')
plt.xlabel('Probability')
plt.show()


# 4. Pairwise Dependencies (Corr/Chi2) - All Pairs - Matches Your Original
corr_matrix = df[sentiment_cols].corr().round(2)
chi_results = {}
for i, s1 in enumerate(sentiment_cols):
    for j in range(i+1, len(sentiment_cols)):
        s2 = sentiment_cols[j]
        cont = pd.crosstab(df[s1], df[s2])
        chi2_stat, p_val, _, _ = chi2_contingency(cont)
        chi_results[f"{s1}-{s2}"] = {'Chi2': round(chi2_stat, 3), 'p-value': round(p_val, 3)}  # FIXED: 'p-value'
chi_df = pd.DataFrame(chi_results).T

print("\n=== DEPENDENCIES (Corr Matrix & Sig Chi2, p<0.05) ===")
print("Correlations:")
print(corr_matrix.to_string())
print("\nChi2 Tests (All Pairs):")
print(chi_df.to_string())

sig_chi = chi_df[chi_df['p-value'] < 0.05].sort_values('Chi2', ascending=False)
if not sig_chi.empty:
    plt.figure(figsize=(8, 5))
    sig_chi['Chi2'].plot(kind='bar')
    plt.title('Significant Overlap Dependencies (Chi2, p<0.05)')
    plt.xticks(rotation=45)
    plt.ylabel('Chi2')
    plt.show()

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title('Sentiment Correlations (Negative = Anti-Overlap)')
plt.show()

print("\n=== EDA COMPLETE: Focus on Co-occurrence Ratios Done ===")


# Global Overlap Summary (for "more or less everywhere")
off_diagonal = co_occ.values[np.triu_indices_from(co_occ.values, k=1)]
mean_overlap = off_diagonal.mean()
max_overlap_pair = co_occ.stack().idxmax()
print(f"\nGlobal Overlap Insights:")
print(f"- Average Co-occurrence Across All Pairs: {mean_overlap:.3f} (widespread blending)")
print(f"- Strongest Pair: {max_overlap_pair[0]}-{max_overlap_pair[1]} ({co_occ.loc[max_overlap_pair]:.3f})")
print(f"- Weakest Non-Diagonal: {co_occ.values[np.tril_indices_from(co_occ.values, k=-1)].min():.3f} (still some bleed)")

# Overlap Spectrum Bar
pair_probs = co_occ.stack().reset_index(name='prob')
pair_probs['pair'] = pair_probs['level_0'] + '-' + pair_probs['level_1']
pair_probs = pair_probs[pair_probs['level_0'] != pair_probs['level_1']].sort_values('prob', ascending=True)
pair_probs.plot(x='pair', y='prob', kind='barh', figsize=(8,6), color='salmon')
plt.title('Overlap Spectrum: From Weakest to Strongest Pairs')
plt.xlabel('Co-occurrence Probability')
plt.tight_layout()
plt.show()
plt.close()


# 4. Co-occurrence Network
G = nx.Graph()
G.add_nodes_from(sentiment_cols)
for i, s1 in enumerate(sentiment_cols):
    for j, s2 in enumerate(sentiment_cols):
        if i < j and co_occ.loc[s1, s2] > 0.3:
            G.add_edge(s1, s2, weight=co_occ.loc[s1, s2])

plt.figure(figsize=(8, 6))
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray',
        width=[G[u][v]['weight']*5 for u,v in G.edges()], node_size=2000)
plt.title('Sentiment Co-occurrence Network (Edge Width = Prob)')
plt.show()
plt.close()


# 8. Outlier Detection: Raw Counts, Overlap Check, Readable Tables
from scipy import stats
import numpy as np

df['word_count'] = df['Text'].apply(lambda x: len(re.findall(r'[\u0980-\u09FF]+', x)))  # Raw Bangla words

z_scores = np.abs(stats.zscore(df['word_count']))
outliers = df[z_scores > 3]

print(f"\nOutlier Texts (Z>3, {len(outliers)/len(df)*100:.1f}% of data, n={len(outliers)}):")
outlier_table = outliers[['word_count'] + sentiment_cols + ['num_sentiments']].head()  # Add num_sentiments
print(outlier_table.round(2).to_string(index=False))  # Readable table

# Check avg overlaps in outliers vs full
outlier_overlaps = outliers[sentiment_cols].sum(axis=1).mean()
full_overlaps = df['num_sentiments'].mean()
print(f"\nAvg Sentiments in Outliers: {outlier_overlaps:.2f} (vs full {full_overlaps:.2f}; higher = co-occ bias)")

rare_profiles = df[df['num_sentiments'].isin([1,5])].groupby('num_sentiments').agg({
    'Text': 'count',
    **{s: 'mean' for s in sentiment_cols},
    'num_sentiments': 'mean'  # Include for profile view
})
print("\nRare Sentiment Profiles (1 or 5 sents):")
print(rare_profiles.round(2).to_string())  # Readable

plt.figure(figsize=(10, 6))
df.boxplot(column='word_count', by='num_sentiments', ax=plt.gca())
plt.title('Text Length Outliers by Sentiment Count')
plt.suptitle('')  # No sub
plt.xlabel('Num Sentiments')
plt.ylabel('Word Count')
plt.show()
plt.close()


# Sentiment Lexicon for Bangla Multi-Sentiment Analysis
sentiment_lexicon = {
    'Happy': ['আনন্দ', 'সুখ', 'খুশি', 'হাসি', 'উল্লাস', 'ভালো', 'সুন্দর', 'খুশি হওয়া', 'আনন্দ করা', 'উত্ফুল্ল', 'সন্তুষ্ট', 'হর্ষ', 'মজা', 'উল্লাসিত', 'প্রফুল্ল', 'প্রসন্ন', 'আহ্লাদ', 'আমোদ', 'রোমাঞ্চ', 'তৃপ্তি', 'সানন্দ', 'পুলকিত', 'মুগ্ধ', 'আনন্দিত', 'সুখী', 'প্রীত', 'প্রমোদ', 'হাস্যোজ্জ্বল', 'আহ্লাদিত', 'উদ্বেল'],
    'Sad': ['দুঃখ', 'কষ্ট', 'বিষণ্ন', 'কান্না', 'হতাশা', 'খারাপ', 'নিরাশ', 'দুঃখিত হওয়া', 'কষ্ট পাওয়া', 'বিষাদ', 'কাতর', 'শোক', 'দুর্ভাগ্য', 'দুঃখিত', 'অনুতাপ', 'বেদনা', 'যন্ত্রণা', 'অশ্রু', 'হাহাকার', 'ক্লান্ত', 'উদাস', 'অবসাদ', 'মলিন', 'অনুতপ্ত', 'দীন', 'করুণ', 'দয়নীয়', 'অসুখী', 'ব্যথিত', 'শোকার্ত'],
    'Angry': ['রাগ', 'ক্রোধ', 'গোস্যা', 'ক্ষোভ', 'বিরক্ত', 'ক্রুদ্ধ', 'রাগান্বিত', 'উত্তেজিত', 'গর্জন', 'কোপ', 'আক্রোশ', 'উষ্মা', 'তেজ', 'ফুটন্ত', 'ঘৃণা', 'অসন্তোষ', 'প্রতিবাদ', 'অপমান', 'দ্বেষ', 'বিদ্বেষ', 'অসন্তুষ্ট', 'ক্ষিপ্ত', 'উন্মাদ', 'তীব্র', 'আক্রমণ', 'যুদ্ধ', 'হিংসা', 'অপছন্দ', 'অসহ্য', 'ঘেন্না'],
    'Fear': ['ভয়', 'আতঙ্ক', 'ডর', 'ত্রাস', 'উদ্বেগ', 'ভীত', 'আতঙ্কিত', 'ত্রস্ত', 'ডরপোক', 'ভয়ার্ত', 'সন্ত্রস্ত', 'উদ্বিগ্ন', 'আশঙ্কা', 'সংশয়', 'ভীতি', 'কম্পন', 'থরথর', 'আত্মরক্ষা', 'পলায়ন', 'অনিশ্চয়তা', 'ঝুঁকি', 'বিপদ', 'সতর্ক', 'আশঙ্কিত', 'অস্থির', 'কাঁপুনি', 'আতঙ্কগ্রস্ত', 'ভয়ংকর', 'অজানা', 'অন্ধকার'],
    'Surprise': ['আশ্চর্য', 'বিস্ময়', 'অবাক', 'চমক', 'আশ্চর্যজনক', 'হতবাক', 'অভিভূত', 'বিস্মিত', 'চমকিত', 'অপ্রত্যাশিত', 'আকস্মিক', 'অভাবিত', 'অদ্ভুত', 'অপূর্ব', 'অচিন্তনীয়', 'অবিশ্বাস্য', 'আশ্চর্যকর', 'চমৎকার', 'অদৃষ্টপূর্ব', 'অভূতপূর্ব', 'অপ্রত্যাশিত', 'অকল্পনীয়', 'আকস্মিকতা', 'বিস্ময়কর', 'হকচক', 'অবাক করা', 'চমকে ওঠা', 'আশ্চর্য হয়ে যাওয়া', 'অবিশ্বাস', 'অভাবনীয়']
}

# Function to tokenize raw Bangla text (simple split, no stemming for lexicon matching)
def tokenize_bangla_text(text):
    text = str(text)
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\.\.\.+', '', text)
    text = re.sub(r'[^\u0980-\u09FF\s]', '', text)
    words = text.split()
    return [w.strip() for w in words if len(w.strip()) > 1]

# Add tokenized raw text to df (for lexicon matching)
df['raw_tokens'] = df['Text'].apply(tokenize_bangla_text)

# Flatten lexicon to a dict for quick lookup (word to list of sentiments it triggers)
lexicon_flat = {}
for sent, words in sentiment_lexicon.items():
    for word in words:
        if word in lexicon_flat:
            lexicon_flat[word].append(sent)
        else:
            lexicon_flat[word] = [sent]

# Remove duplicates in triggered sentiments for each word
for word in lexicon_flat:
    lexicon_flat[word] = list(set(lexicon_flat[word]))

# Find unique lexicon words in dataset
all_lexicon_words_in_data = set()
for tokens in df['raw_tokens']:
    for word in tokens:
        if word in lexicon_flat:
            all_lexicon_words_in_data.add(word)

print(f"Lexicon Words Found in Dataset: {len(all_lexicon_words_in_data)} out of {len(lexicon_flat)}")

# Analyze overlaps: Words that trigger multiple sentiments (by lexicon definition)
multi_sentiment_words = {word: sents for word, sents in lexicon_flat.items() if len(sents) > 1}
print(f"\nLexicon Words Triggering Multiple Sentiments: {len(multi_sentiment_words)}")
if multi_sentiment_words:
    multi_df = pd.DataFrame([{'Word': word, 'Triggered Sentiments': ', '.join(sents), 'Count': len(sents)} for word, sents in multi_sentiment_words.items()])
    print(multi_df.to_string(index=False))
else:
    print("No words in lexicon defined to trigger multiple sentiments.")

# Dataset-level overlaps: Count how often each lexicon word co-occurs with each sentiment label
word_sentiment_cooc = {word: {sent: 0 for sent in sentiment_cols} for word in all_lexicon_words_in_data}

for idx, row in df.iterrows():
    text_words = set(row['raw_tokens'])
    for word in text_words:
        if word in word_sentiment_cooc:
            for sent in sentiment_cols:
                if row[sent] == 1:
                    word_sentiment_cooc[word][sent] += 1

# Top overlapping words across sentiments (by total co-occurrence count)
all_cooc = []
for word, sent_counts in word_sentiment_cooc.items():
    total = sum(sent_counts.values())
    if total > 0:
        all_cooc.append((word, sent_counts, total))

# Sort by total co-occurrence
all_cooc.sort(key=lambda x: x[2], reverse=True)

print(f"\nLexicon Word Co-occurrence with Sentiments (Top 20 by Total Count):")
print("Word: Sent1=count1, Sent2=count2, ... | Total")
print("-" * 60)
for word, sent_counts, total in all_cooc[:20]:
    cooc_str = ', '.join([f"{sent}={sent_counts[sent]}" for sent in sentiment_cols])
    print(f"{word}: {cooc_str} | {total}")

# Per-pair overlaps: Lexicon words associated with sent1 or sent2 that appear in their co-labeled texts
pair_data = []
for i, sent1 in enumerate(sentiment_cols):
    for sent2 in sentiment_cols[i+1:]:
        mask = (df[sent1] == 1) & (df[sent2] == 1)
        pair_count = len(df[mask])
        pair_words = set()
        pair_counts = Counter()
        for idx in df[mask].index:
            text_words = set(df.loc[idx, 'raw_tokens'])
            for word in text_words:
                if word in lexicon_flat and (sent1 in lexicon_flat[word] or sent2 in lexicon_flat[word]):
                    pair_words.add(word)
                    pair_counts[word] += 1
        overlap_score = len(pair_words) / pair_count if pair_count > 0 else 0  # Density: unique words per pair text
        top_pair = [word for word, cnt in pair_counts.most_common(5)]
        pair_data.append({
            'Pair': f"{sent1}-{sent2}",
            'Co-labeled Texts': pair_count,
            'Unique Associated Words': len(pair_words),
            'Overlap Density': f"{overlap_score:.3f}",
            'Top Words': ', '.join(top_pair)
        })

pair_df = pd.DataFrame(pair_data)
print("\nLexicon Words Associated with Sentiment Pairs:")
print(pair_df.to_string(index=False, max_colwidth=25))

# Summary table for pair overlaps (sorted by density)
print("\nPair Overlap Summary (Sorted by Density):")
print(pair_df.sort_values('Overlap Density', ascending=False).to_string(index=False, max_colwidth=25))


###########################

# 3. Text Preprocessing
import unicodedata  # For normalization

bangla_stemmer = BanglaStemmer()

stop_words = {
    'অবশ্য', 'অনেক', 'অনেকে', 'অনেকেই', 'অন্তত', 'অথবা', 'অথচ', 'অর্থাত', 'অন্য', 'আজ', 'আছে', 'আপনার', 'আপনি',
    'আবার', 'আমরা', 'আমাকে', 'আমাদের', 'আমার', 'আমি', 'আরও', 'আর', 'আগে', 'আগেই', 'আই', 'অতএব', 'আগামী', 'অবধি',
    'অনুযায়ী', 'আদ্যভাগে', 'এই', 'একই', 'একে', 'একটি', 'এখন', 'এখনও', 'এখানে', 'এখানেই', 'এটি', 'এটা', 'এটাই', 'এতটাই',
    'এবং', 'একবার', 'এবার', 'এদের', 'এঁদের', 'এমন', 'এমনকী', 'এল', 'এর', 'এরা', 'এঁরা', 'এস', 'এত', 'এতে', 'এসে', 'একে',
    'এ', 'ঐ', 'ই', 'ইহা', 'ইত্যাদি', 'উনি', 'উপর', 'উপরে', 'উচিত', 'ও', 'ওই', 'ওর', 'ওরা', 'ওঁর', 'ওঁরা', 'ওকে', 'ওদের',
    'ওঁদের', 'ওখানে', 'কত', 'কবে', 'করতে', 'কয়েক', 'কয়েকটি', 'করবে', 'করলেন', 'করার', 'কারও', 'করা', 'করি', 'করিয়ে', 'করার',
    'করাই', 'করলে', 'করলেন', 'করিতে', 'করিয়া', 'করেছিলেন', 'করছে', 'করছেন', 'করেছেন', 'করেছে', 'করেন', 'করবেন', 'করায়', 'করে',
    'করেই', 'কাছ', 'কাছে', 'কাজে', 'কারণ', 'কিছু', 'কিছুই', 'কিন্তু', 'কিংবা', 'কি', 'কী', 'কেউ', 'কেউই', 'কাউকে', 'কেন', 'কে',
    'কোনও', 'কোনো', 'কোন', 'কখনও', 'ক্ষেত্রে', 'খুব', 'গুলি', 'গিয়ে', 'গিয়েছে', 'গেছে', 'গেল', 'গেলে', 'গোটা', 'চলে', 'ছাড়া',
    'ছাড়াও', 'ছিলেন', 'ছিল', 'জন্য', 'জানা', 'ঠিক', 'তিনি', 'তিনঐ', 'তিনিও', 'তখন', 'তবে', 'তবু', 'তাঁদের', 'তাঁাহারা', 'তাঁরা',
    'তাঁর', 'তাঁকে', 'তাই', 'তেমন', 'তাকে', 'তাহা', 'তাহাতে', 'তাহার', 'তাদের', 'তারপর', 'তারা', 'তারৈ', 'তার', 'তাহলে', 'তিনি',
    'তা', 'তাও', 'তাতে', 'তো', 'তত', 'তুমি', 'তথা', 'তদ্ব্যতীত', 'তথাপি', 'তাঁরা', 'তুমি', 'তুলনামূলক', 'তে', 'তৈরি', 'দিয়ে',
    'দিন', 'দু', 'দুটি', 'দুটো', 'দেওয়া', 'দেখা', 'দেখে', 'দেন', 'দেয়', 'দ্বারা', 'ধরা', 'ধরে', 'নয়', 'নাকি', 'নাগাদ', 'নানা',
    'নিজে', 'নিজেই', 'নিজের', 'নিজেদের', 'নেওয়া', 'নয়', 'পক্ষে', 'পর্যন্ত', 'পাওয়া', 'পারেন', 'পারি', 'পারে', 'পরেই', 'পরেও',
    'পর', 'পরে', 'প্রায়', 'প্রথম', 'প্রভৃতি', 'ফলে', 'ফিরে', 'ফের', 'বরং', 'বলতে', 'বললেন', 'বলা', 'বলেন', 'বলল', 'বলে', 'বহু',
    'বসে', 'বা', 'বিনা', 'বরং', 'বদলে', 'বার', 'বেশ', 'ব্যবহার', 'ভাবে', 'ভাবেই', 'মধ্যে', 'মধ্যভাগে', 'মধ্যদিয়ে', 'মধ্যেই',
    'মোটেই', 'যখন', 'যদি', 'যিনি', 'যাবে', 'যায়', 'যাকে', 'যাওয়া', 'যওয়া', 'যা', 'যাদের', 'যান', 'যায়', 'যেতে', 'যাতে',
    'যেন', 'যেমন', 'যেখানে', 'যদিও', 'রকম', 'রয়েছে', 'রাখা', 'রয়েছে', 'রেখে', 'লক্ষ', 'শুধু', 'শুরু', 'সমস্ত', 'সহ', 'সুতরাং',
    'সব', 'সহিত', 'সাধারণ', 'সামনে', 'সি', 'সেই', 'সেটা', 'সেটি', 'সেটাই', 'সেখান', 'সেখানে', 'সবার', 'স্বয়ং', 'হইতে', 'হইবে',
    'হইয়া', 'হওয়া', 'হওয়া', 'হচ্ছে', 'হতে', 'হত', 'হবে', 'হবেন', 'হয়েছে', 'হয়নি', 'হয়ে', 'হয়েছে', 'হয়', 'হয়েই', 'হয়তো', 'হল',
    'হলে', 'হলেই', 'হলেও', 'হিসাবে', 'হও', 'হয়', 'হয়েছিল', 'হয়েছে', 'হয়নি', 'যত', 'যতটা', 'যতক্ষণ', 'যথা', 'যতক্ষণে', 'যতগুলো',
    'যতটা', 'যতদিন', 'যতক্ষণ', 'যতক্ষণে', 'যতগুলো', 'যতটা', 'যতদিন', 'যতক্ষণ', 'যতক্ষণে', 'যতগুলো', 'যতটা', 'যতদিন', 'যতক্ষণ',
    'যতক্ষণে', 'যতগুলো', 'যতটা', 'যতদিন'
}

# Function to clean text for SentencePiece training
def clean_for_sp_training(text):
    text = str(text)
    # Unicode normalization (NFC) for consistent Bangla chars
    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
    text = re.sub(r'#\w+', '', text)  # Remove hashtags
    text = re.sub(r'@\w+', '', text)  # Remove mentions
    text = re.sub(r'\.\.\.+', '', text)  # Remove ellipses
    text = re.sub(r'[^\u0980-\u09FF\s]', '', text)  # Remove non-Bangla characters, emojis, English
    tokens = text.split()  # Simple tokenization
    # Add stemming before removing stop words
    stemmed_tokens = [bangla_stemmer.stem(word) for word in tokens]
    # Remove stop words after stemming
    tokens = [word for word in stemmed_tokens if word not in stop_words]
    return ' '.join(tokens)

# Train SentencePiece on cleaned text
with open('bangla_text.txt', 'w', encoding='utf-8') as f:
    for text in df['Text']:
        cleaned = clean_for_sp_training(text)
        if cleaned.strip():
            f.write(cleaned + '\n')

spm.SentencePieceTrainer.train(
    input='bangla_text.txt',
    model_prefix='bangla_spm',
    vocab_size=10000,  # Increased vocab size for better representation
    character_coverage=0.9995,
    model_type='bpe'
)
sp = spm.SentencePieceProcessor()
sp.load('bangla_spm.model')

# Updated cleaning function
def clean_bangla_text(text):
    cleaned = clean_for_sp_training(text)  # Now includes stemming from clean_for_sp_training
    if not cleaned.strip():
        return ''
    sp_tokens = sp.encode_as_pieces(cleaned)  # Apply SentencePiece on stemmed text
    return ' '.join(sp_tokens)

df['cleaned_text'] = df['Text'].apply(clean_bangla_text)
df = df[df['cleaned_text'].str.strip() != '']
print("\nSample Cleaned Texts:")
print(df[['Text', 'cleaned_text']].head())



################## Feature Extraction option-1: ( when use bow/tf-idf/char/combined features)
from sklearn.preprocessing import MaxAbsScaler
from scipy.sparse import hstack

X = df['cleaned_text']
y = df[sentiment_cols]
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
print(f"\nTrain Size: {len(X_train)}, Validation Size: {len(X_val)}, Test Size: {len(X_test)}")

bow_vectorizer = CountVectorizer(max_features=3000, ngram_range=(1, 7), analyzer='word')  # Increased features
tfidf_vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 7), analyzer='word')  # Increased
char_vectorizer = TfidfVectorizer(max_features=7000, ngram_range=(3, 8), analyzer='char')  # Increased for better char ngrams

# Initialize separate scalers for each SVM feature set
scalers = {
    'BoW_SVM': MaxAbsScaler(),
    'TF-IDF_SVM': MaxAbsScaler(),
    'Char_SVM': MaxAbsScaler(),
    'Combined_SVM': MaxAbsScaler()
}

X_train_bow = bow_vectorizer.fit_transform(X_train)
X_val_bow = bow_vectorizer.transform(X_val)
X_test_bow = bow_vectorizer.transform(X_test)

X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
X_val_tfidf = tfidf_vectorizer.transform(X_val)
X_test_tfidf = tfidf_vectorizer.transform(X_test)

X_train_char = char_vectorizer.fit_transform(X_train)
X_val_char = char_vectorizer.transform(X_val)
X_test_char = char_vectorizer.transform(X_test)

# (Removed lexicon features)

X_train_combined = hstack([X_train_bow, X_train_tfidf, X_train_char])  # No lexicon
X_val_combined = hstack([X_val_bow, X_val_tfidf, X_val_char])
X_test_combined = hstack([X_test_bow, X_test_tfidf, X_test_char])

# Apply separate scalers
X_train_bow_svm = scalers['BoW_SVM'].fit_transform(X_train_bow)
X_val_bow_svm = scalers['BoW_SVM'].transform(X_val_bow)
X_test_bow_svm = scalers['BoW_SVM'].transform(X_test_bow)

X_train_tfidf_svm = scalers['TF-IDF_SVM'].fit_transform(X_train_tfidf)
X_val_tfidf_svm = scalers['TF-IDF_SVM'].transform(X_val_tfidf)
X_test_tfidf_svm = scalers['TF-IDF_SVM'].transform(X_test_tfidf)

X_train_char_svm = scalers['Char_SVM'].fit_transform(X_train_char)
X_val_char_svm = scalers['Char_SVM'].transform(X_val_char)
X_test_char_svm = scalers['Char_SVM'].transform(X_test_char)

X_train_combined_svm = scalers['Combined_SVM'].fit_transform(X_train_combined)
X_val_combined_svm = scalers['Combined_SVM'].transform(X_val_combined)
X_test_combined_svm = scalers['Combined_SVM'].transform(X_test_combined)

features = {
    'BoW': (X_train_bow, X_val_bow, X_test_bow),
    'TF-IDF': (X_train_tfidf, X_val_tfidf, X_test_tfidf),
    'Char': (X_train_char, X_val_char, X_test_char),
    'Combined': (X_train_combined, X_val_combined, X_test_combined),
    'BoW_SVM': (X_train_bow_svm, X_val_bow_svm, X_test_bow_svm),
    'TF-IDF_SVM': (X_train_tfidf_svm, X_val_tfidf_svm, X_test_tfidf_svm),
    'Char_SVM': (X_train_char_svm, X_val_char_svm, X_test_char_svm),
    'Combined_SVM': (X_train_combined_svm, X_val_combined_svm, X_test_combined_svm)
}



################### Feature Extraction option-2: ( when use Embeddings features only)
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
X = df['cleaned_text']
y = df[sentiment_cols]
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
print(f"\nTrain Size: {len(X_train)}, Validation Size: {len(X_val)}, Test Size: {len(X_test)}")
# TF-IDF for weighting (fit on train; add bigrams for context)
tfidf_weight = TfidfVectorizer(max_features=3000, ngram_range=(1,2), analyzer='word')
tfidf_weight.fit([clean_for_embeddings(t) for t in X_train])
# Train Word2Vec on corpus (skip-gram for sentiment, tuned for Happy/Sad/Angry: min_count=1 for rare neg, wider window/context)
sentences = [re.findall(r'[\u0980-\u09FF]+', clean_for_embeddings(text)) for text in X_train]
word2vec_model = Word2Vec(sentences, vector_size=100, window=10, min_count=1, workers=2, sg=1, epochs=50, seed=42)
def get_weighted_features(text, model, tfidf):
    clean_text = clean_for_embeddings(text)
    words = re.findall(r'[\u0980-\u09FF]+', clean_text)
    if not words:
        return np.zeros(100)
    tfidf_vec = tfidf.transform([clean_text]).toarray()[0]
    word_scores = {word: tfidf_vec[i] for i, word in enumerate(tfidf.get_feature_names_out()) if word in words}
    vectors = []
    weights = []
    for word in words:
        if word in model.wv:
            vectors.append(model.wv[word])
            weight = np.log(1 + word_scores.get(word, 0.1))
            # Stronger boost for moderate-rare words (Sad/Angry terms ~0.1-0.3 tfidf)
            if 0.5 <= word_scores.get(word, 0.1) <= 0.3:
                weight *= 1.5
            weights.append(weight)
    if not vectors:
        return np.zeros(100)
    weights = np.array(weights)
    weights /= weights.sum() # Normalize
    return np.average(vectors, axis=0, weights=weights)
X_train_word2vec = np.array([get_weighted_features(t, word2vec_model, tfidf_weight) for t in X_train])
X_val_word2vec = np.array([get_weighted_features(t, word2vec_model, tfidf_weight) for t in X_val])
X_test_word2vec = np.array([get_weighted_features(t, word2vec_model, tfidf_weight) for t in X_test])
word2vec_scaler = StandardScaler()
X_train_word2vec = word2vec_scaler.fit_transform(X_train_word2vec)
X_val_word2vec = word2vec_scaler.transform(X_val_word2vec)
X_test_word2vec = word2vec_scaler.transform(X_test_word2vec)
# Train custom FastText on corpus (skip-gram for rare neg words, tuned subword/min_count for Sad/Angry)
from gensim.models import FastText
fasttext_model = FastText(sentences, vector_size=100, window=10, min_count=1, workers=2, sg=1, epochs=60, min_n=2, max_n=4, sample=0.0005, seed=42)
def get_fasttext_weighted_features(text, model, tfidf):
    clean_text = clean_for_embeddings(text)
    words = re.findall(r'[\u0980-\u09FF]+', clean_text)
    if not words:
        return np.zeros(100)
    tfidf_vec = tfidf.transform([clean_text]).toarray()[0]
    word_scores = {word: tfidf_vec[i] for i, word in enumerate(tfidf.get_feature_names_out()) if word in words}
    vectors = []
    weights = []
    for word in words:
        vectors.append(model.wv[word])  # Subword OOV handling
        weight = np.log(1 + word_scores.get(word, 0.1))
        # Stronger boost for moderate-rare words (Sad/Angry focus)
        if 0.5 <= word_scores.get(word, 0.1) <= 0.3:
            weight *= 1.5
        weights.append(weight)
    if not vectors:
        return np.zeros(100)
    weights = np.array(weights)
    weights /= weights.sum()
    return np.average(vectors, axis=0, weights=weights)
X_train_fasttext = np.array([get_fasttext_weighted_features(t, fasttext_model, tfidf_weight) for t in X_train])
X_val_fasttext = np.array([get_fasttext_weighted_features(t, fasttext_model, tfidf_weight) for t in X_val])
X_test_fasttext = np.array([get_fasttext_weighted_features(t, fasttext_model, tfidf_weight) for t in X_test])
fasttext_scaler = StandardScaler()
X_train_fasttext = fasttext_scaler.fit_transform(X_train_fasttext)
X_val_fasttext = fasttext_scaler.transform(X_val_fasttext)
X_test_fasttext = fasttext_scaler.transform(X_test_fasttext)
features = {
    'Word2Vec': (X_train_word2vec, X_val_word2vec, X_test_word2vec),
    'FastText': (X_train_fasttext, X_val_fasttext, X_test_fasttext)
}
# Save embedding models/scalers + TF-IDF
joblib.dump(word2vec_model, 'word2vec_model.pkl')
joblib.dump(fasttext_model, 'fasttext_model.pkl')
joblib.dump(word2vec_scaler, 'word2vec_scaler.pkl')
joblib.dump(fasttext_scaler, 'fasttext_scaler.pkl')
joblib.dump(tfidf_weight, 'tfidf_weight.pkl')


# Model Building
models = {
    'RandomForest': RandomForestClassifier(random_state=42, class_weight='balanced'),
    'XGBoost': xgb.XGBClassifier(random_state=42),
    'LightGBM': lgb.LGBMClassifier(random_state=42, class_weight='balanced', verbose=-1),
    'SVM': LinearSVC(random_state=42, dual='auto', class_weight='balanced'),
    'LogisticRegression': LogisticRegression(random_state=42, max_iter=2000, class_weight='balanced')
}

# Expanded parameter grids for better tuning and performance
param_grids = {
    'RandomForest': {
        'estimator__n_estimators': [100, 200, 300],
        'estimator__max_depth': [5, 7, 10],
        'estimator__min_samples_split': [10, 15],
        'estimator__min_samples_leaf': [2, 3, 5],
        'estimator__max_features': [0.3, 'sqrt']
    },
    'XGBoost': {
        'estimator__n_estimators': [100, 200, 300],
        'estimator__max_depth': [3, 5, 7],
        'estimator__learning_rate': [0.05, 0.1],
        'estimator__subsample': [0.7, 0.8, 0.9, 1.0],
        'estimator__colsample_bytree': [0.7, 0.8, 0.9, 1.0],
        'estimator__gamma': [0, 0.1, 0.2],
        'estimator__min_child_weight': [1, 3, 5],
        'estimator__reg_alpha': [0, 0.01, 0.1],
        'estimator__reg_lambda': [0, 0.01, 0.1],
        'estimator__tree_method': ['hist']

    },
    'LightGBM': {
        'estimator__n_estimators': [100, 200, 300],
        'estimator__max_depth': [4, 5, 6, 7],
        'estimator__learning_rate': [0.05, 0.1],
        'estimator__num_leaves': [31, 63],  # ~2^depth for capacity
        'estimator__min_child_samples': [5, 10],
        'estimator__min_child_weight': [0.001, 0.01],
        'estimator__lambda_l1': [0, 0.01, 0.1],
        'estimator__lambda_l2': [0, 0.01, 0.1],
        'estimator__subsample': [0.8, 0.9, 1.0],
        'estimator__colsample_bytree': [0.8, 0.9, 1.0],
        'estimator__bagging_fraction': [0.8, 0.9],
        'estimator__bagging_freq': [1, 2]
    },
    'SVM': {
        'estimator__C': [0.01, 0.1, 0.5, 1],
        'estimator__penalty': ['l1', 'l2'],
        'estimator__loss': ['hinge', 'squared_hinge'],
        'estimator__tol': [1e-4, 1e-3]
    },
    'LogisticRegression': {
        'estimator__C': [0.01, 0.1, 0.5, 1],
        'estimator__penalty': ['l1', 'l2'],
        'estimator__solver': ['liblinear']
    }
}


# Model selection (run one at a time)
model_name_to_run = 'LogisticRegression' # Model Choose
results = {}
best_thresholds = {}
trained_models = {}
evals_results = {} # To store loss history for boosting models
results[model_name_to_run] = {}
best_thresholds[model_name_to_run] = {}
trained_models[model_name_to_run] = {}
evals_results[model_name_to_run] = {}

#feature_list = list(features.keys()) # All embeding features for all models
feature_list = [k for k in features.keys() if not k.endswith('_SVM')] if model_name_to_run != 'SVM' else [k for k in features.keys() if k.endswith('_SVM')]

# Store best params for learning curves
best_params_dict = {}
best_params_dict[model_name_to_run] = {}
# Persist selectors for LR/SVM
trained_selectors = {}
if model_name_to_run in ['LogisticRegression', 'SVM']:
    trained_selectors[model_name_to_run] = {}
from sklearn.feature_selection import SelectKBest, chi2, f_classif
for feature_name in feature_list:
    X_tr, X_v, X_te = features[feature_name]
    print(f"\nTraining {model_name_to_run} with {feature_name} features...")
    if model_name_to_run == 'LightGBM':
        X_tr = X_tr.astype(np.float32)
        X_v = X_v.astype(np.float32)
        X_te = X_te.astype(np.float32)
    model = MultiOutputClassifier(models[model_name_to_run], n_jobs=-1)
    # Use RandomizedSearchCV (increased n_iter for better tuning)
    if model_name_to_run in ['RandomForest', 'XGBoost']:
        grid_search = RandomizedSearchCV(model, param_grids[model_name_to_run], n_iter=10, cv=3, scoring='f1_weighted', n_jobs=1, random_state=42)
    elif model_name_to_run == 'LightGBM':
        grid_search = RandomizedSearchCV(model, param_grids[model_name_to_run], n_iter=20, cv=3, scoring='f1_weighted', n_jobs=1, random_state=42)
    elif model_name_to_run == 'SVM':
        grid_search = RandomizedSearchCV(model, param_grids[model_name_to_run], n_iter=30, cv=3, scoring='f1_weighted', n_jobs=1, random_state=42)
    else:
        grid_search = RandomizedSearchCV(model, param_grids[model_name_to_run], n_iter=30, cv=3, scoring='f1_weighted', n_jobs=1, random_state=42)
    grid_search.fit(X_tr, y_train)
    model = grid_search.best_estimator_
    # Store best params
    best_params = grid_search.best_params_
    best_params_dict[model_name_to_run][feature_name] = best_params
    print(f"Best Parameters for {model_name_to_run} ({feature_name}): {best_params}")
    # For LogisticRegression/SVM, apply per-label feature selection (SelectKBest chi2, k=3000 for SVM; 2300 for LR) + re-fit
    selectors = {}
    if model_name_to_run in ['LogisticRegression', 'SVM']:
        k_sel = 2300 if model_name_to_run == 'LogisticRegression' else 5000
        score_func = f_classif if feature_name in ['Word2Vec', 'FastText'] else chi2  # f_classif for dense embeddings
        print(f"Applying per-label SelectKBest ({score_func.__name__}, k={k_sel}) for {feature_name}...")
        for i, col in enumerate(sentiment_cols):
            selector = SelectKBest(score_func=score_func, k=min(k_sel, X_tr.shape[1]))
            X_tr_sel = selector.fit_transform(X_tr, y_train[col])
            X_v_sel = selector.transform(X_v)
            X_te_sel = selector.transform(X_te)
            selectors[col] = (selector, X_tr_sel, X_v_sel, X_te_sel)
            # Re-fit tuned model on selected features
            params = {k.replace('estimator__', ''): v for k, v in best_params.items() if k.startswith('estimator__')}
            if model_name_to_run == 'LogisticRegression':
                est = LogisticRegression(**params, class_weight='balanced', random_state=42, max_iter=2000)
            else: # SVM
                est = LinearSVC(**params, class_weight='balanced', random_state=42, dual='auto')
            est.fit(X_tr_sel, y_train[col])
            model.estimators_[i] = est
        print(f"Applied per-label feature selection (k={k_sel} {score_func.__name__}) for {model_name_to_run} ({feature_name})")
        trained_selectors[model_name_to_run][feature_name] = selectors
    # For boosting models, re-train per sentiment to get evals_result for loss curves
    if model_name_to_run in ['XGBoost', 'LightGBM']:
        evals_result_feature = {}
        pos_weights = {}
        for col in sentiment_cols:
            neg, pos = np.bincount(y_train[col])
            pos_weights[col] = min(neg / pos if pos > 0 else 1, 1.4) # Cap at 1.4 for Angry prec
        for i, col in enumerate(sentiment_cols):
            params = {k.replace('estimator__', ''): v for k, v in grid_search.best_params_.items() if k.startswith('estimator__')}
            if model_name_to_run == 'XGBoost':
                params['eval_metric'] = ['logloss', 'error']
                params['scale_pos_weight'] = pos_weights[col]
                params['early_stopping_rounds'] = 50
                est = xgb.XGBClassifier(**params)
                est.fit(X_tr, y_train[col], eval_set=[(X_tr, y_train[col]), (X_v, y_val[col])], verbose=False)
                evals_result_feature[col] = est.evals_result()
            elif model_name_to_run == 'LightGBM':
                params['eval_metric'] = ['binary_logloss', 'binary_error']
                params['scale_pos_weight'] = pos_weights[col]
                est = lgb.LGBMClassifier(**params, force_col_wise=True, verbose=-1)
                est.fit(X_tr, y_train[col], eval_set=[(X_tr, y_train[col]), (X_v, y_val[col])], callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)])
                evals_result_feature[col] = est.evals_result_
            model.estimators_[i] = est
        evals_results[model_name_to_run][feature_name] = evals_result_feature
    def optimize_threshold(model, X_val, y_val, sentiment_cols):
        thresholds = np.arange(0.05, 0.99, 0.01)
        best_thresholds = {}
        for i, col in enumerate(sentiment_cols):
            best_score = 0
            best_thr = 0.5
            # For LR/SVM with selection, use selected X_val for proba
            if model_name_to_run in ['LogisticRegression', 'SVM'] and col in selectors:
                _, _, X_v_sel, _ = selectors[col]
                decision_scores = model.estimators_[i].decision_function(X_v_sel)
                probas = 1 / (1 + np.exp(-decision_scores))
                probas = np.clip(probas, 0.01, 0.99)
            else:
                try:
                    probas = model.estimators_[i].predict_proba(X_val)[:, 1]
                except AttributeError:
                    decision_scores = model.estimators_[i].decision_function(X_val)
                    probas = 1 / (1 + np.exp(-decision_scores))
                    probas = np.clip(probas, 0.01, 0.99)
            for thr in thresholds:
                preds = (probas >= thr).astype(int)
                f1 = f1_score(y_val[col], preds, zero_division=0)
                prec = precision_score(y_val[col], preds, zero_division=0)
                rec = recall_score(y_val[col], preds, zero_division=0)
                if col == 'Angry':
                    score = 0.5 * f1 + 0.45 * prec + 0.05 * rec
                elif col == 'Sad':
                    score = 0.52 * f1 + 0.48 * prec
                elif col == 'Happy':
                    score = 0.58 * f1 + 0.4 * prec
                else:
                    score = 0.65 * f1 + 0.3 * prec + 0.05 * rec
                if score > best_score:
                    best_score = score
                    best_thr = thr
            best_thresholds[col] = best_thr
        return best_thresholds
    thresholds = optimize_threshold(model, X_v, y_val, sentiment_cols)
    best_thresholds[model_name_to_run][feature_name] = thresholds
    y_pred_proba = []
    for i, est in enumerate(model.estimators_):
        if model_name_to_run in ['LogisticRegression', 'SVM'] and sentiment_cols[i] in selectors:
            _, _, X_v_sel, _ = selectors[sentiment_cols[i]]
            decision_scores = est.decision_function(X_v_sel)
            proba = 1 / (1 + np.exp(-decision_scores))
            proba = np.clip(proba, 0.01, 0.99)
        else:
            try:
                proba = est.predict_proba(X_v)[:, 1]
            except AttributeError:
                decision_scores = est.decision_function(X_v)
                proba = 1 / (1 + np.exp(-decision_scores))
                proba = np.clip(proba, 0.01, 0.99)
        y_pred_proba.append(proba)
    y_pred_proba = np.array(y_pred_proba).T
    y_pred = np.zeros_like(y_pred_proba)
    for i, col in enumerate(sentiment_cols):
        y_pred[:, i] = (y_pred_proba[:, i] >= thresholds[col]).astype(int)
    metrics = {}
    for i, col in enumerate(sentiment_cols):
        metrics[col] = {
            'Accuracy': accuracy_score(y_val[col], y_pred[:, i]),
            'Precision': precision_score(y_val[col], y_pred[:, i], zero_division=0),
            'Recall': recall_score(y_val[col], y_pred[:, i], zero_division=0),
            'F1-Score': f1_score(y_val[col], y_pred[:, i], zero_division=0),
            'Jaccard': jaccard_score(y_val[col], y_pred[:, i], zero_division=0)
        }
    results[model_name_to_run][feature_name] = metrics
    trained_models[model_name_to_run][feature_name] = model
    print(f"\nValidation Results for {model_name_to_run} ({feature_name}):")
    for col in sentiment_cols:
        print(f"\n{col}:")
        for metric, value in metrics[col].items():
            print(f"{metric}: {value:.4f}")
        print(f"Threshold: {thresholds[col]:.2f}")
# Save current model's trained models, thresholds, and selectors (if applicable)
for feature_name in list(trained_models[model_name_to_run].keys()):
    joblib.dump(trained_models[model_name_to_run][feature_name], f'model_{model_name_to_run}_{feature_name}.pkl')
joblib.dump(best_thresholds[model_name_to_run], f'best_thresholds_{model_name_to_run}.pkl')
if model_name_to_run in ['LogisticRegression', 'SVM']:
    for feature_name in trained_selectors[model_name_to_run]:
        joblib.dump(trained_selectors[model_name_to_run][feature_name], f'selectors_{model_name_to_run}_{feature_name}.pkl')
print(f"Saved models, thresholds, and selectors (if applicable) for {model_name_to_run}")


# 5.5 Ensemble Methods: Voting, Stacking, Hybrid ()
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import f1_score, hamming_loss, precision_score, recall_score, accuracy_score, jaccard_score
from scipy.sparse import hstack
import numpy as np
import joblib
import pandas as pd
import os
# Helper to get positive-class probas as (n_samples, n_outputs) array from MultiOutputClassifier
def get_positive_probas(model, X, selectors=None):
    probas = []
    for i, est in enumerate(model.estimators_):
        col = sentiment_cols[i]
        x_input = X
        # Apply selector if available for this model/feat/col
        if selectors is not None and col in selectors:
            selector = selectors[col][0] # The fitted SelectKBest
            x_input = selector.transform(X)
        try:
            p = est.predict_proba(x_input)[:, 1]
        except AttributeError:
            dec = est.decision_function(x_input)
            p = 1 / (1 + np.exp(-dec))
            p = np.clip(p, 0.01, 0.99)
        probas.append(p)
    return np.array(probas).T # Shape: (n_samples, n_outputs)
# Enhanced threshold optimizer (per-class F1 on val)
def optimize_ensemble_threshold(probas, y_val, sentiment_cols):
    thresholds = np.arange(0.3, 0.7, 0.05) # Coarser grid around 0.5
    best_thresholds = {}
    for i, col in enumerate(sentiment_cols):
        best_score = 0
        best_thr = 0.5
        for thr in thresholds:
            preds = (probas[:, i] >= thr).astype(int)
            f1 = f1_score(y_val[col], preds, zero_division=0)
            if f1 > best_score:
                best_score = f1
                best_thr = thr
        best_thresholds[col] = best_thr
    return best_thresholds
# Load all base models and thresholds (leverages saved files from individual runs)
base_models = ['RandomForest', 'XGBoost', 'LightGBM', 'LogisticRegression', 'SVM']
if 'trained_models' not in locals():
    trained_models = {}
if 'best_thresholds' not in locals():
    best_thresholds = {}
if 'trained_selectors' not in locals():
    trained_selectors = {}
for model_name in base_models:
    if model_name not in trained_models:
        trained_models[model_name] = {}
    if model_name in ['LogisticRegression', 'SVM'] and model_name not in trained_selectors:
        trained_selectors[model_name] = {}
    # Load non-SVM feats
    for feat in ['BoW', 'TF-IDF', 'Char', 'Combined']:
        file = f'model_{model_name}_{feat}.pkl'
        if os.path.exists(file):
            trained_models[model_name][feat] = joblib.load(file)
        if model_name in ['LogisticRegression', 'SVM']:
            sel_file = f'selectors_{model_name}_{feat}.pkl'
            if os.path.exists(sel_file):
                trained_selectors[model_name][feat] = joblib.load(sel_file)
    # Load SVM feats (only for SVM/LR)
    if model_name in ['SVM', 'LogisticRegression']:
        for feat in ['BoW_SVM', 'TF-IDF_SVM', 'Char_SVM', 'Combined_SVM']:
            file = f'model_{model_name}_{feat}.pkl'
            if os.path.exists(file):
                trained_models[model_name][feat] = joblib.load(file)
            sel_file = f'selectors_{model_name}_{feat}.pkl'
            if os.path.exists(sel_file):
                trained_selectors[model_name][feat] = joblib.load(sel_file)
# Load thresholds
for model_name in base_models:
    file = f'best_thresholds_{model_name}.pkl'
    if os.path.exists(file):
        best_thresholds[model_name] = joblib.load(file)
        print(f"Loaded thresholds for {model_name}")
# === USER CONTROL: Run ONE at a time ===
ensemble_to_run = 'Hybrid' # ← Change to 'Voting', 'Stacking', or 'Hybrid'
print(f"\n{'='*60}")
print(f"ENSEMBLE MODE: {ensemble_to_run.upper()}")
print(f"{'='*60}")
# === Feature lists ===
non_svm_features = ['BoW', 'TF-IDF', 'Char', 'Combined']
svm_features = ['BoW_SVM', 'TF-IDF_SVM', 'Char_SVM', 'Combined_SVM']
# === Results storage ===
ensemble_results = []
per_sentiment_results = [] # New: Track per-sentiment F1/Prec/Rec
ensemble_models = {}
ensemble_thresholds = {}
# ==================================================================
# 1. VOTING: Soft voting of XGBoost + LightGBM + RandomForest
# ==================================================================
if ensemble_to_run == 'Voting':
    required = ['XGBoost', 'LightGBM', 'RandomForest']
    if not all(m in trained_models for m in required):
        print("ERROR: Run XGBoost, LightGBM, RandomForest first!")
    else:
        for feat in non_svm_features:
            if feat not in trained_models['XGBoost']:
                continue
            print(f"\n--- Voting on {feat} ---")
            X_tr, X_v, X_te = features[feat]
            if 'LightGBM' in trained_models:
                X_v = X_v.astype(np.float32)
                X_te = X_te.astype(np.float32)
            # Get positive probas using helper (handles list → array; no selectors for trees)
            proba_xgb = get_positive_probas(trained_models['XGBoost'][feat], X_te)
            proba_lgb = get_positive_probas(trained_models['LightGBM'][feat], X_te)
            proba_rf = get_positive_probas(trained_models['RandomForest'][feat], X_te)
            # Average probabilities (now all (n_test, 5) arrays)
            avg_proba_te = (proba_xgb + proba_lgb + proba_rf) / 3
            # Val for thresh opt
            proba_xgb_v = get_positive_probas(trained_models['XGBoost'][feat], X_v)
            proba_lgb_v = get_positive_probas(trained_models['LightGBM'][feat], X_v)
            proba_rf_v = get_positive_probas(trained_models['RandomForest'][feat], X_v)
            avg_proba_v = (proba_xgb_v + proba_lgb_v + proba_rf_v) / 3
            thresholds = optimize_ensemble_threshold(avg_proba_v, y_val, sentiment_cols)
            y_pred = np.zeros_like(avg_proba_te)
            for i, col in enumerate(sentiment_cols):
                y_pred[:, i] = (avg_proba_te[:, i] >= thresholds[col]).astype(int)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            hl = hamming_loss(y_test, y_pred)
            # Per-sentiment F1/Prec/Rec
            per_metrics = {}
            for i, col in enumerate(sentiment_cols):
                per_metrics[col] = {
                    'F1': f1_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Prec': precision_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Rec': recall_score(y_test[col], y_pred[:, i], zero_division=0)
                }
            print(f"Voting ({feat}) → F1-Macro: {f1_macro:.4f} | Hamming: {hl:.4f}")
            print("Per-Sentiment Metrics:", {k: {kk: f"{vv:.4f}" for kk,vv in v.items()} for k,v in per_metrics.items()})
            ensemble_results.append({
                'Ensemble': 'Voting', 'Feature': feat,
                'F1-Macro': round(f1_macro, 4), 'Hamming Loss': round(hl, 4)
            })
            flat_per = {}
            for col in sentiment_cols:
                flat_per[f'F1_{col}'] = round(per_metrics[col]['F1'], 4)
                flat_per[f'Prec_{col}'] = round(per_metrics[col]['Prec'], 4)
                flat_per[f'Rec_{col}'] = round(per_metrics[col]['Rec'], 4)
            per_sentiment_results.append({'Ensemble': 'Voting', 'Feature': feat, **flat_per})
            ensemble_models[feat] = {'type': 'voting', 'thresholds': thresholds}
            ensemble_thresholds[feat] = thresholds
        # SVM feats: SVM + LR voting (direct proba avg, no input alignment)
        for feat in svm_features:
            if feat not in trained_models['SVM']:
                continue
            print(f"\n--- Voting on {feat} ---")
            X_te = features[feat][2]
            # Get SVM probas (on _SVM feat, with selectors)
            proba_svm = get_positive_probas(trained_models['SVM'][feat], X_te, trained_selectors['SVM'].get(feat, {}))
            non_svm_feat = feat.replace('_SVM', '')
            X_te_lr = features[non_svm_feat][2]
            # Get LR probas (on non-SVM feat, with selectors)
            proba_lr = get_positive_probas(trained_models['LogisticRegression'][non_svm_feat], X_te_lr, trained_selectors['LogisticRegression'].get(non_svm_feat, {}))
            avg_proba_te = (proba_svm + proba_lr) / 2
            # Val
            X_v = features[feat][1]
            proba_svm_v = get_positive_probas(trained_models['SVM'][feat], X_v, trained_selectors['SVM'].get(feat, {}))
            X_v_lr = features[non_svm_feat][1]
            proba_lr_v = get_positive_probas(trained_models['LogisticRegression'][non_svm_feat], X_v_lr, trained_selectors['LogisticRegression'].get(non_svm_feat, {}))
            avg_proba_v = (proba_svm_v + proba_lr_v) / 2
            thresholds = optimize_ensemble_threshold(avg_proba_v, y_val, sentiment_cols)
            y_pred = np.zeros_like(avg_proba_te)
            for i, col in enumerate(sentiment_cols):
                y_pred[:, i] = (avg_proba_te[:, i] >= thresholds[col]).astype(int)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            hl = hamming_loss(y_test, y_pred)
            # Per-sentiment F1/Prec/Rec
            per_metrics = {}
            for i, col in enumerate(sentiment_cols):
                per_metrics[col] = {
                    'F1': f1_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Prec': precision_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Rec': recall_score(y_test[col], y_pred[:, i], zero_division=0)
                }
            print(f"Voting ({feat}) → F1-Macro: {f1_macro:.4f} | Hamming: {hl:.4f}")
            print("Per-Sentiment Metrics:", {k: {kk: f"{vv:.4f}" for kk,vv in v.items()} for k,v in per_metrics.items()})
            ensemble_results.append({
                'Ensemble': 'Voting', 'Feature': feat,
                'F1-Macro': round(f1_macro, 4), 'Hamming Loss': round(hl, 4)
            })
            flat_per = {}
            for col in sentiment_cols:
                flat_per[f'F1_{col}'] = round(per_metrics[col]['F1'], 4)
                flat_per[f'Prec_{col}'] = round(per_metrics[col]['Prec'], 4)
                flat_per[f'Rec_{col}'] = round(per_metrics[col]['Rec'], 4)
            per_sentiment_results.append({'Ensemble': 'Voting', 'Feature': feat, **flat_per})
            ensemble_models[feat] = {'type': 'voting_svm', 'thresholds': thresholds}
            ensemble_thresholds[feat] = thresholds
# ==================================================================
# 2. STACKING: Meta-learner on top of all 4 models
# ==================================================================
elif ensemble_to_run == 'Stacking':
    required = ['XGBoost', 'LightGBM', 'RandomForest', 'LogisticRegression']
    if not all(m in trained_models for m in required):
        print("ERROR: Run all 4 models first!")
    else:
        for feat in non_svm_features:
            if feat not in trained_models['XGBoost']:
                continue
            print(f"\n--- Stacking on {feat} ---")
            X_tr, X_v, X_te = features[feat]
            if 'LightGBM' in trained_models:
                X_tr = X_tr.astype(np.float32)
                X_v = X_v.astype(np.float32)
                X_te = X_te.astype(np.float32)
            # === Generate meta-features (NO refit) ===
            meta_tr = np.hstack([
                get_positive_probas(trained_models['XGBoost'][feat], X_tr),
                get_positive_probas(trained_models['LightGBM'][feat], X_tr),
                get_positive_probas(trained_models['RandomForest'][feat], X_tr),
                get_positive_probas(trained_models['LogisticRegression'][feat], X_tr, trained_selectors['LogisticRegression'].get(feat, {}))
            ])
            meta_te = np.hstack([
                get_positive_probas(trained_models['XGBoost'][feat], X_te),
                get_positive_probas(trained_models['LightGBM'][feat], X_te),
                get_positive_probas(trained_models['RandomForest'][feat], X_te),
                get_positive_probas(trained_models['LogisticRegression'][feat], X_te, trained_selectors['LogisticRegression'].get(feat, {}))
            ])
            meta_v = np.hstack([
                get_positive_probas(trained_models['XGBoost'][feat], X_v),
                get_positive_probas(trained_models['LightGBM'][feat], X_v),
                get_positive_probas(trained_models['RandomForest'][feat], X_v),
                get_positive_probas(trained_models['LogisticRegression'][feat], X_v, trained_selectors['LogisticRegression'].get(feat, {}))
            ])
            # === Light meta-learner ===
            meta_learner = MultiOutputClassifier(
                LogisticRegression(max_iter=1000, class_weight='balanced', C=0.1),
                n_jobs=1
            )
            meta_learner.fit(meta_tr, y_train)
            # Predict on val for threshold opt
            meta_pred_proba_val = get_positive_probas(meta_learner, meta_v)
            thresholds = optimize_ensemble_threshold(meta_pred_proba_val, y_val, sentiment_cols)
            # Predict on test
            meta_pred_proba = get_positive_probas(meta_learner, meta_te)
            y_pred = np.zeros_like(meta_pred_proba)
            for i, col in enumerate(sentiment_cols):
                y_pred[:, i] = (meta_pred_proba[:, i] >= thresholds[col]).astype(int)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            hl = hamming_loss(y_test, y_pred)
            # Per-sentiment F1/Prec/Rec
            per_metrics = {}
            for i, col in enumerate(sentiment_cols):
                per_metrics[col] = {
                    'F1': f1_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Prec': precision_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Rec': recall_score(y_test[col], y_pred[:, i], zero_division=0)
                }
            print(f"Stacking ({feat}) → F1-Macro: {f1_macro:.4f} | Hamming: {hl:.4f}")
            print("Per-Sentiment Metrics:", {k: {kk: f"{vv:.4f}" for kk,vv in v.items()} for k,v in per_metrics.items()})
            ensemble_results.append({
                'Ensemble': 'Stacking', 'Feature': feat,
                'F1-Macro': round(f1_macro, 4), 'Hamming Loss': round(hl, 4)
            })
            flat_per = {}
            for col in sentiment_cols:
                flat_per[f'F1_{col}'] = round(per_metrics[col]['F1'], 4)
                flat_per[f'Prec_{col}'] = round(per_metrics[col]['Prec'], 4)
                flat_per[f'Rec_{col}'] = round(per_metrics[col]['Rec'], 4)
            per_sentiment_results.append({'Ensemble': 'Stacking', 'Feature': feat, **flat_per})
            ensemble_models[feat] = {'type': 'stacking', 'model': meta_learner, 'thresholds': thresholds}
            ensemble_thresholds[feat] = thresholds
        # SVM feats: SVM + LR stacking (direct proba hstack, no input alignment)
        for feat in svm_features:
            if feat not in trained_models['SVM']:
                continue
            print(f"\n--- Stacking on {feat} ---")
            X_tr_s, X_v_s, X_te_s = features[feat]
            non_svm_feat = feat.replace('_SVM', '')
            X_tr_n, X_v_n, X_te_n = features[non_svm_feat]
            if 'LightGBM' in trained_models:
                X_tr_s = X_tr_s.astype(np.float32)
                X_v_s = X_v_s.astype(np.float32)
                X_te_s = X_te_s.astype(np.float32)
            proba_svm_tr = get_positive_probas(trained_models['SVM'][feat], X_tr_s, trained_selectors['SVM'].get(feat, {}))
            proba_lr_tr = get_positive_probas(trained_models['LogisticRegression'][non_svm_feat], X_tr_n, trained_selectors['LogisticRegression'].get(non_svm_feat, {}))
            meta_tr = np.hstack([proba_svm_tr, proba_lr_tr])
            proba_svm_te = get_positive_probas(trained_models['SVM'][feat], X_te_s, trained_selectors['SVM'].get(feat, {}))
            proba_lr_te = get_positive_probas(trained_models['LogisticRegression'][non_svm_feat], X_te_n, trained_selectors['LogisticRegression'].get(non_svm_feat, {}))
            meta_te = np.hstack([proba_svm_te, proba_lr_te])
            proba_svm_v = get_positive_probas(trained_models['SVM'][feat], X_v_s, trained_selectors['SVM'].get(feat, {}))
            proba_lr_v = get_positive_probas(trained_models['LogisticRegression'][non_svm_feat], X_v_n, trained_selectors['LogisticRegression'].get(non_svm_feat, {}))
            meta_v = np.hstack([proba_svm_v, proba_lr_v])
            meta_learner = MultiOutputClassifier(
                LogisticRegression(max_iter=1000, class_weight='balanced', C=0.1),
                n_jobs=1
            )
            meta_learner.fit(meta_tr, y_train)
            meta_pred_proba_val = get_positive_probas(meta_learner, meta_v)
            thresholds = optimize_ensemble_threshold(meta_pred_proba_val, y_val, sentiment_cols)
            meta_pred_proba = get_positive_probas(meta_learner, meta_te)
            y_pred = np.zeros_like(meta_pred_proba)
            for i, col in enumerate(sentiment_cols):
                y_pred[:, i] = (meta_pred_proba[:, i] >= thresholds[col]).astype(int)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            hl = hamming_loss(y_test, y_pred)
            # Per-sentiment F1/Prec/Rec
            per_metrics = {}
            for i, col in enumerate(sentiment_cols):
                per_metrics[col] = {
                    'F1': f1_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Prec': precision_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Rec': recall_score(y_test[col], y_pred[:, i], zero_division=0)
                }
            print(f"Stacking ({feat}) → F1-Macro: {f1_macro:.4f} | Hamming: {hl:.4f}")
            print("Per-Sentiment Metrics:", {k: {kk: f"{vv:.4f}" for kk,vv in v.items()} for k,v in per_metrics.items()})
            ensemble_results.append({
                'Ensemble': 'Stacking', 'Feature': feat,
                'F1-Macro': round(f1_macro, 4), 'Hamming Loss': round(hl, 4)
            })
            flat_per = {}
            for col in sentiment_cols:
                flat_per[f'F1_{col}'] = round(per_metrics[col]['F1'], 4)
                flat_per[f'Prec_{col}'] = round(per_metrics[col]['Prec'], 4)
                flat_per[f'Rec_{col}'] = round(per_metrics[col]['Rec'], 4)
            per_sentiment_results.append({'Ensemble': 'Stacking', 'Feature': feat, **flat_per})
            ensemble_models[feat] = {'type': 'stacking_svm', 'model': meta_learner, 'thresholds': thresholds}
            ensemble_thresholds[feat] = thresholds
# ==================================================================
# 3. HYBRID: Tree Voting → Feed into SVM
# ==================================================================
elif ensemble_to_run == 'Hybrid':
    required = ['XGBoost', 'LightGBM', 'RandomForest', 'SVM']
    if not all(m in trained_models for m in required):
        print("ERROR: Run XGBoost, LightGBM, RandomForest, SVM first!")
    else:
        for non_svm_feat in non_svm_features:
            svm_feat = non_svm_feat + '_SVM'
            if svm_feat not in features or svm_feat not in trained_models['SVM']:
                continue
            print(f"\n--- Hybrid: {non_svm_feat} → {svm_feat} ---")
            X_tr_n, X_v_n, X_te_n = features[non_svm_feat]
            X_tr_s, X_v_s, X_te_s = features[svm_feat]
            if 'LightGBM' in trained_models:
                X_tr_n = X_tr_n.astype(np.float32)
                X_v_n = X_v_n.astype(np.float32)
                X_te_n = X_te_n.astype(np.float32)
            tree_proba_tr = (get_positive_probas(trained_models['XGBoost'][non_svm_feat], X_tr_n) +
                             get_positive_probas(trained_models['LightGBM'][non_svm_feat], X_tr_n) +
                             get_positive_probas(trained_models['RandomForest'][non_svm_feat], X_tr_n)) / 3
            tree_proba_te = (get_positive_probas(trained_models['XGBoost'][non_svm_feat], X_te_n) +
                             get_positive_probas(trained_models['LightGBM'][non_svm_feat], X_te_n) +
                             get_positive_probas(trained_models['RandomForest'][non_svm_feat], X_te_n)) / 3
            X_hybrid_tr = hstack([X_tr_s, tree_proba_tr])
            X_hybrid_te = hstack([X_te_s, tree_proba_te])
            hybrid_svm = MultiOutputClassifier(LinearSVC(C=0.01, class_weight='balanced', dual='auto'), n_jobs=1)
            hybrid_svm.fit(X_hybrid_tr, y_train)
            # Val for thresh opt
            tree_proba_v = (get_positive_probas(trained_models['XGBoost'][non_svm_feat], X_v_n) +
                            get_positive_probas(trained_models['LightGBM'][non_svm_feat], X_v_n) +
                            get_positive_probas(trained_models['RandomForest'][non_svm_feat], X_v_n)) / 3
            X_hybrid_v = hstack([X_v_s, tree_proba_v])
            y_pred_v_dec = np.array([est.decision_function(X_hybrid_v) for est in hybrid_svm.estimators_]).T
            proba_v = 1 / (1 + np.exp(-y_pred_v_dec))
            proba_v = np.clip(proba_v, 0.01, 0.99)
            thresholds = optimize_ensemble_threshold(proba_v, y_val, sentiment_cols)
            # Test predict with thresh
            y_pred_dec = np.array([est.decision_function(X_hybrid_te) for est in hybrid_svm.estimators_]).T
            proba_te = 1 / (1 + np.exp(-y_pred_dec))
            proba_te = np.clip(proba_te, 0.01, 0.99)
            y_pred = np.zeros_like(proba_te)
            for i, col in enumerate(sentiment_cols):
                y_pred[:, i] = (proba_te[:, i] >= thresholds[col]).astype(int)
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            hl = hamming_loss(y_test, y_pred)
            # Per-sentiment F1/Prec/Rec
            per_metrics = {}
            for i, col in enumerate(sentiment_cols):
                per_metrics[col] = {
                    'F1': f1_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Prec': precision_score(y_test[col], y_pred[:, i], zero_division=0),
                    'Rec': recall_score(y_test[col], y_pred[:, i], zero_division=0)
                }
            print(f"Hybrid ({non_svm_feat}+SVM) → F1-Macro: {f1_macro:.4f} | Hamming: {hl:.4f}")
            print("Per-Sentiment Metrics:", {k: {kk: f"{vv:.4f}" for kk,vv in v.items()} for k,v in per_metrics.items()})
            ensemble_results.append({
                'Ensemble': 'Hybrid', 'Feature': f'{non_svm_feat}+SVM',
                'F1-Macro': round(f1_macro, 4), 'Hamming Loss': round(hl, 4)
            })
            flat_per = {}
            for col in sentiment_cols:
                flat_per[f'F1_{col}'] = round(per_metrics[col]['F1'], 4)
                flat_per[f'Prec_{col}'] = round(per_metrics[col]['Prec'], 4)
                flat_per[f'Rec_{col}'] = round(per_metrics[col]['Rec'], 4)
            per_sentiment_results.append({'Ensemble': 'Hybrid', 'Feature': f'{non_svm_feat}+SVM', **flat_per})
            ensemble_models[f'{non_svm_feat}+SVM'] = {'type': 'hybrid', 'model': hybrid_svm, 'thresholds': thresholds}
            ensemble_thresholds[f'{non_svm_feat}+SVM'] = thresholds
# ==================================================================
# FINAL SUMMARY (Enhanced: Add Per-Sentiment)
# ==================================================================
if ensemble_results:
    summary_df = pd.DataFrame(ensemble_results)
    per_sent_df = pd.DataFrame(per_sentiment_results)
    print(f"\n{'='*60}")
    print(f"{ensemble_to_run.upper()} ENSEMBLE SUMMARY")
    print(f"{'='*60}")
    print(summary_df.sort_values('F1-Macro', ascending=False).to_string(index=False))
    print(f"\nPer-Sentiment Metrics Details:")
    print(per_sent_df.sort_values('Ensemble', ascending=False).to_string(index=False))
    summary_df.to_csv(f'ensemble_summary_{ensemble_to_run}.csv', index=False)
    per_sent_df.to_csv(f'ensemble_per_sentiment_{ensemble_to_run}.csv', index=False) # New save
    joblib.dump(ensemble_models, f'ensemble_{ensemble_to_run}_models.pkl')
    joblib.dump(ensemble_thresholds, f'ensemble_{ensemble_to_run}_thresholds.pkl')
    print(f"Saved: ensemble_{ensemble_to_run}_models.pkl, ensemble_per_sentiment_{ensemble_to_run}.csv")
else:
    print("No results. Check if all base models are trained.")



# Learning Curve and Loss Curve (with Over/Underfitting Detection)
from sklearn.model_selection import learning_curve
from sklearn.metrics import make_scorer, log_loss
from sklearn.feature_selection import SelectKBest, chi2, f_classif

scorer = make_scorer(f1_score, average='weighted', zero_division=0)
for model_name in trained_models:
    for feature_name in trained_models[model_name]:
        model = trained_models[model_name][feature_name]
        X_tr, X_v, _ = features[feature_name]
        if model_name in ['LightGBM', 'XGBoost']:
            X_tr = X_tr.astype(np.float32)
            X_v = X_v.astype(np.float32)
        # For LR/SVM, compute shared proxy selection for LC/incremental loss consistency
        if model_name in ['LogisticRegression', 'SVM']:
            y_proxy = y_train.sum(axis=1) # Multi-label proxy
            score_func_proxy = f_classif if feature_name in ['Word2Vec', 'FastText'] else chi2  # f_classif for dense
            selector_proxy = SelectKBest(score_func=score_func_proxy, k=min(80, X_tr.shape[1]))
            X_tr_sel_proxy = selector_proxy.fit_transform(X_tr, y_proxy)
            X_v_sel_proxy = selector_proxy.transform(X_v)
        else:
            X_tr_sel_proxy, X_v_sel_proxy = X_tr, X_v
        # Proper Learning Curve (retrain progressively) - Use proxy selected for LR/SVM
        print(f"\nPlotting Learning Curve for {model_name} ({feature_name})...")
        params = best_params_dict[model_name][feature_name]
        base_params = {k.replace('estimator__', ''): v for k, v in params.items() if k.startswith('estimator__')}
        base_est_class = models[model_name].__class__
        if model_name == 'LightGBM':
            base_est_class = lgb.LGBMClassifier(verbose=-1, **base_params)
        elif model_name == 'XGBoost':
            base_est_class = xgb.XGBClassifier(**base_params)
        else:
            base_est_class = base_est_class(**base_params)
        estimator = MultiOutputClassifier(base_est_class, n_jobs=1)
        train_sizes_abs, train_scores, val_scores = learning_curve(
            estimator, X_tr_sel_proxy if model_name in ['LogisticRegression', 'SVM'] else X_tr, y_train,
            cv=3, scoring=scorer,
            train_sizes=np.linspace(0.1, 1.0, 10),
            n_jobs=1, random_state=42, shuffle=True
        )
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std = np.std(train_scores, axis=1)
        val_scores_mean = np.mean(val_scores, axis=1)
        val_scores_std = np.std(val_scores, axis=1)
        # Plot with confidence bands
        plt.figure(figsize=(10, 6))
        plt.fill_between(train_sizes_abs, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std, alpha=0.1, color='blue')
        plt.fill_between(train_sizes_abs, val_scores_mean - val_scores_std, val_scores_mean + val_scores_std, alpha=0.1, color='green')
        plt.plot(train_sizes_abs, train_scores_mean, 'o-', color='blue', label='Training F1 (Weighted)')
        plt.plot(train_sizes_abs, val_scores_mean, 'o-', color='green', label='Validation F1 (Weighted)')
        plt.title(f'Learning Curve for {model_name} ({feature_name})')
        plt.xlabel('Training Examples')
        plt.ylabel('F1 Score (Weighted)')
        plt.legend(loc='best')
        plt.grid()
        plt.show()
        # Over/Underfitting Detection
        final_gap = train_scores_mean[-1] - val_scores_mean[-1]
        mean_score = np.mean([train_scores_mean[-1], val_scores_mean[-1]])
        print(f"Diagnostic for {model_name} ({feature_name}):")
        if final_gap > 0.25:
            print(f"Potential Overfitting: Train-Val Gap = {final_gap:.4f} (High gap)")
        elif mean_score < 0.6:
            print(f"Potential Underfitting: Mean Score = {mean_score:.4f} (Low performance)")
        else:
            print("Good Fit: Balanced performance")
        # Loss Curve (for boosting models via evals; others via incremental param sweep)
        if model_name in ['XGBoost', 'LightGBM'] and model_name in evals_results and feature_name in evals_results[model_name]:
            evals_result_feature = evals_results[model_name][feature_name]
            for col in sentiment_cols:
                if col in evals_result_feature and (model_name == 'XGBoost' and 'validation_0' in evals_result_feature[col] or model_name == 'LightGBM' and 'training' in evals_result_feature[col]):
                    plt.figure(figsize=(10, 6))
                    if model_name == 'XGBoost':
                        if 'logloss' in evals_result_feature[col]['validation_0']:
                            plt.plot(evals_result_feature[col]['validation_0']['logloss'], label='Train Loss')
                            plt.plot(evals_result_feature[col]['validation_1']['logloss'], label='Val Loss')
                    elif model_name == 'LightGBM':
                        if 'binary_logloss' in evals_result_feature[col]['training']:
                            plt.plot(evals_result_feature[col]['training']['binary_logloss'], label='Train Loss')
                            plt.plot(evals_result_feature[col]['valid_1']['binary_logloss'], label='Val Loss')
                    plt.title(f'Loss Curve for {col} - {model_name} ({feature_name})')
                    plt.xlabel('Iterations')
                    plt.ylabel('Log Loss')
                    plt.legend(loc='best')
                    plt.grid()
                    plt.show()
                    # Loss-Based Diagnostic (per sentiment)
                    if model_name == 'XGBoost':
                        tr_loss = evals_result_feature[col]['validation_0']['logloss'][-1]
                        v_loss = evals_result_feature[col]['validation_1']['logloss'][-1]
                    elif model_name == 'LightGBM':
                        tr_loss = evals_result_feature[col]['training']['binary_logloss'][-1]
                        v_loss = evals_result_feature[col]['valid_1']['binary_logloss'][-1]
                    loss_gap = v_loss - tr_loss
                    print(f"Diagnostic for {col}:")
                    if loss_gap > 0.3:
                        print(f"Potential Overfitting: Val-Train Loss Gap = {loss_gap:.4f}")
                    elif v_loss > 0.7:
                        print(f"Potential Underfitting: High Val Loss = {v_loss:.4f}")
                    else:
                        print("Good Fit")
                else:
                    print(f"No loss data for {col}")
        else:
            # Incremental loss curve for RF/SVM/LR (log loss vs. key param as proxy for iterations) - Use proxy selected for LR/SVM
            print(f"Computing Incremental Loss Curve for {model_name} ({feature_name})...")
            best_params_local = best_params_dict[model_name][feature_name]
            if model_name == 'RandomForest':
                max_n_est = best_params_local['estimator__n_estimators']
                param_steps = np.linspace(10, max_n_est, 10, dtype=int) # 10 steps to best n_estimators
                x_label = 'Trees (Iterations)'
            elif model_name in ['SVM', 'LogisticRegression']:
                param_steps = np.logspace(-2, 1, 10) # Vary C
                base_params['C'] = param_steps[0]
                x_label = 'C (Regularization)'
            else:
                continue # Skip if unsupported
            train_losses = {col: [] for col in sentiment_cols}
            val_losses = {col: [] for col in sentiment_cols}
            temp_X_tr = X_tr_sel_proxy if model_name in ['LogisticRegression', 'SVM'] else X_tr
            temp_X_v = X_v_sel_proxy if model_name in ['LogisticRegression', 'SVM'] else X_v
            for step in param_steps:
                if model_name == 'RandomForest':
                    base_params['n_estimators'] = step
                else:
                    base_params['C'] = step
                base_est = models[model_name].__class__(**base_params)
                temp_model = MultiOutputClassifier(base_est, n_jobs=1)
                temp_model.fit(temp_X_tr, y_train)
                for i, col in enumerate(sentiment_cols):
                    try:
                        tr_proba = temp_model.estimators_[i].predict_proba(temp_X_tr)[:, 1]
                        v_proba = temp_model.estimators_[i].predict_proba(temp_X_v)[:, 1]
                    except AttributeError: # SVM/LR use decision_function
                        tr_dec = temp_model.estimators_[i].decision_function(temp_X_tr)
                        v_dec = temp_model.estimators_[i].decision_function(temp_X_v)
                        tr_proba = 1 / (1 + np.exp(-tr_dec))
                        v_proba = 1 / (1 + np.exp(-v_dec))
                        tr_proba = np.clip(tr_proba, 1e-15, 1 - 1e-15)
                        v_proba = np.clip(v_proba, 1e-15, 1 - 1e-15)
                    train_losses[col].append(log_loss(y_train[col], tr_proba))
                    val_losses[col].append(log_loss(y_val[col], v_proba))
            # Avg loss plot + per-sentiment
            avg_train = np.mean([train_losses[col] for col in sentiment_cols], axis=0)
            avg_val = np.mean([val_losses[col] for col in sentiment_cols], axis=0)
            plt.figure(figsize=(10, 6))
            plt.plot(param_steps, avg_train, 'o-', label='Avg Train Loss', color='blue')
            plt.plot(param_steps, avg_val, 's-', label='Avg Val Loss', color='green')
            plt.title(f'Avg Loss Curve - {model_name} ({feature_name})')
            plt.xlabel(x_label)
            plt.ylabel('Log Loss')
            plt.legend(loc='best')
            plt.grid(True)
            plt.show()
            for col in sentiment_cols:
                plt.figure(figsize=(10, 6))
                plt.plot(param_steps, train_losses[col], 'o-', label='Train Loss', color='blue')
                plt.plot(param_steps, val_losses[col], 's-', label='Val Loss', color='green')
                plt.title(f'Loss Curve for {col} - {model_name} ({feature_name})')
                plt.xlabel(x_label)
                plt.ylabel('Log Loss')
                plt.legend(loc='best')
                plt.grid(True)
                plt.show()
            # Diagnostic using final (best) model losses + model-specific thresholds
            print(f"Diagnostic for {model_name} ({feature_name}) using Best Model Losses:")
            underfit_thresh = 0.7 # Standardized for non-boosting (val-focus avoids false flags)
            for i, col in enumerate(sentiment_cols):
                if model_name in ['LogisticRegression', 'SVM'] and feature_name in trained_selectors.get(model_name_to_run, {}):
                    _, X_tr_sel, X_v_sel, _ = trained_selectors[model_name_to_run][feature_name][col]
                    tr_dec = model.estimators_[i].decision_function(X_tr_sel)
                    v_dec = model.estimators_[i].decision_function(X_v_sel)
                    tr_proba = 1 / (1 + np.exp(-tr_dec))
                    v_proba = 1 / (1 + np.exp(-v_dec))
                    tr_proba = np.clip(tr_proba, 1e-15, 1 - 1e-15)
                    v_proba = np.clip(v_proba, 1e-15, 1 - 1e-15)
                else:
                    try:
                        tr_proba = model.estimators_[i].predict_proba(X_tr)[:, 1]
                        v_proba = model.estimators_[i].predict_proba(X_v)[:, 1]
                    except AttributeError:
                        tr_dec = model.estimators_[i].decision_function(X_tr)
                        v_dec = model.estimators_[i].decision_function(X_v)
                        tr_proba = 1 / (1 + np.exp(-tr_dec))
                        v_proba = 1 / (1 + np.exp(-v_dec))
                        tr_proba = np.clip(tr_proba, 1e-15, 1 - 1e-15)
                        v_proba = np.clip(v_proba, 1e-15, 1 - 1e-15)
                tr_loss = log_loss(y_train[col], tr_proba)
                v_loss = log_loss(y_val[col], v_proba)
                loss_gap = v_loss - tr_loss
                print(f"{col} (Train: {tr_loss:.4f}, Val: {v_loss:.4f}, Gap: {loss_gap:.4f}):", end=' ')
                if loss_gap > 0.2:
                    print("Potential Overfitting")
                elif v_loss > underfit_thresh:
                    print("Potential Underfitting")
                else:
                    print("Good Fit")


# Train/Validation Accuracy (with Over/Underfitting Detection)
from sklearn.metrics import accuracy_score

for model_name in trained_models:
    for feature_name in trained_models[model_name]:
        model = trained_models[model_name][feature_name]
        X_tr, X_v, _ = features[feature_name]

        # Cast to np.float32 for LightGBM and XGBoost
        if model_name in ['LightGBM', 'XGBoost']:
            X_tr = X_tr.astype(np.float32)
            X_v = X_v.astype(np.float32)

        # Compute predictions for training and validation sets
        if model_name in ['LogisticRegression', 'SVM'] and feature_name in trained_selectors.get(model_name_to_run, {}):
            y_tr_pred_list = []
            y_v_pred_list = []
            for i, col in enumerate(sentiment_cols):
                _, X_tr_sel, X_v_sel, _ = trained_selectors[model_name_to_run][feature_name][col]
                pred_tr = model.estimators_[i].predict(X_tr_sel)
                pred_v = model.estimators_[i].predict(X_v_sel)
                y_tr_pred_list.append(pred_tr)
                y_v_pred_list.append(pred_v)
            y_tr_pred = np.column_stack(y_tr_pred_list)
            y_v_pred = np.column_stack(y_v_pred_list)
        else:
            y_tr_pred = model.predict(X_tr)
            y_v_pred = model.predict(X_v)

        # Accuracy Curve
        accuracies_tr = {col: accuracy_score(y_train[col], y_tr_pred[:, i]) for i, col in enumerate(sentiment_cols)}
        accuracies_v = {col: accuracy_score(y_val[col], y_v_pred[:, i]) for i, col in enumerate(sentiment_cols)}

        plt.figure(figsize=(10, 6))
        plt.plot(sentiment_cols, [accuracies_tr[col] for col in sentiment_cols], label='Training Accuracy', marker='o', color='blue')
        plt.plot(sentiment_cols, [accuracies_v[col] for col in sentiment_cols], label='Validation Accuracy', marker='o', color='green')
        plt.title(f'Accuracy Curve for {model_name} ({feature_name})')
        plt.xlabel('Sentiment')
        plt.ylabel('Accuracy')
        plt.legend(loc='best')
        plt.grid()
        plt.show()

        # Accuracy-Based Diagnostic (per sentiment)
        print(f"Diagnostic for {model_name} ({feature_name}) - Accuracy:")
        under_acc_thresh = 0.65  # Imbalance-tolerant (Sad/Angry ~0.53-0.68 acc ok)
        for col in sentiment_cols:
            gap = accuracies_tr[col] - accuracies_v[col]
            mean_acc = (accuracies_tr[col] + accuracies_v[col]) / 2
            print(f"{col}:")
            if gap > 0.25:
                print(f"Potential Overfitting: Train-Val Accuracy Gap = {gap:.4f}")
            elif mean_acc < under_acc_thresh:
                print(f"Potential Underfitting: Mean Accuracy = {mean_acc:.4f}")
            else:
                print("Good Fit")
                   

# 6. Final Evaluation on Test Set
print("\nTest Set Evaluation:")
summary = []
#feature_list = list(features.keys())  # No _SVM filter for embeddings
feature_list = [k for k in features.keys() if not k.endswith('_SVM')] if model_name_to_run != 'SVM' else [k for k in features.keys() if k.endswith('_SVM')]  # for ow/tf-idf/char/combined and svm features 
for feature_name in feature_list:
    X_tr, X_v, X_te = features[feature_name]
    if model_name_to_run == 'LightGBM':
        X_te = X_te.astype(np.float32)
    model = trained_models[model_name_to_run][feature_name]
    thresholds = best_thresholds[model_name_to_run][feature_name]
    y_pred_proba = []
    for i, est in enumerate(model.estimators_):
        if model_name_to_run in ['LogisticRegression', 'SVM'] and feature_name in trained_selectors.get(model_name_to_run, {}):
            _, _, _, X_te_sel = trained_selectors[model_name_to_run][feature_name][sentiment_cols[i]]
            decision_scores = est.decision_function(X_te_sel)
            proba = 1 / (1 + np.exp(-decision_scores))
            proba = np.clip(proba, 0.01, 0.99)
        else:
            try:
                proba = est.predict_proba(X_te)[:, 1]
            except AttributeError:
                decision_scores = est.decision_function(X_te)
                proba = 1 / (1 + np.exp(-decision_scores))
                proba = np.clip(proba, 0.01, 0.99)
        y_pred_proba.append(proba)
    y_pred_proba = np.array(y_pred_proba).T
    y_pred = np.zeros_like(y_pred_proba)
    for i, col in enumerate(sentiment_cols):
        y_pred[:, i] = (y_pred_proba[:, i] >= thresholds[col]).astype(int)
    print(f"\n{model_name_to_run} ({feature_name}) - Multi-label Metrics:")
    metrics = {
        'Hamming Loss': hamming_loss(y_test, y_pred),
        'Subset Accuracy': accuracy_score(y_test, y_pred),
        'F1-Score (Micro)': f1_score(y_test, y_pred, average='micro', zero_division=0),
        'F1-Score (Macro)': f1_score(y_test, y_pred, average='macro', zero_division=0),
        'Precision (Micro)': precision_score(y_test, y_pred, average='micro', zero_division=0),
        'Precision (Macro)': precision_score(y_test, y_pred, average='macro', zero_division=0),
        'Recall (Micro)': recall_score(y_test, y_pred, average='micro', zero_division=0),
        'Recall (Macro)': recall_score(y_test, y_pred, average='macro', zero_division=0),
        'Jaccard (Micro)': jaccard_score(y_test, y_pred, average='micro', zero_division=0)
    }
    print(f"Hamming Loss: {metrics['Hamming Loss']:.4f}")
    print(f"Subset Accuracy: {metrics['Subset Accuracy']:.4f}")
    print(f"F1-Score (Micro): {metrics['F1-Score (Micro)']:.4f}")
    print(f"F1-Score (Macro): {metrics['F1-Score (Macro)']:.4f}")
    print(f"Precision (Micro): {metrics['Precision (Micro)']:.4f}")
    print(f"Precision (Macro): {metrics['Precision (Macro)']:.4f}")
    print(f"Recall (Micro): {metrics['Recall (Micro)']:.4f}")
    print(f"Recall (Macro): {metrics['Recall (Macro)']:.4f}")
    print(f"Jaccard (Micro): {metrics['Jaccard (Micro)']:.4f}")
    for i, col in enumerate(sentiment_cols):
        print(f"\n{col}:")
        print(f"Accuracy: {accuracy_score(y_test[col], y_pred[:, i]):.4f}")
        print(f"Precision: {precision_score(y_test[col], y_pred[:, i], zero_division=0):.4f}")
        print(f"Recall: {recall_score(y_test[col], y_pred[:, i], zero_division=0):.4f}")
        print(f"F1-Score: {f1_score(y_test[col], y_pred[:, i], zero_division=0):.4f}")
        print(f"Jaccard: {jaccard_score(y_test[col], y_pred[:, i], zero_division=0):.4f}")
        cm = confusion_matrix(y_test[col], y_pred[:, i])
        plt.figure(figsize=(5, 4))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title(f'Confusion Matrix: {col} ({model_name_to_run} - {feature_name})')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.show()
    # ROC-AUC Curves
    plt.figure(figsize=(10, 8))
    mean_fpr = np.linspace(0, 1, 100)
    tprs = []
    aucs = []
    for i, col in enumerate(sentiment_cols):
        fpr, tpr, _ = roc_curve(y_test[col], y_pred_proba[:, i])
        roc_auc = auc(fpr, tpr)
        aucs.append(roc_auc)
        plt.plot(fpr, tpr, label=f'{col} (AUC = {roc_auc:.2f})')
        interp_tpr = np.interp(mean_fpr, fpr, tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    plt.plot(mean_fpr, mean_tpr, label=f'Mean ROC (AUC = {mean_auc:.2f})', lw=2, alpha=0.8)
    plt.plot([0, 1], [0, 1], 'k--', label='Chance')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC-AUC Curve Comparison for {model_name_to_run} ({feature_name})')
    plt.legend(loc='lower right')
    plt.show()
    summary.append({
        'Model': model_name_to_run,
        'Feature': feature_name,
        **metrics
    })
# Summary Table
summary_df = pd.DataFrame(summary)
print("\nModel Comparison Summary:")
print(summary_df.sort_values(by='F1-Score (Macro)', ascending=False))
summary_df.to_csv(f'summary_{model_name_to_run}.csv', index=False)
print(f"Saved summary for {model_name_to_run} to 'summary_{model_name_to_run}.csv'")


# Prediction Function (Handles Ensembles with bow/tf-idf/char/combined, svm features and embeddings features)
def predict_sentiments(text, model, embedding_model, tfidf_weight, scaler, vectorizer, thresholds, sentiment_cols, feature_name, is_combined=False, is_svm=False, is_ensemble=False, ensemble_type=None, ensemble_feat=None):
    cleaned_text = clean_bangla_text(text)
    if not cleaned_text.strip():
        print(f"\nText: {text}")
        print("No valid Bangla text after cleaning.")
        return [], []

    if is_combined:
        bow_vec = vectorizer[0].transform([cleaned_text])
        tfidf_vec = vectorizer[1].transform([cleaned_text])
        char_vec = vectorizer[2].transform([cleaned_text])
        text_vector = hstack([bow_vec, tfidf_vec, char_vec])
    else:
        text_vector = vectorizer.transform([cleaned_text])

    if is_svm:
        scaler_key = best_feature_name
        if scaler_key in scalers:
            text_vector = scalers[scaler_key].transform(text_vector)
        else:
            raise ValueError(f"No scaler found for feature set {scaler_key}")
    
    # Get embedding vector
    if feature_name == 'Word2Vec':
        text_vector = get_weighted_features(cleaned_text, embedding_model, tfidf_weight)
    elif feature_name == 'FastText':
        text_vector = get_fasttext_weighted_features(cleaned_text, embedding_model, tfidf_weight)
    else:
        raise ValueError(f"Unsupported feature: {feature_name}")
    text_vector = scaler.transform([text_vector])[0]  # Reshape/scale


    if model_name_to_run == 'LightGBM':
        text_vector = text_vector.astype(np.float32)

    if is_ensemble:
        if ensemble_type == 'voting':
            # Manual avg proba (non-SVM: 3 trees; SVM: SVM+LR)
            if not is_svm:
                proba_xgb = trained_models['XGBoost'][ensemble_feat].predict_proba(text_vector)[:, 1]
                proba_lgb = trained_models['LightGBM'][ensemble_feat].predict_proba(text_vector)[:, 1]
                proba_rf = trained_models['RandomForest'][ensemble_feat].predict_proba(text_vector)[:, 1]
                probas = (proba_xgb + proba_lgb + proba_rf) / 3
            else:
                svm_dec = trained_models['SVM'][ensemble_feat].decision_function(text_vector)
                proba_svm = 1 / (1 + np.exp(-svm_dec))
                proba_lr = trained_models['LogisticRegression'][ensemble_feat.replace('_SVM', '')].predict_proba(text_vector)[:, 1]
                probas = (proba_svm + proba_lr) / 2
        elif ensemble_type == 'stacking':
            meta_model = model['model']
            if not is_svm:
                meta_te = np.hstack([
                    trained_models['XGBoost'][ensemble_feat].predict_proba(text_vector),
                    trained_models['LightGBM'][ensemble_feat].predict_proba(text_vector),
                    trained_models['RandomForest'][ensemble_feat].predict_proba(text_vector),
                    trained_models['LogisticRegression'][ensemble_feat].predict_proba(text_vector)
                ])
            else:
                svm_dec_te = trained_models['SVM'][ensemble_feat].decision_function(text_vector)
                proba_svm_te = 1 / (1 + np.exp(-svm_dec_te))
                proba_lr_te = trained_models['LogisticRegression'][ensemble_feat.replace('_SVM', '')].predict_proba(text_vector)
                meta_te = np.hstack([proba_svm_te, proba_lr_te])
            probas = np.column_stack([meta_model.estimators_[i].predict_proba(meta_te)[:, 1] for i in range(len(sentiment_cols))])
        elif ensemble_type == 'hybrid':
            # Tree proba + SVM feats hstack + predict
            non_svm_feat = ensemble_feat.replace('_SVM', '')
            tree_proba_te = (trained_models['XGBoost'][non_svm_feat].predict_proba(text_vector) +
                             trained_models['LightGBM'][non_svm_feat].predict_proba(text_vector) +
                             trained_models['RandomForest'][non_svm_feat].predict_proba(text_vector)) / 3
            X_hybrid_te = hstack([text_vector, tree_proba_te])
            probas = model['model'].predict_proba(X_hybrid_te)[:, 1]
        else:
            raise ValueError("Unknown ensemble type.")
    else:
        probas = []
        for i, est in enumerate(model.estimators_):
            if model_name_to_run in ['LogisticRegression', 'SVM'] and feature_name and best_feature_name in trained_selectors.get(model_name_to_run, {}):
                selector, _, _, _ = trained_selectors[model_name_to_run][feature_name][best_feature_name][sentiment_cols[i]]
                text_vector_sel = selector.transform(text_vector)
                decision_scores = est.decision_function(text_vector_sel)
                proba = 1 / (1 + np.exp(-decision_scores))
                proba = np.clip(proba, 0.01, 0.99)
            else:
                try:
                    proba = est.predict_proba(text_vector)[:, 1]
                except AttributeError:
                    decision_scores = est.decision_function(text_vector)
                    proba = 1 / (1 + np.exp(-decision_scores))
                    proba = np.clip(proba, 0.01, 0.99)
            probas.append(proba)
        probas = np.array(probas).T[0]

    present_indices = [i for i in range(len(sentiment_cols)) if probas[i] >= thresholds[sentiment_cols[i]]]
    present_sentiments = [sentiment_cols[i] for i in present_indices]

    if present_sentiments:
        present_probas = probas[present_indices]
        total_proba = present_probas.sum()
        normalized_probas = (present_probas / total_proba) * 100 if total_proba > 0 else present_probas * 0
        print(f"\nText: {text}")
        print("Present Sentiments and Percentages:")
        for sent, prob in zip(present_sentiments, normalized_probas):
            print(f"{sent}: {prob:.2f}%")
    else:
        print(f"\nText: {text}")
        print("No sentiments detected above thresholds.")

    return present_sentiments, probas




# Test Prediction with Best Model (Handles Ensembles)
import pandas as pd
import os
import joblib

# Check if summary_df exists, else load from CSV
try:
    summary_df
except NameError:
    summary_file = f'summary_{model_name_to_run}.csv'
    if os.path.exists(summary_file):
        summary_df = pd.read_csv(summary_file)
    else:
        raise FileNotFoundError(f"Summary file {summary_file} not reading. Run the '# Final Evaluation on Test Set' cell first.")

# Select the best model based on F1-Score (Macro)
best_model_row = summary_df.loc[summary_df['F1-Score (Macro)'].idxmax()]
best_model_name = best_model_row['Model']
best_feature_name = best_model_row['Feature']
print(f"\nBest Model: {best_model_name} with {best_feature_name} features")

# Test text for prediction
test_text = "এক সময় আফ্রিকা থেকে লক্ষ লক্ষ মানুষকে দাস বানিয়ে ইউরোপ ও আমেরিকায় নিয়ে যাওয়া হতো। তাদের পশুর মতো কেনাবেচা করা হতো, অমানবিক পরিশ্রম করানো হতো। এত অন্যায় আর নির্মমতা দেখে আজও রাগ হয়। মানব ইতিহাসের অন্যতম কলঙ্কময় অধ্যায় এটি।"
print(f"\nPredictions for Test Text with {best_model_name} ({best_feature_name}):")

# Select appropriate vectorizer
vectorizer = (bow_vectorizer, tfidf_vectorizer, char_vectorizer) if best_feature_name in ['Combined', 'Combined_SVM'] else \
             bow_vectorizer if best_feature_name in ['BoW', 'BoW_SVM'] else \
             tfidf_vectorizer if best_feature_name in ['TF-IDF', 'TF-IDF_SVM'] else char_vectorizer
is_combined = best_feature_name in ['Combined', 'Combined_SVM']

# Select appropriate embedding components
if best_feature_name == 'Word2Vec':
    embedding_model = word2vec_model
    scaler = word2vec_scaler
elif best_feature_name == 'FastText':
    embedding_model = fasttext_model
    scaler = fasttext_scaler
else:
    raise ValueError(f"Unsupported feature for prediction: {best_feature_name}")

# Check if ensemble (load if best is ensemble)
is_ensemble = best_model_name in ['Voting', 'Stacking', 'Hybrid']
if is_ensemble:
    ens_file = f'ensemble_{best_model_name}_models.pkl'
    if os.path.exists(ens_file):
        ensemble_models = joblib.load(ens_file)
        model = ensemble_models[best_feature_name]
        thresholds = ensemble_thresholds[best_feature_name]
        ensemble_type = model['type']
        print(f"Using ensemble type: {ensemble_type}")
    else:
        raise FileNotFoundError(f"Run ensemble {best_model_name} first.")
else:
    model = trained_models[best_model_name][best_feature_name]
    thresholds = best_thresholds[best_model_name][best_feature_name]
    ensemble_type = None

is_svm_feat = best_feature_name.endswith('_SVM')

# Predict sentiments
predict_sentiments(
    test_text,
    model,
    trained_models[best_model_name][best_feature_name],
    embedding_model,
    tfidf_weight,
    scaler,
    best_thresholds[best_model_name][best_feature_name],
    vectorizer,
    thresholds,
    sentiment_cols,
    is_combined,
    is_svm_feat,
    is_ensemble,
    ensemble_type,
    best_feature_name if is_ensemble else None
)

# Save Models, Vectorizers, and Scalers (Modified - Add Scaler Saving)
for model_name in trained_models:
    for feature_name in trained_models[model_name]:
        joblib.dump(trained_models[model_name][feature_name], f'model_{model_name}_{feature_name}.pkl')
joblib.dump(bow_vectorizer, 'bow_vectorizer.pkl')
joblib.dump(tfidf_vectorizer, 'tfidf_vectorizer.pkl')
joblib.dump(char_vectorizer, 'char_vectorizer.pkl')
joblib.dump(word2vec_model, 'word2vec_model.pkl')
joblib.dump(fasttext_model, 'fasttext_model.pkl')
joblib.dump(word2vec_scaler, 'word2vec_scaler.pkl')
joblib.dump(fasttext_scaler, 'fasttext_scaler.pkl')
joblib.dump(tfidf_weight, 'tfidf_weight.pkl')
joblib.dump(best_thresholds, 'best_thresholds.pkl')
for scaler_key in scalers:
    joblib.dump(scalers[scaler_key], f'scaler_{scaler_key}.pkl')

# Save ensembles (if run)
for ens in ['Voting', 'Stacking', 'Hybrid']:
    if os.path.exists(f'ensemble_{ens}_models.pkl'):
        print(f"Ensemble {ens} already saved.")


# 10. Compare All Models (Fixed - Aligns Ensemble Columns)
import os
import glob

model_names = ['RandomForest', 'XGBoost', 'LightGBM', 'SVM', 'LogisticRegression']
ensemble_names = ['Voting', 'Stacking', 'Hybrid']
summary_files = [f'summary_{name}.csv' for name in model_names] + [f'ensemble_summary_{ens}.csv' for ens in ensemble_names]
combined_summary = []

for file in summary_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        if 'Ensemble' in df.columns:
            df['Model'] = df['Ensemble']
            df['F1-Score (Macro)'] = df['F1-Macro']  # Align for barplot
            df['Hamming Loss'] = df['Hamming Loss']  # Already matches
            df['Feature'] = df['Feature']  # Keep
        combined_summary.append(df)
    else:
        print(f"Warning: {file} not found. Run the model/ensemble first.")

if combined_summary:
    combined_summary_df = pd.concat(combined_summary, ignore_index=True)
    print("\nCombined Model Comparison Summary:")
    print(combined_summary_df.sort_values(by='F1-Score (Macro)', ascending=False))

    plt.figure(figsize=(12, 6))
    sns.barplot(data=combined_summary_df, x='Model', y='F1-Score (Macro)', hue='Feature')
    plt.title('F1-Score (Macro) Comparison Across Models and Features')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()
else:
    print("\nNo summary files found. Please run all models/ensembles first.")
