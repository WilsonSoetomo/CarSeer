from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
from datetime import datetime
import json
import math
import re
import aiohttp
import asyncio
import os
import statistics
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="CarSeer API", description="Car value prediction API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_model_name(model_name: str) -> str:
    """Normalize model name for consistent matching."""
    # Remove special characters and extra spaces
    model_name = re.sub(r'[^\w\s-]', '', model_name)
    # Convert to lowercase and replace multiple spaces with single space
    model_name = ' '.join(model_name.lower().split())
    return model_name

def find_matching_model(make: str, model: str) -> tuple[str, str]:
    """Find matching make and model in our database."""
    normalized_make = normalize_model_name(make)
    normalized_model = normalize_model_name(model)
    
    # Check for exact make match
    if normalized_make in [normalize_model_name(m) for m in BASE_VALUES.keys()]:
        actual_make = next(m for m in BASE_VALUES.keys() if normalize_model_name(m) == normalized_make)
        
        # Check for model match
        for actual_model in BASE_VALUES[actual_make].keys():
            if normalize_model_name(actual_model) == normalized_model:
                return actual_make, actual_model
            
    return None, None

# Base values for different car categories
BASE_VALUES = {
    "Luxury": {
        "Mercedes-Benz": {
            "S-Class": 95000,
            "E-Class": 65000,
            "C-Class": 45000,
            "G-Class": 130000,
            "SLS AMG": 250000,
            "AMG GT": 120000
        },
        "BMW": {
            "7 Series": 85000,
            "5 Series": 55000,
            "3 Series": 45000,
            "X7": 75000,
            "M8": 130000
        },
        "Audi": {
            "A8": 85000,
            "A6": 55000,
            "A4": 45000,
            "Q7": 65000,
            "RS e-tron GT": 140000
        }
    },
    "Super Luxury": {
        "Rolls-Royce": {
            "Phantom": 450000,
            "Ghost": 350000,
            "Cullinan": 400000
        },
        "Bentley": {
            "Continental GT": 200000,
            "Flying Spur": 250000,
            "Bentayga": 180000
        },
        "Aston Martin": {
            "DB11": 200000,
            "Vantage": 150000,
            "DBX": 180000
        }
    },
    "Exotic": {
        "Ferrari": {
            "F8": 280000,
            "SF90": 520000,
            "812": 340000
        },
        "Lamborghini": {
            "Huracan": 210000,
            "Aventador": 420000,
            "Urus": 230000
        },
        "McLaren": {
            "720S": 300000,
            "GT": 200000,
            "Artura": 225000
        }
    },
    "Premium": {
        "Lexus": {
            "LS": 75000,
            "ES": 45000,
            "RX": 55000
        },
        "Porsche": {
            "911": 110000,
            "Cayenne": 75000,
            "Panamera": 90000
        },
        "Tesla": {
            "Model S": 90000,
            "Model 3": 45000,
            "Model X": 100000
        }
    },
    "Mainstream": {
        "Toyota": {
            "Camry": 27000,
            "Corolla": 22000,
            "RAV4": 28000
        },
        "Honda": {
            "Accord": 27000,
            "Civic": 23000,
            "CR-V": 28000
        },
        "Ford": {
            "F-150": 35000,
            "Mustang": 30000,
            "Explorer": 35000
        }
    }
}

# Condition multipliers
CONDITION_MULTIPLIERS = {
    "Excellent": 1.1,
    "Good": 1.0,
    "Fair": 0.8,
    "Poor": 0.6
}

# Trim level multipliers
TRIM_MULTIPLIERS = {
    # Performance trims
    "AMG": 1.5,
    "M": 1.5,
    "RS": 1.4,
    "F": 1.3,
    "Type R": 1.3,
    "GT": 1.4,
    "Sport": 1.1,
    
    # Luxury trims
    "Premium": 1.2,
    "Luxury": 1.25,
    "Executive": 1.3,
    "Maybach": 2.0,
    
    # Base trims
    "Base": 1.0,
    "Standard": 1.0,
    "L": 1.0,
    
    # Special editions
    "Black Series": 2.0,
    "Competition": 1.6,
    "Limited": 1.15
}

