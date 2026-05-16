
import numpy as np
import pandas as pd

from google.colab import drive
drive.mount('/content/drive')

df = pd.read_csv('/content/drive/MyDrive/MLL-2/spam.csv', encoding='latin-1')
# Try reading the file with the 'latin-1' encoding. If this doesn't work, try other encodings like 'ISO-8859-1'.

df.sample(5)

df.shape

# 1. Data cleaning
# 2. EDA
# 3. Text Preprocessing
# 4. Model building
# 5. Evaluation
# 6. Improvement

"""**1. Data Cleaning**"""

df.info()

df.drop(columns=['Unnamed: 2','Unnamed: 3','Unnamed: 4'],inplace=True)

df.sample(5)

# renaming the cols
df.rename(columns={'v1':'target','v2':'text'},inplace=True)
df.sample(5)

#level encoding
from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()

df['target'] = encoder.fit_transform(df['target'])

df.head()

# missing values
df.isnull().sum()

# check for duplicate values
df.duplicated().sum()

# remove duplicates
df = df.drop_duplicates(keep='first')

df.duplicated().sum()

df.shape

"""**2. EDA**"""

df.head()

df['target'].value_counts()

import matplotlib.pyplot as plt
plt.pie(df['target'].value_counts(), labels=['ham','spam'],autopct="%0.2f")
plt.show()

# Data is imbalanced

import nltk

!pip install nltk

nltk.download('punkt')

df['num_characters'] = df['text'].apply(len)

df.head()

# num of words
df['num_words'] = df['text'].apply(lambda x:len(nltk.word_tokenize(x)))

df.head()

df['num_sentences'] = df['text'].apply(lambda x:len(nltk.sent_tokenize(x)))

df.head()

df[['num_characters','num_words','num_sentences']].describe()

# ham
df[df['target'] == 0][['num_characters','num_words','num_sentences']].describe()

#spam
df[df['target'] == 1][['num_characters','num_words','num_sentences']].describe()

import seaborn as sns

plt.figure(figsize=(8,6))
sns.histplot(df[df['target'] == 0]['num_characters'])
sns.histplot(df[df['target'] == 1]['num_characters'],color='red')

plt.figure(figsize=(8,6))
sns.histplot(df[df['target'] == 0]['num_words'])
sns.histplot(df[df['target'] == 1]['num_words'],color='red')

sns.pairplot(df,hue='target')

#sns.heatmap(df.corr(),annot=True)
sns.heatmap(df.corr(numeric_only=True),annot=True)
# Set numeric_only to True to only include numerical columns in the correlation calculation.

"""**3. Data Preprocessing**

* Lower case
* Tokenization
* Removing special characters
* Removing stop words and punctuation
* Stemming
"""

!pip install nltk
import nltk
nltk.download('stopwords')
import string

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
ps = PorterStemmer()

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))


    return " ".join(y)

transform_text("I'm gonna be home soon and i don't want to talk about this stuff anymore tonight, k? I've cried enough today.")

df['transformed_text'] = df['text'].apply(transform_text)

df.head()

from wordcloud import WordCloud
wc = WordCloud(width=500,height=500,min_font_size=10,background_color='white')

spam_wc = wc.generate(df[df['target'] == 1]['transformed_text'].str.cat(sep=" "))

plt.figure(figsize=(8,6))
plt.imshow(spam_wc)

ham_wc = wc.generate(df[df['target'] == 0]['transformed_text'].str.cat(sep=" "))

plt.figure(figsize=(8,6))
plt.imshow(ham_wc)

df.head()

spam_corpus = []
for msg in df[df['target'] == 1]['transformed_text'].tolist():
    for word in msg.split():
        spam_corpus.append(word)

#spam_corpus
len(spam_corpus)

from collections import Counter
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

#Counter(spam_corpus)

# Convert the Counter output to a DataFrame
df_spam_corpus = pd.DataFrame(Counter(spam_corpus).most_common(30))

# Use the 'x' and 'y' keywords to specify the data
sns.barplot(x=df_spam_corpus[0], y=df_spam_corpus[1])

plt.xticks(rotation='vertical')
plt.show()

#from collections import Counter
#sns.barplot(pd.DataFrame(Counter(spam_corpus).most_common(30))[0],pd.DataFrame(Counter(spam_corpus).most_common(30))[1])
#plt.xticks(rotation='vertical')
#plt.show()

ham_corpus = []
for msg in df[df['target'] == 0]['transformed_text'].tolist():
    for word in msg.split():
        ham_corpus.append(word)

len(ham_corpus)

sns.barplot(x=pd.DataFrame(Counter(ham_corpus).most_common(30))[0],y=pd.DataFrame(Counter(ham_corpus).most_common(30))[1]) # Use keyword arguments x and y to specify data
plt.xticks(rotation='vertical')
plt.show()

