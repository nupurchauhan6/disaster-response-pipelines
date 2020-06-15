# importing libraries
import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.multioutput import MultiOutputClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.svm import LinearSVC
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report,accuracy_score
import warnings
warnings.filterwarnings("ignore")
import joblib
from sklearn.ensemble.forest import RandomForestClassifier

# downloading necessary NLTK data
import nltk
import re
nltk.download(['punkt', 'wordnet'])
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

def load_data(database_filepath):

    engine = create_engine('sqlite:///'+ database_filepath)
    df = pd.read_sql_table('dataset', engine)
    df = df.dropna()
    X = df.message.values
    Y = df.iloc[:,4:].values
    category_names = list(df.iloc[:,4:])
    return X, Y, category_names

def tokenize(text):

    # tokenize text
    text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    tokens = word_tokenize(text)
    
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model():

    svc = LinearSVC(random_state=0)
    multi_class_svc = OneVsRestClassifier(svc)
    multi_target_svc = MultiOutputClassifier(multi_class_svc)
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', multi_target_svc)
    ])
    parameters =  { 
      'tfidf__smooth_idf':[True, False],
      'clf__estimator__estimator__C': [0.001, 0.01, 0.1, 1, 10, 100]
    }
    print(pipeline.get_params().keys())
    cv = GridSearchCV(pipeline, parameters,refit = True,verbose=2,n_jobs = -1)
    return cv

def evaluate_model(model, X_test, Y_test, category_names):
    Y_pred = model.predict(X_test)
    for i, col in enumerate(category_names):
        print('{} category metrics: '.format(col))
        print(classification_report(Y_test[:,i], Y_pred[:,i]))

def save_model(model, model_filepath):
    joblib.dump(model, model_filepath)


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)

        print('Building model...')
        model = build_model()

        print('Training model...')
        model.fit(X_train, Y_train)

        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()