class CarInput(BaseModel):
    make: str
    model: str
    trim: Optional[str] = None
    year: int
    mileage: Optional[float] = None
    condition: Optional[str] = None

class PredictionResponse(BaseModel):
    current_value: float
    predicted_values: List[dict]
    confidence_score: float

class CarDetails(BaseModel):
    make: str
    model: str
    trim: Optional[str] = None
    year: int
    mileage: Optional[float] = None
    condition: str = "Good"
    zip_code: Optional[str] = None

class MarketData:
    def __init__(self):
        # API Keys should be stored in environment variables
        self.kbb_api_key = os.getenv('KBB_API_KEY')
        self.cargurus_api_key = os.getenv('CARGURUS_API_KEY')
        self.nada_api_key = os.getenv('NADA_API_KEY')
        self.cars_com_api_key = os.getenv('CARS_COM_API_KEY')
        
        # API endpoints
        self.kbb_endpoint = "https://api.kbb.com/v1/values"
        self.cargurus_endpoint = "https://api.cargurus.com/v2/listings/search"
        self.nada_endpoint = "https://api.nadaguides.com/v2/values"
        self.cars_endpoint = "https://api.cars.com/v2/listings"

    async def get_kbb_value(self, session: aiohttp.ClientSession, car: CarDetails) -> Dict:
        """Fetch Kelley Blue Book value"""
        try:
            params = {
                'api_key': self.kbb_api_key,
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'mileage': car.mileage or 0,
                'condition': car.condition,
                'trim': car.trim
            }
            
            async with session.get(self.kbb_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'source': 'KBB',
                        'retail_value': data.get('retail', 0),
                        'private_party_value': data.get('privateParty', 0),
                        'trade_in_value': data.get('tradeIn', 0)
                    }
                return None
        except Exception as e:
            print(f"KBB API Error: {str(e)}")
            return None

    async def get_cargurus_listings(self, session: aiohttp.ClientSession, car: CarDetails) -> List[Dict]:
        """Fetch local market listings from CarGurus"""
        try:
            params = {
                'api_key': self.cargurus_api_key,
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'zip': car.zip_code or '90210',  # Default to Beverly Hills if no zip provided
                'radius': 100,  # 100 mile radius
                'maxMileage': car.mileage + 15000 if car.mileage else 100000
            }
            
            async with session.get(self.cargurus_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('listings', [])
                return []
        except Exception as e:
            print(f"CarGurus API Error: {str(e)}")
            return []

    async def get_nada_value(self, session: aiohttp.ClientSession, car: CarDetails) -> Dict:
        """Fetch NADA Guides value"""
        try:
            params = {
                'api_key': self.nada_api_key,
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'mileage': car.mileage or 0,
                'condition': car.condition,
                'trim': car.trim
            }
            
            async with session.get(self.nada_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'source': 'NADA',
                        'retail_value': data.get('retail', 0),
                        'trade_in_value': data.get('tradeIn', 0)
                    }
                return None
        except Exception as e:
            print(f"NADA API Error: {str(e)}")
            return None

    async def get_cars_com_listings(self, session: aiohttp.ClientSession, car: CarDetails) -> List[Dict]:
        """Fetch listings from Cars.com"""
        try:
            params = {
                'api_key': self.cars_com_api_key,
                'make': car.make,
                'model': car.model,
                'year': car.year,
                'zip': car.zip_code or '90210',
                'radius': 100,
                'max_mileage': car.mileage + 15000 if car.mileage else 100000
            }
            
            async with session.get(self.cars_endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('listings', [])
                return []
        except Exception as e:
            print(f"Cars.com API Error: {str(e)}")
            return []

    def calculate_market_value(self, kbb_data: Dict, nada_data: Dict, 
                             cargurus_listings: List[Dict], cars_listings: List[Dict]) -> Dict:
        """Calculate final market value using all available data sources"""
        values = []
        
        # Add KBB values if available
        if kbb_data:
            values.extend([
                kbb_data['retail_value'],
                kbb_data['private_party_value']
            ])
        
        # Add NADA values if available
        if nada_data:
            values.append(nada_data['retail_value'])
        
        # Add listing prices from CarGurus
        values.extend([listing['price'] for listing in cargurus_listings if listing.get('price')])
        
        # Add listing prices from Cars.com
        values.extend([listing['price'] for listing in cars_listings if listing.get('price')])
        
        if not values:
            raise ValueError("No market data available")
        
        # Calculate statistics
        median_value = statistics.median(values)
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        return {
            'predicted_value': round(median_value),  # Use median as the primary prediction
            'mean_value': round(mean_value),
            'std_dev': round(std_dev),
            'price_range': {
                'low': round(median_value - std_dev),
                'high': round(median_value + std_dev)
            },
            'sample_size': len(values),
            'sources': {
                'kbb': bool(kbb_data),
                'nada': bool(nada_data),
                'cargurus': len(cargurus_listings),
                'cars_com': len(cars_listings)
            }
        }

market_data = MarketData()

def calculate_depreciation(initial_value: float, age: int, mileage: Optional[float], condition: Optional[str]) -> float:
    # Base depreciation rate (yearly)
    base_rate = 0.15
    
    # Age-based depreciation
    age_factor = math.pow(1 - base_rate, age)
    
    # Mileage adjustment
    mileage_factor = 1.0
    if mileage:
        expected_mileage = age * 12000  # Average 12k miles per year
        mileage_diff = mileage - expected_mileage
        mileage_factor = 1.0 - (max(0, mileage_diff) * 0.00001)  # 1% per 1000 miles over expected
    
    # Condition adjustment
    condition_factors = {
        "Excellent": 1.1,
        "Good": 1.0,
        "Fair": 0.9,
        "Poor": 0.7
    }
    condition_factor = condition_factors.get(condition, 1.0)
    
    return initial_value * age_factor * mileage_factor * condition_factor

def get_car_category(make: str) -> str:
    """Determine the category of a car based on its make"""
    for category, makes in BASE_VALUES.items():
        if make in makes:
            return category
    return "Mainstream"

def get_base_value(make: str, model: str, year: int) -> float:
    """Get the base value for a car model with fallback calculations"""
    current_year = datetime.now().year
    age = current_year - year
    
    # Try to get the exact base value
    category = get_car_category(make)
    try:
        base_value = BASE_VALUES[category][make][model]
    except KeyError:
        # Fallback values based on category
        fallback_values = {
            "Luxury": 60000,
            "Super Luxury": 200000,
            "Exotic": 250000,
            "Premium": 50000,
            "Mainstream": 25000
        }
        base_value = fallback_values.get(category, 25000)
    
    # Apply age-based depreciation
    depreciation_rates = {
        "Luxury": 0.1,
        "Super Luxury": 0.08,
        "Exotic": 0.07,
        "Premium": 0.11,
        "Mainstream": 0.12
    }
    
    depreciation_rate = depreciation_rates.get(category, 0.12)
    depreciated_value = base_value * math.pow(1 - depreciation_rate, age)
    
    # Set minimum value as percentage of original value
    min_value_percent = {
        "Luxury": 0.2,
        "Super Luxury": 0.3,
        "Exotic": 0.4,
        "Premium": 0.15,
        "Mainstream": 0.1
    }
    
    min_value = base_value * min_value_percent.get(category, 0.1)
    return max(depreciated_value, min_value)

def get_trim_multiplier(trim: str) -> float:
    """Get the multiplier for a trim level"""
    if not trim:
        return 1.0
        
    # Check for exact match
    if trim in TRIM_MULTIPLIERS:
        return TRIM_MULTIPLIERS[trim]
    
    # Check for partial matches
    for known_trim, multiplier in TRIM_MULTIPLIERS.items():
        if known_trim.lower() in trim.lower():
            return multiplier
    
    return 1.0

def calculate_mileage_impact(mileage: float, category: str) -> float:
    """Calculate the impact of mileage on the car's value"""
    if not mileage:
        return 1.0
    
    # Different mileage thresholds and impacts based on category
    thresholds = {
        "Luxury": 100000,
        "Super Luxury": 50000,
        "Exotic": 30000,
        "Premium": 120000,
        "Mainstream": 150000
    }
    
    impacts = {
        "Luxury": 0.5,
        "Super Luxury": 0.6,
        "Exotic": 0.7,
        "Premium": 0.4,
        "Mainstream": 0.3
    }
    
    threshold = thresholds.get(category, 150000)
    impact = impacts.get(category, 0.3)
    
    return max(0.3, 1 - (mileage / threshold) * impact)

@app.get("/api/trims/{make}/{model}")
async def get_trims(make: str, model: str):
    try:
        # Basic trims for all cars
        basic_trims = ["Base", "Sport", "Premium", "Limited"]
        
        # Get car category
        category = get_car_category(make)
        
        # Category-specific trims
        category_trims = {
            "Luxury": ["Base", "Sport", "Premium", "Executive", "AMG", "M", "RS"],
            "Super Luxury": ["Base", "Extended", "Black Badge", "Mulliner", "First Edition"],
            "Exotic": ["Base", "Sport", "Performance", "Competition", "Spyder"],
            "Premium": ["Base", "Premium", "F-Sport", "Sport", "Turbo"],
            "Mainstream": ["L", "LE", "SE", "XLE", "Sport", "Limited"]
        }
        
        # Make-specific trims
        make_trims = {
            "Mercedes-Benz": ["Base", "AMG", "AMG Line", "Maybach"],
            "BMW": ["Base", "M Sport", "M", "M Competition"],
            "Audi": ["Base", "Premium", "Premium Plus", "Prestige", "S", "RS"],
            "Porsche": ["Base", "S", "GTS", "Turbo", "Turbo S"],
            "Ferrari": ["Base", "Pista", "Speciale"],
            "Lamborghini": ["Base", "Performante", "STO", "SVJ"],
            "Toyota": ["L", "LE", "XLE", "SE", "XSE", "TRD"],
            "Honda": ["LX", "Sport", "EX", "EX-L", "Touring"],
            "Ford": ["XL", "XLT", "Lariat", "Limited", "Platinum"]
        }
        
        # Combine and deduplicate trims
        all_trims = set(basic_trims)
        all_trims.update(category_trims.get(category, []))
        all_trims.update(make_trims.get(make, []))
        
        return {"trims": sorted(list(all_trims))}
        
    except Exception as e:
        print(f"Error getting trims: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to CarSeer API"}

@app.post("/predict")
async def predict_value(car: CarDetails):
    try:
        # Get car category
        category = get_car_category(car.make)
        
        # Get base value
        base_value = get_base_value(car.make, car.model, car.year)
        
        # Apply trim multiplier
        trim_multiplier = get_trim_multiplier(car.trim)
        
        # Apply condition multiplier
        condition_multiplier = CONDITION_MULTIPLIERS.get(car.condition, 1.0)
        
        # Apply mileage impact
        mileage_multiplier = calculate_mileage_impact(car.mileage, category)
        
        # Calculate final value
        predicted_value = base_value * trim_multiplier * condition_multiplier * mileage_multiplier
        
        # Calculate value range (±10% for mainstream, ±15% for luxury, ±20% for exotic)
        range_multipliers = {
            "Luxury": 0.15,
            "Super Luxury": 0.20,
            "Exotic": 0.20,
            "Premium": 0.12,
            "Mainstream": 0.10
        }
        
        range_multiplier = range_multipliers.get(category, 0.10)
        value_range = {
            "low": round(predicted_value * (1 - range_multiplier)),
            "high": round(predicted_value * (1 + range_multiplier))
        }
        
        # Round the final value to nearest hundred
        predicted_value = round(predicted_value / 100) * 100
        
        return {
            "predicted_value": predicted_value,
            "price_range": value_range,
            "category": category,
            "factors": {
                "base_value": round(base_value),
                "trim_multiplier": trim_multiplier,
                "condition_multiplier": condition_multiplier,
                "mileage_multiplier": mileage_multiplier
            },
            "confidence": "high" if car.make in BASE_VALUES.get(category, {}) else "medium",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 