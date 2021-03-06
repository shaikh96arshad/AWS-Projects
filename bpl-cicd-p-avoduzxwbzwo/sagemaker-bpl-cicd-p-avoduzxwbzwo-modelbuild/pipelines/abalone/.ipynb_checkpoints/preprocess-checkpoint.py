"""Feature engineers the abalone dataset."""
import argparse
import logging
import os
import pathlib
import requests
import tempfile

import boto3
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


# Since we get a headerless CSV file we specify the column names here.
feature_columns_names = [
    "Age",
    "Experience",
    "Income",
    "ZIP Code",
    "Family",
    "CCAvg",
    "Education",
    "Mortgage",
    "Personal Loan",
    "Securities Account",
    "CD Account",
    "Online",
    "CreditCard",
]
label_column = "Personal Loan"

feature_columns_dtype = {
    "Age": str,
    "Experience" : np.float64,
    "Income" : np.float64,
    "ZIP Code": np.float64,
    "Family" : np.float64,
    "CCAvg"  : np.float64,
    "Education" : np.float64,
    "Mortgage" : np.float64,
    "Personal Loan" : np.float64,
    "Securities Account" : np.float64,
    "CD Account" : np.float64,
    "Online" : np.float64,
    "CreditCard" : np.float64,
}
label_column_dtype = {"Personal Loan": np.float64}


def merge_two_dicts(x, y):
    """Merges two dicts, returning a new copy."""
    z = x.copy()
    z.update(y)
    return z


if __name__ == "__main__":
    logger.debug("Starting preprocessing.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", type=str, required=True)
    args = parser.parse_args()

    base_dir = "/opt/ml/processing"
    pathlib.Path(f"{base_dir}/data").mkdir(parents=True, exist_ok=True)
    input_data = args.input_data
    bucket = input_data.split("/")[2]
    key = "/".join(input_data.split("/")[3:])

    logger.info("Downloading data from bucket: %s, key: %s", bucket, key)
    fn = f"{base_dir}/data/Bank_Personal_Loan_Modelling.csv"
    s3 = boto3.resource("s3")
    s3.Bucket(bucket).download_file(key, fn)

    logger.debug("Reading downloaded data.")
    df = pd.read_csv(fn)
    os.unlink(fn)

    logger.debug("Defining transformers.")
    numeric_features = list(feature_columns_names)
    numeric_features.remove("ZIP Code")
    

    logger.info("Applying transforms.")
    y = df.pop("Personal Loan")
    X_pre = df
    y_pre = y.to_numpy().reshape(len(y), 1)

    X = np.concatenate((y_pre, X_pre), axis=1)

    logger.info("Splitting %d rows of data into train, validation, test datasets.", len(X))
    np.random.shuffle(X)
    train, validation, test = np.split(X, [int(0.7 * len(X)), int(0.85 * len(X))])

    logger.info("Writing out datasets to %s.", base_dir)
    pd.DataFrame(train).to_csv(f"{base_dir}/train/train.csv", header=False, index=False)
    pd.DataFrame(validation).to_csv(
        f"{base_dir}/validation/validation.csv", header=False, index=False
    )
    pd.DataFrame(test).to_csv(f"{base_dir}/test/test.csv", header=False, index=False)