# Text Vectorization
# using Bag of Words
df.head()

"""**4. Model Building**"""

from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer
cv = CountVectorizer()
tfidf = TfidfVectorizer(max_features=3000)

X = tfidf.fit_transform(df['transformed_text']).toarray()

#from sklearn.preprocessing import MinMaxScaler
#scaler = MinMaxScaler()
#X = scaler.fit_transform(X)


# appending the num_character col to X
#X = np.hstack((X,df['num_characters'].values.reshape(-1,1)))

X.shape

y = df['target'].values

from sklearn.model_selection import train_test_split

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=2)

from sklearn.naive_bayes import GaussianNB,MultinomialNB,BernoulliNB
from sklearn.metrics import accuracy_score,confusion_matrix,precision_score

gnb = GaussianNB()
mnb = MultinomialNB()
bnb = BernoulliNB()

gnb.fit(X_train,y_train)
y_pred1 = gnb.predict(X_test)
print(accuracy_score(y_test,y_pred1))
print(confusion_matrix(y_test,y_pred1))
print(precision_score(y_test,y_pred1))

mnb.fit(X_train,y_train)
y_pred2 = mnb.predict(X_test)
print(accuracy_score(y_test,y_pred2))
print(confusion_matrix(y_test,y_pred2))
print(precision_score(y_test,y_pred2))

bnb.fit(X_train,y_train)
y_pred3 = bnb.predict(X_test)
print(accuracy_score(y_test,y_pred3))
print(confusion_matrix(y_test,y_pred3))
print(precision_score(y_test,y_pred3))

# tfidf --> MNB

input_mail = input('Enter an Email:')
input_data_features = tfidf.transform([input_mail])
prediction = mnb.predict(input_data_features)
print(prediction)
if (prediction[0]==1):
  print("Spam")
else:
  print("Ham")

#input_mail = ["Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C's apply 08452810075over18's"]

#input_data_features = tfidf.transform(input_mail)
#prediction = mnb.predict(input_data_features)
#print(prediction)
#if (prediction[0]==1):
  #print("Spam mail")
#else:
  #print("Ham mail")

import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

cm = confusion_matrix(y_test, y_pred2)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Ham', 'Spam'])

disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix for Multinomial Naive Bayes')
plt.show()

from sklearn.metrics import classification_report

print(classification_report(y_test, y_pred2))

"""**Using vectorizer**"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# Dictionary to store metrics for bar chart
model_names = ["GaussianNB", "MultinomialNB", "BernoulliNB"]
accuracies = [accuracy_score(y_test, y_pred1), accuracy_score(y_test, y_pred2), accuracy_score(y_test, y_pred3)]
precisions = [precision_score(y_test, y_pred1), precision_score(y_test, y_pred2), precision_score(y_test, y_pred3)]

# Create subplots with two graphs in one row
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))

# Grouped Bar Chart for Accuracy and Precision on ax1
x = np.arange(len(model_names))  # label locations
width = 0.3  # width of bars

bars1 = ax1.bar(x - width/2, accuracies, width, label='Accuracy')
bars2 = ax1.bar(x + width/2, precisions, width, label='Precision')

ax1.set_xlabel("Model")
ax1.set_ylabel("Score")
ax1.set_title("Model Comparison: Accuracy and Precision")
ax1.set_xticks(x)
ax1.set_xticklabels(model_names)
ax1.legend()

# Adding value labels on top of bars
for bar in bars1 + bars2:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.01, round(yval, 2), ha="center", va="bottom")

# ROC-AUC Comparison Plot on ax2
for model, name in zip([gnb, mnb, bnb], model_names):
    y_prob = model.predict_proba(X_test)[:, 1]  # Get probability predictions
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    ax2.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.2f})")

ax2.plot([0, 1], [0, 1], 'k--')
ax2.set_xlabel("False Positive Rate")
ax2.set_ylabel("True Positive Rate")
ax2.set_title("ROC-AUC Comparison")
ax2.legend(loc="lower right")

plt.tight_layout()
plt.show()

"""**Using tfidf**"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# Dictionary to store metrics for bar chart
model_names = ["GaussianNB", "MultinomialNB", "BernoulliNB"]
accuracies = [accuracy_score(y_test, y_pred1), accuracy_score(y_test, y_pred2), accuracy_score(y_test, y_pred3)]
precisions = [precision_score(y_test, y_pred1), precision_score(y_test, y_pred2), precision_score(y_test, y_pred3)]

# Create subplots with two graphs in one row
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))

# Grouped Bar Chart for Accuracy and Precision on ax1
x = np.arange(len(model_names))  # label locations
width = 0.3  # width of bars

bars1 = ax1.bar(x - width/2, accuracies, width, label='Accuracy')
bars2 = ax1.bar(x + width/2, precisions, width, label='Precision')

