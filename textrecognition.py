# -*- coding: utf-8 -*-
"""textRecognition.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19Jyr0fPFHdaf8W4ghNxG5cqge4MOy3rB
"""

import os
import sys
import csv
import pandas as pd
import matplotlib as plt
import numpy as np
from sklearn.preprocessing import LabelEncoder
import seaborn as sns

""" ## Data Acquisition



"""

def downloadDataset():
  if  not os.path.isfile('./QS-OCR-small.tar.gz'):
    print("Downloading... ")
    ! wget https://github.com/QuickSign/ocrized-text-dataset/releases/download/v1.0/QS-OCR-small.tar.gz -P ./
    !mkdir dataset
    !tar -xf QS-OCR-small.tar.gz -C ./dataset
  else: 
    print("Dataset has already been downloaded. ")

def createSingleDataset():
  # join all the file content into a single csv file
  if not os.path.isfile('./dataset.csv'):
    print("joining..")
    path = "./dataset"
    file_dataset = open('dataset.csv', mode='w')
    file_writer = csv.writer(file_dataset, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #walk trough the directory to get all the files' content
    for dirpath, dirs, filenames in os.walk(path):
      for filename in filenames:
        f = open(dirpath +"/"+filename, "r")
        getfilebody = f.read()
        file_writer.writerow([filename, getfilebody,  dirpath.replace("./dataset/", "") ] )
        f.close()
  else:
      print("Dataset files have already been joined. ")

downloadDataset()
createSingleDataset()

import tensorflow as tf
tf.test.gpu_device_name()

"""##Pre-Processing
Data cleaning:
  >* filling in missing values,
  >*  smoothing noisy data,
  >* identifying or removing outliers,
  >* resolving inconsistencies,
  >* duplicate samples
  >* NLP pipeline = data normalizzation for text
  >>* Tokenization
  >>* punctuation removal
  >>* stop words removal
  >>* noise removal: Remove HTML tags, remove extra whitespaces, 
  >>* normalization: typo correction,  converting all characters to lowercase, number, date, symbol textualization, Expand contractions, remove_accented_chars
  >>* lemmatization o steaming 

"""

df = pd.read_csv("dataset.csv", sep='|', delimiter=None, names = ["filename","content", "label"] )
df.dropna

#label encoding
categories = pd.unique(df["label"])

labelencoder = LabelEncoder()

df['y'] = labelencoder.fit_transform(df['label'])
df

!pip install langid
import spacy 
import en_core_web_sm
import langid
import re as re

def remove_tags(string):
    result = re.sub('<.*?>',' ',string)
    return result

def clean_text(text):
  for t in nlp.tokenizer(text):
    if ((not t.is_stop) and ( not t.is_punct) and (not t.is_currency) and (not t.is_digit) and (not t.is_space) and (t.is_alpha) ):
      return t.lemma_.lower().join(t.pos_)

def execute_nlp(df):
  nlp = spacy.load('en')  
  #speech tag is slow
  #df['tagged_text'] = df['content_without_tags'].apply(lambda x: [t.pos_ for t in nlp(x) if ((not t.is_stop) and ( not t.is_punct) and (not t.is_currency) and (not t.is_digit) and (not t.is_space) and (t.is_alpha) ) ])
  df.insert(1, 'cleaned_text', df['content_without_tags'].apply(lambda x: [t.lemma_.lower() for t in nlp.tokenizer(x) if ((not t.is_stop) and ( not t.is_punct) and (not t.is_currency) and (not t.is_digit) and (not t.is_space) and (t.is_alpha) ) ]))
  return df

df['content']=df['content'].apply(str)
df.insert(1, 'content_without_tags', df["content"].apply(lambda cw : remove_tags(cw)))  

df = execute_nlp(df)

df = df.drop("content_without_tags", axis = 1)
df = df.drop("filename", axis = 1)

nlp = spacy.load('en')  

prova = nlp("ciao come stai? ")
prova
for token in prova: 
  print(token.text, ': ', token.pos_)
 #df['cleaned_text'].apply(lambda x: [t.pos for t in x  ])

"""## Visualization and Dataset Analysis"""

df

categoryDistribution = df.groupby(["label"])["content"].count()
plt.pyplot.bar(categories, categoryDistribution, width = 0.8, bottom=None, align='center', data=None)

#visualize mean of sentence lenght for each category
df['number_of_words'] = df.cleaned_text.apply(lambda x: len(x))
mean_words_for_sentence = df.groupby("label")["number_of_words"].mean()
plt.pyplot.bar(categories, mean_words_for_sentence, width = 0.8, bottom=None, align='center', data=None)

zero_lenght = df.loc[df.number_of_words == 0]
zero_lenght
#remove zero lenght documents?

!sudo pip install imbalanced-learn
oversample = RandomOverSampler(sampling_strategy='minority')

"""## Baseline Model """

## for bag-of-words
from sklearn import feature_extraction, model_selection, manifold, preprocessing, feature_selection
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

df['cleaned_text'] = df['cleaned_text'].apply(lambda x: ','.join(map(str, x)))

## split dataset
X = df["cleaned_text"]
y = df["label"]
X_train, X_test, y_train, y_test= model_selection.train_test_split(X, y, test_size=0.3, random_state = 42)

#categories = ['ADVE','Email','Form','Letter','Memo','News','Note','Report','Resume','Scientific']

def multinomialNBmodel():
  nb = Pipeline([('vectorizer', feature_extraction.text.CountVectorizer()),
                ('tfidf', feature_extraction.text.TfidfTransformer()),
               ('clf', MultinomialNB()),])
  #nb.fit(X_train, y_train)
  return nb
def SVMmodel():
  svm = Pipeline([('vectorizer', feature_extraction.text.CountVectorizer()),
              #  ('tfidf', feature_extraction.text.TfidfTransformer()),
               ('clf',  SGDClassifier(penalty='l2', alpha=1e-3, random_state=42)),])
  #nb.fit(X_train, y_train)
  return svm

def getPerformanceMetrics(model):
  from sklearn.metrics import classification_report, accuracy_score,confusion_matrix,roc_curve,auc,precision_recall_curve
  y_pred = model.predict(X_test)
  #predicted_prob = model.predict_proba(X_test)
  print('accuracy %s' % accuracy_score(y_pred, y_test))
  print(classification_report(y_test, y_pred, target_names=categories))
   ## Plot confusion matrix
  cm = confusion_matrix(y_test, y_pred)
  fig, ax = plt.pyplot.subplots()
  sns.heatmap(cm, annot=True, fmt='d', ax=ax, cmap=plt.cm.Blues, 
              cbar=False)
  ax.set(xlabel="Pred", ylabel="True", xticklabels=categories, 
        yticklabels=categories, title="Confusion matrix")
  plt.pyplot.yticks(rotation=0)
  fig, ax = plt.pyplot.subplots(nrows=1, ncols=2)
  ## Plot roc
  """y_test_array = pd.get_dummies(y_test, drop_first=False).values
  for i in range(len(categories)):
      fpr, tpr, thresholds = roc_curve(y_test_array[:,i],  
                            predicted_prob[:,i])
      ax[0].plot(fpr, tpr, lw=3, 
                label='{0} (area={1:0.2f})'.format(categories[i], 
                                auc(fpr, tpr))
                )
  ax[0].plot([0,1], [0,1], color='navy', lw=3, linestyle='--')
  ax[0].set(xlim=[-0.05,1.0], ylim=[0.0,1.05], 
            xlabel='False Positive Rate', 
            ylabel="True Positive Rate (Recall)", 
            title="Receiver operating characteristic")
  ax[0].legend(loc="lower right")
  ax[0].grid(True)
      
  ## Plot precision-recall curve
   for i in range(len(categories)):
      precision, recall, thresholds = precision_recall_curve(
                  y_test_array[:,i], predicted_prob[:,i])
      ax[1].plot(recall, precision, lw=3, 
                label='{0} (area={1:0.2f})'.format(categories[i], 
                                    auc(recall, precision))
                )
  ax[1].set(xlim=[0.0,1.05], ylim=[0.0,1.05], xlabel='Recall', 
            ylabel="Precision", title="Precision-Recall curve")
  ax[1].legend(loc="best")
  ax[1].grid(True)
  plt.pyplot.show()"""
 

#NOTE: with tfidf there are label that are not predicted

#model = multinomialNBmodel()
model = SVMmodel()
model.fit(X_train, y_train)

getPerformanceMetrics(model)

#TO DO: tuning of parameters with searchgrid

"""## Improvement"""