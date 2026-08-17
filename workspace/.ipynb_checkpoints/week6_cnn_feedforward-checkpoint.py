# %% [markdown]
# # Lab 1: Feedforward Neural Network with ETIDS Manufacturing Data
# 
# ## Objective
# In this lab, students will build a Feedforward Neural Network using PyTorch and the project's manufacturing feature mart.
# 
# Instead of using MNIST image data, this lab uses data from:
# - `mart.feature_quality_model`
# 
# Students will learn how to:
# 1. Connect to the ETIDS PostgreSQL database
# 2. Load project data from the feature mart
# 3. Inspect schema before modeling
# 4. Prepare tabular data for neural network training
# 5. Build a Feedforward Neural Network in PyTorch
# 6. Train and evaluate the model
# 7. Interpret model performance carefully

# %% [markdown]
# ## Step 1: Install Required Libraries
# Run this inside the ETIDS Python/Jupyter environment if the packages are not already installed.

# %%
# !pip install torch pandas scikit-learn sqlalchemy psycopg2-binary matplotlib seaborn

# %% [markdown]
# ## Step 2: Import Required Libraries

# %%
import os
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# For visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seeds for reproducibility
np.random.seed(42)
torch.manual_seed(42)

print("Libraries imported successfully!")

# %% [markdown]
# ## Step 3: Connect to the ETIDS Project Database
# 
# **Docker Connection** - Using the specified connection string for the container environment.

# %%
# Docker container connection - Use this for Docker
DATABASE_URL = "postgresql+psycopg2://manufacturing:manufacturing@postgres:5432/manufacturing_dw"
engine = create_engine(DATABASE_URL)

print("Database connection created successfully!")
print(f"Connection URL: {DATABASE_URL}")

# Test the connection
try:
    with engine.connect() as conn:
        print("Connection test successful!")
except Exception as e:
    print(f"Connection failed: {e}")

# %% [markdown]
# ## Step 4: Inspect the Feature Mart Schema
# 
# Students must inspect the schema before modeling. Do not assume column names.

# %%
schema_query = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'mart'
  AND table_name = 'feature_quality_model'
