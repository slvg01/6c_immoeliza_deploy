import joblib
import numpy as np
import pandas as pd
import sklearn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Union

app = FastAPI()

DEFAULTS = {
    "num_features": {
        "construction_year": 2000,
        "latitude": 50.8503,
        "longitude": 4.3517,
        "total_area_sqm": 100.0,
        "surface_land_sqm": 500.0,
        "nbr_frontages": 2.0,
        "nbr_bedrooms": 3.0,
        "terrace_sqm": 10.0,
        "primary_energy_consumption_sqm": 250.0,
        "cadastral_income": 1000.0,
        "garden_sqm": 50.0,
        "zip_code": 1000
    },
    "fl_features": {
        "fl_terrace": 0,
        "fl_open_fire": 0,
        "fl_swimming_pool": 0,
        "fl_garden": 0,
        "fl_double_glazing": 1
    },
    "cat_features": {
        "subproperty_type": "APARTMENT",
        "locality": "Brussels",
        "equipped_kitchen": "NOT_INSTALLED",
        "state_building": "TO_RENOVATE",
        "epc": "MISSING"
    }
}

# Load model and artifacts once during startup
artifacts = joblib.load("model/Gradient_boost_artifacts.joblib")
imputer = artifacts["imputer"]
enc = artifacts["enc"]
model = artifacts["model"]

# Features class
class Features(BaseModel):
    num_features: Dict[str, float]
    fl_features: Dict[str, int]
    cat_features: Dict[str, str]

# Check function
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Immo Eliza ML model API!"}

# Predict function
@app.post("/predict")
async def predict(features: Features):
    # Fill in missing values with defaults
    filled_features = {
        "num_features": {**DEFAULTS["num_features"], **features.num_features},
        "fl_features": {**DEFAULTS["fl_features"], **features.fl_features},
        "cat_features": {**DEFAULTS["cat_features"], **features.cat_features},
    }
    
    # Now proceed with constructing DataFrame from filled_features
    num_df = pd.DataFrame([filled_features["num_features"]])
    fl_df = pd.DataFrame([filled_features["fl_features"]])
    cat_df = pd.DataFrame([filled_features["cat_features"]])

    # Process numerical features with imputer
    num_df = pd.DataFrame(imputer.transform(num_df), columns=num_df.columns)

    # Process categorical features with encoder
    if not cat_df.empty:
        cat_encoded = enc.transform(cat_df).toarray()
        cat_df = pd.DataFrame(cat_encoded, columns=enc.get_feature_names_out())

    # Combine all features
    data_df = pd.concat([num_df, fl_df, cat_df], axis=1)

    # Make predictions
    predictions = model.predict(data_df)
    
    return f"{predictions:.2f}"
    #return {"predictions": predictions.tolist()}