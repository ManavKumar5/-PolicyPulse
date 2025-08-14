import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "violation_model.pkl")
VECT_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "sample_data", "dataset.csv")


def train_model():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Sample dataset not found at {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    vect = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
    X = vect.fit_transform(df["text"].astype(str))
    y = df["label"].astype(int)
    clf = MultinomialNB()
    clf.fit(X, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(vect, VECT_PATH)
    return clf, vect


def load_model():
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECT_PATH):
        return train_model()
    clf = joblib.load(MODEL_PATH)
    vect = joblib.load(VECT_PATH)
    return clf, vect


if __name__ == "__main__":
    train_model()