ORDER BY ordinal_position;
"""

schema_df = pd.read_sql(schema_query, engine)
print("Schema Information:")
display(schema_df)

# %% [markdown]
# ## Step 5: Load Data from the Project Feature Mart

# %%
query = """
SELECT *
FROM mart.feature_quality_model;
"""

df = pd.read_sql(query, engine)

print(f"Shape: {df.shape}")
print("\nFirst 5 rows:")
display(df.head())

# %% [markdown]
# ### Check Missing Values

# %%
missing_values = df.isna().sum().sort_values(ascending=False)
missing_values_head = missing_values.head(20)
print("Missing Values (Top 20 columns):")
display(missing_values_head)

print(f"\nTotal missing values: {missing_values.sum()}")
print(f"Number of columns with missing values: {(missing_values > 0).sum()}")

# %% [markdown]
# ## Step 6: Select Target Column
# 
# The target column depends on the actual project schema. The code below tries common target names first. If none is found, students must manually set the target column based on the schema.

# %%
candidate_targets = [
    "quality_label",
    "defect_label",
    "defect_flag",
    "is_defective",
    "defective_flag",
    "quality_class",
    "target",
    "label",
    "class"
]

available_columns = df.columns.tolist()

TARGET_COLUMN = None

for col in candidate_targets:
    if col in available_columns:
        TARGET_COLUMN = col
        break

if TARGET_COLUMN is None:
    print("Available columns:")
    print(available_columns)
    
    # Manual selection - change this to the correct target column
    # For demonstration, let's find columns that might be targets
    possible_targets = [col for col in available_columns if 'flag' in col.lower() or 'label' in col.lower() or 'class' in col.lower()]
    print(f"\nPossible target columns based on naming: {possible_targets}")
    
    if possible_targets:
        TARGET_COLUMN = possible_targets[0]
        print(f"Automatically selected: {TARGET_COLUMN}")
    else:
        raise ValueError(
            "No default target column found. "
            "Please set TARGET_COLUMN manually based on the schema."
        )

print(f"Selected target column: {TARGET_COLUMN}")

# %% [markdown]
# ## Step 7: Prepare Features and Target
# 
# Remove ID, timestamp, and target columns from the feature matrix.

# %%
# Define patterns for columns to drop
drop_patterns = ["id", "date", "time", "timestamp", "created_at", "updated_at"]

drop_columns = [TARGET_COLUMN]

for col in df.columns:
    lower_col = col.lower()
    if any(pattern in lower_col for pattern in drop_patterns):
        if col != TARGET_COLUMN:
            drop_columns.append(col)

drop_columns = list(set(drop_columns))

X = df.drop(columns=drop_columns, errors="ignore")
y = df[TARGET_COLUMN]

print(f"Dropped columns: {drop_columns}")
print(f"Feature columns ({len(X.columns)} columns): {X.columns.tolist()}")
print(f"Target column: {TARGET_COLUMN}")

# %% [markdown]
# ### Handle Categorical Features

# %%
# Identify categorical columns
categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
print(f"Categorical columns: {categorical_cols}")

# Apply one-hot encoding
X = pd.get_dummies(X, drop_first=True)
print(f"Shape after one-hot encoding: {X.shape}")

# %% [markdown]
# ### Handle Missing Values

# %%
# Replace infinite values with NaN
X = X.replace([np.inf, -np.inf], np.nan)

# Fill NaN with median of each column
X = X.fillna(X.median(numeric_only=True))

print(f"Missing values after handling: {X.isna().sum().sum()}")

# %% [markdown]
# ### Encode Target

# %%
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y.astype(str))

print(f"Classes: {list(label_encoder.classes_)}")
print(f"Number of classes: {len(label_encoder.classes_)}")
print(f"Class distribution:")
for cls, count in zip(label_encoder.classes_, np.bincount(y_encoded)):
    print(f"  {cls}: {count} ({count/len(y_encoded)*100:.1f}%)")

# %% [markdown]
# ## Step 8: Train-Test Split and Scaling

# %%
# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded if len(np.unique(y_encoded)) > 1 else None
)

print(f"Training set size: {len(X_train)}")
print(f"Testing set size: {len(X_test)}")

# Scale features
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training shape: {X_train_scaled.shape}")
print(f"Testing shape: {X_test_scaled.shape}")

# %% [markdown]
# ## Step 9: Convert Data to PyTorch Tensors

# %%
X_train_tensor = torch.tensor(X_train_scaled, dtype=torch.float32)
X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)

y_train_tensor = torch.tensor(y_train, dtype=torch.long)
y_test_tensor = torch.tensor(y_test, dtype=torch.long)

train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
test_dataset = TensorDataset(X_test_tensor, y_test_tensor)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

print("PyTorch datasets created successfully!")
print(f"Number of training batches: {len(train_loader)}")
print(f"Number of testing batches: {len(test_loader)}")

# %% [markdown]
# ## Step 10: Define the Feedforward Neural Network
# 
# **Important:** Do not use Softmax inside the model when using CrossEntropyLoss. PyTorch CrossEntropyLoss expects raw logits.

# %%
class FeedforwardNN(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(FeedforwardNN, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, output_dim)
        )
    
    def forward(self, x):
        return self.network(x)

# %% [markdown]
# ## Step 11: Initialize Model, Loss Function, and Optimizer

# %%
input_dim = X_train_scaled.shape[1]
hidden_dim = 128
output_dim = len(label_encoder.classes_)

model = FeedforwardNN(
    input_dim=input_dim,
    hidden_dim=hidden_dim,
    output_dim=output_dim
)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

print(model)
print(f"\nInput dimension: {input_dim}")
print(f"Hidden dimension: {hidden_dim}")
print(f"Output dimension: {output_dim}")

# %% [markdown]
# ## Step 12: Train the Model

# %%
def train_model(model, dataloader, criterion, optimizer, epochs=20, verbose=True):
    model.train()
    history = {'train_loss': []}
    
    for epoch in range(epochs):
        total_loss = 0.0
        
        for x_batch, y_batch in dataloader:
            optimizer.zero_grad()
            
            outputs = model(x_batch)
            loss = criterion(outputs, y_batch)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(dataloader)
        history['train_loss'].append(avg_loss)
        
        if verbose:
            print(f"Epoch {epoch + 1:02d}/{epochs}, Loss: {avg_loss:.4f}")
    
    return history

# Run training
print("Starting training...")
history = train_model(
    model=model,
    dataloader=train_loader,
    criterion=criterion,
    optimizer=optimizer,
    epochs=20
)
print("Training completed!")

# %% [markdown]
# ### Plot Training Loss

# %%
plt.figure(figsize=(10, 6))
plt.plot(history['train_loss'])
plt.title('Training Loss Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.grid(True)
plt.show()

# %% [markdown]
# ## Step 13: Evaluate the Model

# %%
def evaluate_model(model, dataloader):
    model.eval()
    
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for x_batch, y_batch in dataloader:
            outputs = model(x_batch)
            predictions = torch.argmax(outputs, dim=1)
            
            all_predictions.extend(predictions.numpy())
            all_targets.extend(y_batch.numpy())
    
    accuracy = accuracy_score(all_targets, all_predictions)
    
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(
        classification_report(
            all_targets,
            all_predictions,
            target_names=label_encoder.classes_,
            zero_division=0
        )
    )
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(all_targets, all_predictions))
    
    return accuracy, all_predictions, all_targets

# Run evaluation
accuracy, predictions, targets = evaluate_model(model, test_loader)

# %% [markdown]
# ## Step 14: Compare Actual vs Predicted Results

# %%
results_df = pd.DataFrame({
    "actual": label_encoder.inverse_transform(targets),
    "predicted": label_encoder.inverse_transform(predictions)
})

print("First 20 predictions vs actual:")
display(results_df.head(20))

# %%
# Additional analysis - misclassifications
misclassified = results_df[results_df['actual'] != results_df['predicted']]
print(f"\nNumber of misclassifications: {len(misclassified)}")
print(f"Misclassification rate: {len(misclassified)/len(results_df)*100:.2f}%")

if len(misclassified) > 0:
    print("\nFirst 10 misclassifications:")
    display(misclassified.head(10))

# %% [markdown]
# ### Visualize Confusion Matrix

# %%
# Calculate confusion matrix
cm = confusion_matrix(targets, predictions)

# Create heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_)
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.show()

# %% [markdown]
# ## Step 15: Save the Trained Model

# %%
# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

model_path = "models/lecture6_fnn_quality_model.pt"

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "output_dim": output_dim,
        "feature_columns": X.columns.tolist(),
        "target_column": TARGET_COLUMN,
        "classes": label_encoder.classes_.tolist(),
        "scaler": scaler,  # Save the scaler for inference
    },
    model_path
)

print(f"Model saved as {model_path}")

# %% [markdown]
# ## Additional Analysis: Model Performance Summary

# %%
print("="*50)
print("MODEL PERFORMANCE SUMMARY")
print("="*50)

print(f"Target Column: {TARGET_COLUMN}")
print(f"Number of Features: {input_dim}")
print(f"Number of Classes: {output_dim}")
print(f"Classes: {label_encoder.classes_.tolist()}")
print(f"Training Samples: {len(X_train)}")
print(f"Testing Samples: {len(X_test)}")
print(f"Test Accuracy: {accuracy:.4f}")

# Calculate per-class accuracy
from sklearn.metrics import precision_recall_fscore_support

precision, recall, f1, support = precision_recall_fscore_support(
    targets, predictions, average=None, zero_division=0
)

print("\nPer-Class Metrics:")
for i, class_name in enumerate(label_encoder.classes_):
    print(f"  {class_name}:")
    print(f"    Precision: {precision[i]:.4f}")
    print(f"    Recall: {recall[i]:.4f}")
    print(f"    F1-Score: {f1[i]:.4f}")
    print(f"    Support: {support[i]}")

print("\nModel saved successfully!")

# %% [markdown]
# ## Inference Example: Using the Saved Model

# %%
# Example of how to load and use the saved model
def load_model(model_path):
    checkpoint = torch.load(model_path)
    
    model = FeedforwardNN(
        input_dim=checkpoint['input_dim'],
        hidden_dim=checkpoint['hidden_dim'],
        output_dim=checkpoint['output_dim']
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    
    return model, checkpoint['scaler'], checkpoint['feature_columns']

# Load the model
loaded_model, loaded_scaler, feature_columns = load_model(model_path)
print("Model loaded successfully!")

print(f"\nModel info:")
print(f"  Input dimension: {input_dim}")
print(f"  Hidden dimension: {hidden_dim}")
print(f"  Output dimension: {output_dim}")
print(f"  Number of features: {len(feature_columns)}")

print("\nReady for inference!")

# %%
print("="*50)
print("LAB COMPLETED SUCCESSFULLY")
print("="*50)