ax1.set_xlabel("Model")
ax1.set_ylabel("Score")
ax1.set_title("Model Comparison: Accuracy and Precision")
ax1.set_xticks(x)
ax1.set_xticklabels(model_names)
ax1.legend()

# Adding value labels on top of bars
for bar in bars1 + bars2:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.01, round(yval, 2), ha="center", va="bottom")

# ROC-AUC Comparison Plot on ax2
for model, name in zip([gnb, mnb, bnb], model_names):
    y_prob = model.predict_proba(X_test)[:, 1]  # Get probability predictions
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    ax2.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.2f})")

ax2.plot([0, 1], [0, 1], 'k--')
ax2.set_xlabel("False Positive Rate")
ax2.set_ylabel("True Positive Rate")
ax2.set_title("ROC-AUC Comparison")
ax2.legend(loc="lower right")

plt.tight_layout()
plt.show()

#tring some other model comapring

#model comparion

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import BaggingClassifier

svc = SVC(kernel='sigmoid', gamma=1.0)
knc = KNeighborsClassifier()
mnb = MultinomialNB()
dtc = DecisionTreeClassifier(max_depth=5)
lrc = LogisticRegression(solver='liblinear', penalty='l1')
rfc = RandomForestClassifier(n_estimators=50, random_state=2)
abc = AdaBoostClassifier(n_estimators=50, random_state=2)
bc = BaggingClassifier(n_estimators=50, random_state=2)

clfs = {
    'SVC' : svc,
    'KN' : knc,
    'NB': mnb,
    'DT': dtc,
    'LR': lrc,
    'RF': rfc,
    'AdaBoost': abc,
    'BgC': bc
}

def train_classifier(clf,X_train,y_train,X_test,y_test):
    clf.fit(X_train,y_train)
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test,y_pred)
    precision = precision_score(y_test,y_pred)

    return accuracy,precision

train_classifier(svc,X_train,y_train,X_test,y_test)

accuracy_scores = []
precision_scores = []

for name,clf in clfs.items():

    current_accuracy,current_precision = train_classifier(clf, X_train,y_train,X_test,y_test)

    print("For ",name)
    print("Accuracy - ",current_accuracy)
    print("Precision - ",current_precision)

    accuracy_scores.append(current_accuracy)
    precision_scores.append(current_precision)

performance_df = pd.DataFrame({'Algorithm':clfs.keys(),'Accuracy':accuracy_scores,'Precision':precision_scores}).sort_values('Precision',ascending=False)

performance_df

performance_df1 = pd.melt(performance_df, id_vars = "Algorithm")

performance_df1

sns.catplot(x = 'Algorithm', y='value',
               hue = 'variable',data=performance_df1, kind='bar',height=4)
plt.ylim(0.5,1.0)
plt.xticks(rotation='vertical')
plt.show()

# model improve
# 1. Change the max_features parameter of TfIdf

temp_df = pd.DataFrame({'Algorithm':clfs.keys(),'Accuracy_max_ft_3000':accuracy_scores,'Precision_max_ft_3000':precision_scores}).sort_values('Precision_max_ft_3000',ascending=False)

temp_df = pd.DataFrame({'Algorithm':clfs.keys(),'Accuracy_scaling':accuracy_scores,'Precision_scaling':precision_scores}).sort_values('Precision_scaling',ascending=False)

new_df = performance_df.merge(temp_df,on='Algorithm')

new_df_scaled = new_df.merge(temp_df,on='Algorithm')

temp_df = pd.DataFrame({'Algorithm':clfs.keys(),'Accuracy_num_chars':accuracy_scores,'Precision_num_chars':precision_scores}).sort_values('Precision_num_chars',ascending=False)

new_df_scaled.merge(temp_df,on='Algorithm')

# Voting Classifier
svc = SVC(kernel='sigmoid', gamma=1.0,probability=True)
mnb = MultinomialNB()
rfc = RandomForestClassifier(n_estimators=50, random_state=2)

from sklearn.ensemble import VotingClassifier

voting = VotingClassifier(estimators=[('svm', svc), ('nb', mnb), ('rf', rfc)],voting='soft')

voting.fit(X_train,y_train)

y_pred = voting.predict(X_test)
print("Accuracy",accuracy_score(y_test,y_pred))
print("Precision",precision_score(y_test,y_pred))

# Applying stacking
estimators=[('svm', svc), ('nb', mnb), ('rf', rfc)]
final_estimator=RandomForestClassifier()

from sklearn.ensemble import StackingClassifier

clf = StackingClassifier(estimators=estimators, final_estimator=final_estimator)

clf.fit(X_train,y_train)
y_pred = clf.predict(X_test)
print("Accuracy",accuracy_score(y_test,y_pred))
print("Precision",precision_score(y_test,y_pred))