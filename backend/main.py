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
from ml_model import predictor

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

# API Keys from environment variables - only load what we have
CARMD_API_KEY = os.getenv('CARMD_API_KEY')
CARMD_AUTHORIZATION = os.getenv('CARMD_AUTHORIZATION')
EDMUNDS_API_KEY = os.getenv('EDMUNDS_API_KEY')

# MarketCheck configuration
MARKETCHECK_API_KEY = os.getenv('API_KEY')
if not MARKETCHECK_API_KEY:
    raise ValueError("MarketCheck API key not found in environment variables")

NHTSA_API_BASE = 'https://vpic.nhtsa.dot.gov/api'

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
            "A-Class": 35000,
            "C-Class": 44000,
            "E-Class": 57000,
            "S-Class": 115000,
            "EQS": 105000,
            "G-Class": 140000,
            "GLE": 57000,
            "GLS": 78000,
            "AMG GT": 95000,
            "AMG GT 4-Door": 140000,
            "SL": 138000,
            "AMG ONE": 2700000
        },
        "BMW": {
            "2 Series": 38000,
            "3 Series": 48000,
            "4 Series": 47000,
            "5 Series": 55000,
            "7 Series": 95000,
            "8 Series": 85000,
            "X3": 46000,
            "X5": 65000,
            "X7": 77000,
            "XM": 159000,
            "M2": 63000,
            "M3": 73000,
            "M4": 74000,
            "M5": 108000,
            "M8": 130000,
            "iX": 87000
        },
        "Audi": {
            "A3": 35000,
            "A4": 40000,
            "A6": 56000,
            "A8": 87000,
            "Q3": 36000,
            "Q5": 44000,
            "Q7": 58000,
            "Q8": 71000,
            "e-tron GT": 106000,
            "RS e-tron GT": 143000,
            "RS3": 59000,
            "RS6 Avant": 119000,
            "RS7": 121000,
            "R8": 158000
        }
    },
    "Super Luxury": {
        "Rolls-Royce": {
            "Phantom": 460000,
            "Ghost": 375000,
            "Cullinan": 355000,
            "Spectre": 420000,
            "Dawn": 380000,
            "Boat Tail": 28000000
        },
        "Bentley": {
            "Continental GT": 225000,
            "Flying Spur": 215000,
            "Bentayga": 190000,
            "Bentayga EWB": 226000,
            "Batur": 2000000,
            "Bacalar": 1800000
        },
        "Aston Martin": {
            "DB12": 245000,
            "DBS": 330000,
            "DBX": 185000,
            "DBX707": 236000,
            "Vantage": 150000,
            "Valkyrie": 3000000,
            "Valkyrie AMR Pro": 4000000,
            "Valhalla": 800000
        }
    },
    "Exotic": {
        "Ferrari": {
            "296 GTB": 322000,
            "296 GTS": 367000,
            "SF90 Stradale": 520000,
            "SF90 Spider": 570000,
            "F8 Tributo": 280000,
            "F8 Spider": 302000,
            "812 Competizione": 601000,
            "812 Competizione A": 670000,
            "Daytona SP3": 2250000,
            "Purosangue": 400000,
            "LaFerrari": 3500000,
            "Monza SP1": 1800000,
            "Monza SP2": 1800000
        },
        "Lamborghini": {
            "Huracan STO": 330000,
            "Huracan Tecnica": 245000,
            "Huracan Sterrato": 270000,
            "Revuelto": 610000,
            "Urus S": 230000,
            "Urus Performante": 265000,
            "Countach LPI 800-4": 2640000,
            "Sian FKP 37": 3600000,
            "Sian Roadster": 3700000
        },
        "McLaren": {
            "Artura": 237000,
            "720S": 310000,
            "765LT": 382000,
            "750S": 330000,
            "GT": 200000,
            "Elva": 1700000,
            "Senna": 1000000,
            "Speedtail": 2200000,
            "Solus GT": 3500000
        },
        "Bugatti": {
            "Chiron": 3300000,
            "Chiron Super Sport": 3825000,
            "Chiron Super Sport 300+": 4300000,
            "Chiron Pur Sport": 4000000,
            "Mistral": 5000000,
            "Bolide": 4700000,
            "Divo": 5800000,
            "Centodieci": 9000000,
            "La Voiture Noire": 18500000
        },
        "Pagani": {
            "Huayra R": 3100000,
            "Huayra Roadster BC": 3500000,
            "Huayra Codalunga": 7400000,
            "Utopia": 2200000,
            "Zonda HP Barchetta": 17600000
        },
        "Koenigsegg": {
            "Jesko": 3000000,
            "Jesko Absolut": 3400000,
            "Gemera": 1900000,
            "CC850": 3650000,
            "Regera": 2000000,
            "Agera RS": 2100000
        },
        "Rimac": {
            "Nevera": 2400000,
            "Concept_One": 1000000
        }
    },
    "Premium": {
        "Lexus": {
            "IS": 40000,
            "ES": 42000,
            "LS": 77000,
            "NX": 39000,
            "RX": 48000,
            "LX": 88000,
            "LC": 94000,
            "LC Convertible": 102000,
            "RZ": 59000,
            "LFA": 450000
        },
        "Porsche": {
            "718 Cayman": 63000,
            "718 Boxster": 65000,
            "911 Carrera": 107000,
            "911 GT3": 170000,
            "911 GT3 RS": 225000,
            "911 Turbo S": 208000,
            "Taycan": 88000,
            "Panamera": 92000,
            "Cayenne": 72000,
            "Macan": 58000,
            "918 Spyder": 1800000,
            "Carrera GT": 1200000
        },
        "Tesla": {
            "Model 3": 40000,
            "Model Y": 47000,
            "Model S": 88000,
            "Model X": 98000,
            "Roadster": 200000,
            "Cybertruck": 60000
        },
        "Lucid": {
            "Air Pure": 78000,
            "Air Touring": 96000,
            "Air Grand Touring": 126000,
            "Air Sapphire": 250000
        },
        "Rivian": {
            "R1T": 73000,
            "R1S": 78000
        }
    },
    "Mainstream": {
        "Toyota": {
            "Corolla": 21000,
            "Camry": 26000,
            "RAV4": 27000,
            "Highlander": 36000,
            "Supra": 45000,
            "Tundra": 37000,
            "Prius": 28000,
            "Crown": 41000,
            "GR Corolla": 36000,
            "bZ4X": 43000
        },
        "Honda": {
            "Civic": 23000,
            "Accord": 27000,
            "CR-V": 27000,
            "Pilot": 36000,
            "Ridgeline": 38000,
            "Odyssey": 33000,
            "Civic Type R": 43000,
            "NSX Type S": 171000
        },
        "Ford": {
            "Mustang": 30000,
            "F-150": 34000,
            "F-150 Lightning": 52000,
            "Bronco": 31000,
            "Explorer": 36000,
            "Mach-E": 46000,
            "GT": 500000
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
    "AMG": 1.4,
    "M": 1.35,
    "RS": 1.35,
    "GT": 1.3,
    "Type R": 1.3,
    "Sport": 1.15,
    "S": 1.25,
    "Competition": 1.35,
    "Performance": 1.25,
    "F Sport": 1.2,
    
    # Luxury trims
    "Premium": 1.15,
    "Luxury": 1.2,
    "Elite": 1.25,
    "Platinum": 1.3,
    "Limited": 1.2,
    "Ultimate": 1.35,
    "Prestige": 1.25,
    
    # Special editions
    "Black Edition": 1.4,
    "Launch Edition": 1.5,
    "Anniversary Edition": 1.45,
    "Special Edition": 1.35,
    
    # Base and standard trims
    "Base": 1.0,
    "Standard": 1.0,
    "L": 1.0,
    "LE": 1.05,
    "SE": 1.1,
    "XLE": 1.15,
    "XSE": 1.2,
    "LX": 1.0,
    "EX": 1.1,
    "EX-L": 1.15,
    "Touring": 1.2,
    "XL": 1.0,
    "XLT": 1.1,
    "Lariat": 1.2,
    "King Ranch": 1.3,
    
    # Electric/Hybrid variants
    "Hybrid": 1.15,
    "Plug-in Hybrid": 1.2,
    "Electric": 1.25,
}

class CarInput(BaseModel):
    make: str
    model: str
    trim: Optional[str] = "Base"  # Make trim optional with default "Base"
    year: int
    mileage: Optional[float] = None
    condition: Optional[str] = "Good"
    zip_code: Optional[str] = None

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
    if not trim or trim.lower() == "base":
        return 1.0
        
    # Normalize the trim name
    trim = trim.strip()
    
    # Check for exact match
    if trim in TRIM_MULTIPLIERS:
        return TRIM_MULTIPLIERS[trim]
    
    # Check for partial matches (case insensitive)
    trim_lower = trim.lower()
    for known_trim, multiplier in TRIM_MULTIPLIERS.items():
        if known_trim.lower() in trim_lower or trim_lower in known_trim.lower():
            return multiplier
    
    # Check for performance indicators
    if any(perf in trim_lower for perf in ["amg", "m sport", "rs", "type r", "gt", "sport"]):
        return 1.3
    
    # Check for luxury indicators
    if any(lux in trim_lower for lux in ["premium", "luxury", "elite", "platinum", "limited"]):
        return 1.2
        
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

async def get_market_check_price(make: str, model: str, year: int, trim: str = None) -> Optional[float]:
    """Fetch pricing data from MarketCheck API"""
    try:
        url = "https://api.marketcheck.com/v2/search/car/active"
        api_key = os.getenv('API_KEY')
        headers = {
            "content-type": "application/json",
            "Authorization": api_key
        }
        params = {
            'api_key': api_key,
            'make': make,
            'model': model,
            'year': year,
            'car_type': 'used',
            'stats': 'price',
            'facets': 'trim',
            'rows': 0
        }
        
        if trim and trim.lower() != "base":
            params['trim'] = trim
        
        print(f"Calling MarketCheck API with params: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"MarketCheck API Response: {json.dumps(data, indent=2)}")
                    
                    if 'num_found' in data and data['num_found'] > 0:
                        # Get average price from listings
                        if 'listings' in data:
                            prices = [listing['price'] for listing in data['listings'] if 'price' in listing]
                            if prices:
                                return statistics.mean(prices)
                    
                    print("No price data found in MarketCheck response")
                    return None
                else:
                    print(f"MarketCheck API error: {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"Error calling MarketCheck API: {str(e)}")
        return None

def get_base_trims(make: str, model: str) -> List[str]:
    """Get base trims for a specific make and model"""
    # Basic trim levels that most cars have
    basic_trims = ["Base", "Sport", "Limited"]
    
    # Make-specific base trims
    make_base_trims = {
        "Toyota": ["L", "LE", "XLE", "SE"],
        "Honda": ["LX", "EX", "EX-L"],
        "Ford": ["XL", "XLT", "Lariat"],
        "Chevrolet": ["LS", "LT", "LTZ"],
        "BMW": ["sDrive", "xDrive", "M Sport"],
        "Mercedes-Benz": ["Base", "AMG Line"],
        "Audi": ["Premium", "Prestige", "S Line"],
        "Lexus": ["Base", "F Sport"],
        "Porsche": ["Base", "S"],
        "Ferrari": ["Base", "Spider"],
        "Lamborghini": ["Base", "Spyder"],
        "McLaren": ["Base", "S"],
        "Rolls-Royce": ["Base", "Extended Wheelbase"],
        "Bentley": ["Base", "Speed"],
        "Aston Martin": ["Base", "Volante"],
    }
    
    # Model-specific base trims
    model_base_trims = {
        "911": ["Carrera", "Carrera S", "Turbo"],
        "F-150": ["XL", "XLT", "Lariat", "King Ranch", "Platinum"],
        "Corvette": ["1LT", "2LT", "3LT"],
        "Mustang": ["EcoBoost", "GT", "Mach 1"],
        "Civic": ["LX", "Sport", "EX", "Touring"],
        "Camry": ["L", "LE", "SE", "XLE", "XSE"],
        "3 Series": ["330i", "M340i"],
        "E-Class": ["E 350", "E 450", "AMG E 53"],
        "A4": ["40 TFSI", "45 TFSI", "S4"],
    }
    
    # Get base trims for the specific make
    make_trims = make_base_trims.get(make, basic_trims)
    
    # Add model-specific trims if available
    model_trims = model_base_trims.get(model, [])
    
    # Combine and remove duplicates
    all_trims = list(set(make_trims + model_trims))
    
    return sorted(all_trims)

@app.get("/api/trims/{make}/{model}")
async def get_trims(make: str, model: str):
    """Get available trims for a make/model"""
    try:
        # First get base trims from our database
        base_trims = get_base_trims(make, model)
        trims = set(base_trims)  # Use a set to avoid duplicates
        
        # Try to get trims from MarketCheck API
        url = "https://api.marketcheck.com/v2/search/car/active"
        api_key = os.getenv('API_KEY')
        headers = {
            "content-type": "application/json",
            "Authorization": api_key
        }
        params = {
            'api_key': api_key,
            'make': make,
            'model': model,
            'facets': 'trim',
            'rows': 0
        }
        
        print(f"Fetching trims from MarketCheck API with params: {params}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"MarketCheck API Trim Response: {json.dumps(data, indent=2)}")
                    
                    # Extract trims from API response
                    if 'facets' in data and 'trim' in data['facets']:
                        api_trims = [trim['item'] for trim in data['facets']['trim'] if trim.get('item')]
                        trims.update(api_trims)  # Add API trims to our set
                
                else:
                    print(f"MarketCheck API error when fetching trims: {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    
    except Exception as e:
        print(f"Error fetching trims from MarketCheck API: {str(e)}")
    
    # Always ensure "Base" is included and is first
    trims.discard("Base")  # Remove it if it exists
    final_trims = ["Base"] + sorted(list(trims))  # Add it back as first element
    
    print(f"Final trims for {make} {model}: {final_trims}")
    return {"trims": final_trims}

@app.get("/")
async def root():
    return {"message": "Welcome to CarSeer API"}

async def get_carmd_price(make: str, model: str, year: int) -> Optional[float]:
    """Fetch pricing data from CarMD API"""
    try:
        url = "http://api.carmd.com/v3.0/price"
        headers = {
            "content-type": "application/json",
            "authorization": CARMD_AUTHORIZATION,
            "partner-token": CARMD_API_KEY
        }
        params = {
            'make': make,
            'model': model,
            'year': year
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'price' in data['data']:
                        return float(data['data']['price'])
    except Exception as e:
        print(f"CarMD API error: {str(e)}")
    return None

async def get_edmunds_price(make: str, model: str, year: int, zip_code: str = "90210") -> Optional[float]:
    """Fetch pricing data from Edmunds API"""
    try:
        url = f"https://api.edmunds.com/api/vehicle/v2/{make}/{model}/{year}/price"
        params = {
            'api_key': EDMUNDS_API_KEY,
            'zip': zip_code
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'msrp' in data:
                        return float(data['msrp'])
    except Exception as e:
        print(f"Edmunds API error: {str(e)}")
    return None

async def get_base_value_from_apis(make: str, model: str, year: int, trim: str = None, zip_code: str = None) -> Optional[float]:
    """Try to get the base value from multiple APIs"""
    prices = []
    
    # Try MarketCheck API
    market_price = await get_market_check_price(make, model, year, trim)
    if market_price:
        prices.append(market_price)
    
    # Try CarMD API
    carmd_price = await get_carmd_price(make, model, year)
    if carmd_price:
        prices.append(carmd_price)
    
    # Try Edmunds API
    edmunds_price = await get_edmunds_price(make, model, year, zip_code or "90210")
    if edmunds_price:
        prices.append(edmunds_price)
    
    # If we have prices, return the median
    if prices:
        return statistics.median(prices)
    
    # If no API prices available, fall back to our base values
    return get_fallback_base_value(make, model)

def get_fallback_base_value(make: str, model: str) -> float:
    """Get the base value from our database as a fallback"""
    try:
        category = get_car_category(make)
        return BASE_VALUES[category][make][model]
    except KeyError:
        # If not found, use category fallback values
        category = get_car_category(make)
        fallback_values = {
            "Luxury": 60000,
            "Super Luxury": 200000,
            "Exotic": 250000,
            "Premium": 50000,
            "Mainstream": 25000
        }
        return fallback_values.get(category, 25000)

@app.post("/predict")
async def predict_price(car: CarInput):
    try:
        print(f"Predicting price for: {car}")
        
        # Get base value from APIs first, fall back to our database if needed
        base_value = await get_base_value_from_apis(
            car.make,
            car.model,
            car.year,
            car.trim if car.trim != "Base" else None,  # Don't send trim if it's Base
            car.zip_code
        )
        
        print(f"Base value from API: {base_value}")
        
        # Get car category
        category = get_car_category(car.make)
        
        # Calculate multipliers
        trim_multiplier = get_trim_multiplier(car.trim) if car.trim else 1.0
        condition_multiplier = CONDITION_MULTIPLIERS.get(car.condition, 1.0)
        mileage_multiplier = calculate_mileage_impact(car.mileage, category) if car.mileage else 1.0
        
        print(f"Multipliers - Trim: {trim_multiplier}, Condition: {condition_multiplier}, Mileage: {mileage_multiplier}")
        
        # Calculate predicted value
        predicted_value = base_value * trim_multiplier * condition_multiplier * mileage_multiplier
        
        print(f"Final predicted value: {predicted_value}")
        
        # Calculate confidence based on data sources
        confidence = "high" if base_value != get_fallback_base_value(car.make, car.model) else "medium"
        
        return {
            "predicted_value": round(predicted_value),
            "mean_value": round(predicted_value),
            "price_range": {
                "low": round(predicted_value * 0.9),
                "high": round(predicted_value * 1.1)
            },
            "category": category,
            "factors": {
                "base_value": round(base_value),
                "trim_multiplier": trim_multiplier,
                "condition_multiplier": condition_multiplier,
                "mileage_multiplier": mileage_multiplier
            },
            "confidence": confidence
        }
        
    except Exception as e:
        print(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/test")
async def test_api():
    """Test endpoint to verify MarketCheck API connection"""
    try:
        url = "https://api.marketcheck.com/v2/search/car/active"
        headers = {
            "content-type": "application/json",
            "Authorization": os.getenv('API_KEY')
        }
        params = {
            'api_key': os.getenv('API_KEY'),
            'make': 'Toyota',  # Using Toyota as a test case
            'model': 'Camry',
            'year': 2020,
            'stats': 'price',
            'facets': 'trim',
            'rows': 0
        }
        
        print(f"Testing API connection with params: {params}")
        print(f"API Key being used: {os.getenv('API_KEY')}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                print(f"API Test - Response Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "message": "API connection successful",
                        "data": data
                    }
                else:
                    error_text = await response.text()
                    print(f"API Test - Error Response: {error_text}")
                    return {
                        "status": "error",
                        "message": f"API returned status {response.status}",
                        "error": error_text
                    }
    except Exception as e:
        print(f"API Test - Exception: {str(e)}")
        return {
            "status": "error",
            "message": "API connection failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 