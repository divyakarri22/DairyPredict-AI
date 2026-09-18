import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle

# Load dataset
data = pd.read_csv("dataset/milk_data.csv")

# Encode breed
encoder = LabelEncoder()
data["breed"] = encoder.fit_transform(data["breed"])

# Input features
X = data[[
    "age",
    "breed",
    "milk",
    "feed",
    "water"
]]

# Target
y = data["milk"]

# Train model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

# Save model
with open("milk_model.pkl", "wb") as file:
    pickle.dump(model, file)

# Save breed encoder
with open("breed_encoder.pkl", "wb") as file:
    pickle.dump(encoder, file)

print("Improved milk prediction model trained successfully!")