import pandas as pd
import numpy as np
from datetime import datetime
import requests
import time
import json
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CarDataCollector:
    def __init__(self):
        self.data_path = "data/car_prices.csv"
        os.makedirs("data", exist_ok=True)
        
        # API keys (you'll need to get these from respective services)
        self.cargurus_api_key = os.getenv('CARGURUS_API_KEY')
        self.cars_com_api_key = os.getenv('CARS_COM_API_KEY')
        
    async def collect_cargurus_data(self, make: str, model: str, year: int) -> List[Dict]:
        """Collect data from CarGurus API"""
        try:
            url = "https://api.cargurus.com/v2/listings/search"
            params = {
                'api_key': self.cargurus_api_key,
                'make': make,
                'model': model,
                'year': year,
                'zip': '90210',  # Default to Beverly Hills
                'radius': 500,  # 500 mile radius for more data
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('listings', [])
            return []
            
        except Exception as e:
            print(f"Error collecting CarGurus data: {str(e)}")
            return []
    
    async def collect_cars_com_data(self, make: str, model: str, year: int) -> List[Dict]:
        """Collect data from Cars.com API"""
        try:
            url = "https://api.cars.com/v2/listings"
            params = {
                'api_key': self.cars_com_api_key,
                'make': make,
                'model': model,
                'year': year,
                'zip': '90210',
                'radius': 500,
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('listings', [])
            return []
            
        except Exception as e:
            print(f"Error collecting Cars.com data: {str(e)}")
            return []
    
    def process_listing_data(self, listings: List[Dict]) -> pd.DataFrame:
        """Process raw listing data into a structured DataFrame"""
        processed_data = []
        
        for listing in listings:
            try:
                processed_listing = {
                    'make': listing.get('make', ''),
                    'model': listing.get('model', ''),
                    'trim': listing.get('trim', 'Base'),
                    'year': listing.get('year', 0),
                    'mileage': listing.get('mileage', 0),
                    'price': listing.get('price', 0),
                    'condition': listing.get('condition', 'Good'),
                    'listing_date': listing.get('listingDate', datetime.now().isoformat()),
                    'source': listing.get('source', 'unknown')
                }
                
                # Basic validation
                if all([processed_listing['make'], 
                       processed_listing['model'], 
                       processed_listing['year'],
                       processed_listing['price'] > 0]):
                    processed_data.append(processed_listing)
                    
            except Exception as e:
                print(f"Error processing listing: {str(e)}")
                continue
        
        return pd.DataFrame(processed_data)
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the collected data"""
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Remove outliers using IQR method
        Q1 = df['price'].quantile(0.25)
        Q3 = df['price'].quantile(0.75)
        IQR = Q3 - Q1
        df = df[~((df['price'] < (Q1 - 1.5 * IQR)) | (df['price'] > (Q3 + 1.5 * IQR)))]
        
        # Fill missing values
        df['trim'] = df['trim'].fillna('Base')
        df['condition'] = df['condition'].fillna('Good')
        df['mileage'] = df['mileage'].fillna(df.groupby(['make', 'model', 'year'])['mileage'].transform('median'))
        
        # Convert mileage to float if it's not already
        df['mileage'] = pd.to_numeric(df['mileage'], errors='coerce')
        
        # Normalize text fields
        df['make'] = df['make'].str.strip().str.title()
        df['model'] = df['model'].str.strip().str.title()
        df['trim'] = df['trim'].str.strip().str.title()
        df['condition'] = df['condition'].str.strip().str.title()
        
        return df
    
    def save_data(self, df: pd.DataFrame):
        """Save the collected data to CSV"""
        df.to_csv(self.data_path, index=False)
        print(f"Data saved to {self.data_path}")
    
    def load_data(self) -> pd.DataFrame:
        """Load the collected data from CSV"""
        if os.path.exists(self.data_path):
            return pd.read_csv(self.data_path)
        return pd.DataFrame()
    
    async def collect_data(self, makes: List[str], start_year: int = 2010):
        """Main method to collect car price data"""
        current_year = datetime.now().year
        years = range(start_year, current_year + 1)
        
        all_data = []
        
        for make in makes:
            print(f"Collecting data for {make}...")
            
            # Get models for this make
            try:
                models_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/getmodelsformake/{make}?format=json"
                response = requests.get(models_url)
                models_data = response.json()
                models = [model['Model_Name'] for model in models_data.get('Results', [])]
                
                for model in models:
                    print(f"Processing {make} {model}...")
                    
                    for year in years:
                        # Collect data from multiple sources
                        cargurus_listings = await self.collect_cargurus_data(make, model, year)
                        cars_com_listings = await self.collect_cars_com_data(make, model, year)
                        
                        # Process and combine data
                        all_listings = cargurus_listings + cars_com_listings
                        if all_listings:
                            df = self.process_listing_data(all_listings)
                            all_data.append(df)
                        
                        # Be nice to the APIs
                        time.sleep(1)
                
            except Exception as e:
                print(f"Error processing {make}: {str(e)}")
                continue
        
        # Combine all data
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df = self.clean_data(final_df)
            self.save_data(final_df)
            return final_df
        
        return pd.DataFrame()

# Create a global instance
collector = CarDataCollector() 