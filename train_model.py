import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

import os

DATA_PATH = "data/sample_cicids_like.csv"   # replace with CICIDS2017 cleaned csv
MODEL_PATH = "model/ids_model.pkl"


def main():
    df = pd.read_csv(DATA_PATH)

    # Features used (keep same columns in Flask prediction)
    feature_cols = [
        "Flow Duration",
        "Total Fwd Packets",
        "Total Backward Packets",
        "Flow Bytes/s",
        "Flow Packets/s",
        "Fwd Packet Length Mean",
        "Bwd Packet Length Mean",
        "Destination Port",
        "Protocol"
    ]

    X = df[feature_cols].fillna(0)
    y = df["Label"]

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)

    print("Model Accuracy:", acc)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    package = {
        "model": model,
        "scaler": scaler,
        "label_encoder": le,
        "feature_cols": feature_cols
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(package, f)

    print("Saved model to:", MODEL_PATH)

if __name__ == "__main__":
    main()