import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from datetime import datetime
import joblib
import os
from typing import Dict, List, Tuple, Optional

class CarPriceNN(nn.Module):
    def __init__(self, input_size: int):
        super(CarPriceNN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
        
    def forward(self, x):
        return self.network(x)

class CarPricePredictor:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = "models/car_price_model.pth"
        self.preprocessor_path = "models/preprocessor.joblib"
        
        # Create models directory if it doesn't exist
        os.makedirs("models", exist_ok=True)
        
        # Try to load model if exists, but don't fail if it doesn't
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.preprocessor_path):
                self.load_model()
        except Exception as e:
            print(f"Warning: Could not load existing model: {str(e)}")
            self.model = None
            self.preprocessor = None
    
    def create_preprocessor(self, categorical_features: List[str], numerical_features: List[str]) -> ColumnTransformer:
        """Create a preprocessor for the input features"""
        numeric_transformer = StandardScaler()
        categorical_transformer = OneHotEncoder(drop='first', sparse=False)
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numerical_features),
                ('cat', categorical_transformer, categorical_features)
            ])
        
        return preprocessor
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[torch.Tensor, torch.Tensor]:
        """Prepare the data for training"""
        # Define feature columns
        categorical_features = ['make', 'model', 'trim', 'condition']
        numerical_features = ['year', 'mileage']
        
        # Create and fit preprocessor if not exists
        if self.preprocessor is None:
            self.preprocessor = self.create_preprocessor(categorical_features, numerical_features)
            self.preprocessor.fit(df[categorical_features + numerical_features])
        
        # Transform features
        X = self.preprocessor.transform(df[categorical_features + numerical_features])
        y = df['price'].values
        
        # Convert to PyTorch tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.FloatTensor(y).reshape(-1, 1)
        
        return X_tensor, y_tensor
    
    def train(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.001):
        """Train the neural network model"""
        X_tensor, y_tensor = self.prepare_data(df)
        
        # Create model if not exists
        if self.model is None:
            input_size = X_tensor.shape[1]
            self.model = CarPriceNN(input_size).to(self.device)
        
        # Create data loader
        dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Define loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Training loop
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward pass
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                
                # Backward pass and optimize
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(dataloader):.4f}')
        
        # Save the model and preprocessor
        self.save_model()
    
    def predict(self, car_details: Dict) -> Dict[str, float]:
        """Predict the price for a single car"""
        if self.model is None or self.preprocessor is None:
            # Return a default prediction if model is not trained
            base_price = 30000  # Default base price
            return {
                "predicted_value": base_price,
                "price_range": {
                    "low": base_price * 0.9,
                    "high": base_price * 1.1
                },
                "confidence": "low",
                "timestamp": datetime.now().isoformat(),
                "note": "Model not trained yet. Using default values."
            }
        
        # Create a DataFrame with the car details
        df = pd.DataFrame([car_details])
        
        # Transform the input
        try:
            X = self.preprocessor.transform(df)
            X_tensor = torch.FloatTensor(X).to(self.device)
            
            # Make prediction
            self.model.eval()
            with torch.no_grad():
                predicted_price = self.model(X_tensor).cpu().numpy()[0][0]
            
            # Calculate confidence interval (using 10% range for demonstration)
            confidence_range = predicted_price * 0.1
            
            return {
                "predicted_value": round(predicted_price, 2),
                "price_range": {
                    "low": round(predicted_price - confidence_range, 2),
                    "high": round(predicted_price + confidence_range, 2)
                },
                "confidence": "high" if car_details['make'] in df.columns else "medium",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error making prediction: {str(e)}")
            base_price = 30000  # Default base price
            return {
                "predicted_value": base_price,
                "price_range": {
                    "low": base_price * 0.9,
                    "high": base_price * 1.1
                },
                "confidence": "low",
                "timestamp": datetime.now().isoformat(),
                "note": f"Error making prediction: {str(e)}"
            }
    
    def save_model(self):
        """Save the model and preprocessor"""
        torch.save(self.model.state_dict(), self.model_path)
        joblib.dump(self.preprocessor, self.preprocessor_path)
    
    def load_model(self):
        """Load the model and preprocessor"""
        self.preprocessor = joblib.load(self.preprocessor_path)
        
        # Create and load the model
        sample_input_size = len(self.preprocessor.get_feature_names_out())
        self.model = CarPriceNN(sample_input_size).to(self.device)
        self.model.load_state_dict(torch.load(self.model_path))
        self.model.eval()

# Create a global instance
predictor = CarPricePredictor() 