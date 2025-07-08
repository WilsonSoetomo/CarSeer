import requests
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any

load_dotenv()

api_url = "https://carapi.app/api/auth/login"
payload = {
    "api_token": os.getenv("API_TOKEN"),
    "api_secret": os.getenv("API_SECRET")
}

def test_api():
    response = requests.post(api_url, json=payload)
    print("status code: ", response.status_code)
    # print("response: ", response.text)
    if response.status_code == 200:
        jwt_token = response.text.strip()
        if jwt_token:
            # print("successful jwt_token: ", jwt_token)
            return jwt_token
    else:
        print("error could not login with api_token and api_secret: ", response.text)

def get_car_data(token: str, make: str = None, model: str = None, year: int = None) -> List[Dict]:
    """Fetch car data from the API"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Build query parameters
    params = {}
    if make:
        params['make'] = make
    if model:
        params['model'] = model
    if year:
        params['year'] = year
    
    try:
        # You'll need to adjust this endpoint based on what CarAPI actually provides
        response = requests.get("https://carapi.app/api/cars", headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"Error fetching car data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching car data: {e}")
        return []

def get_cars_from_api(token: str = None, makes: List[str] = None, min_year: int = 2010) -> List[Dict]:
    """Fetch car data from CarAPI using the provided endpoint"""
    
    # Build the JSON filter for the API
    filters = []
    
    if makes:
        filters.append({
            "field": "make", 
            "op": "in", 
            "val": makes
        })
    
    if min_year:
        filters.append({
            "field": "year", 
            "op": ">=", 
            "val": min_year
        })
    
    # Convert filters to JSON string
    json_filters = json.dumps(filters)
    
    # Try the newer v2 endpoint first
    url = f"https://carapi.app/api/models/v2?json={json_filters}"
    
    # Set up headers
    headers = {'accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        print(f"Trying API endpoint: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # print(f"data: {data}")
            print(f"Successfully fetched {len(data)} cars from API v2")
            
            # Process the API response - it might be a list of strings or objects
            processed_cars = []
            for item in data:
                if isinstance(item, str):
                    # If it's a string, try to parse it as JSON
                    print(f"item: {item}")
                    try:
                        car_data = json.loads(item)
                        processed_cars.append(car_data)
                    except:
                        # If it's just a string, create a basic car object
                        processed_cars.append({
                            "make": "Unknown",
                            "model": item,
                            "year": 2023,
                            "price": 30000,
                            "horsepower": 200,
                            "mpg": 25,
                            "safety_rating": 4.0
                        })
                elif isinstance(item, dict):
                    # If it's already a dictionary, use it directly
                    processed_cars.append(item)
                else:
                    print(f"Unexpected data type: {type(item)}")
            
            return processed_cars
            
        else:
            print(f"v2 API Error: {response.status_code} - {response.text}")
            
            # Try the original endpoint as fallback
            url_original = f"https://carapi.app/api/models?json={json_filters}"
            print(f"Trying fallback endpoint: {url_original}")
            response = requests.get(url_original, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully fetched {len(data)} cars from original API")
                return data
            else:
                print(f"Original API Error: {response.status_code} - {response.text}")
                return []
            
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def calculate_car_score(car: Dict[str, Any], criteria: str = "overall") -> float:
    """Calculate a score for a car based on specified criteria"""
    score = 0.0
    
    # Extract car data (adjust field names based on actual API response)
    make = car.get("make", "")
    model = car.get("model", "")
    year = car.get("year", 0)
    
    # For demonstration, we'll use some sample values
    # In a real scenario, these would come from the API
    price = car.get("price", 30000)  # Default price
    horsepower = car.get("horsepower", 200)  # Default HP
    mpg = car.get("mpg", 25)  # Default MPG
    safety_rating = car.get("safety_rating", 4.0)  # Default safety
    
    if criteria == "price":
        # Lower price = higher score (better value)
        score = max(0, 100000 - price) / 1000
    elif criteria == "performance":
        # Higher horsepower = higher score
        score = horsepower / 10
    elif criteria == "efficiency":
        # Higher MPG = higher score
        score = mpg
    elif criteria == "safety":
        # Higher safety rating = higher score
        score = safety_rating * 20
    elif criteria == "reliability":
        # Simulate reliability based on make (Toyota/Honda = higher)
        reliability_bonus = 20 if make.lower() in ["toyota", "honda", "lexus"] else 0
        score = 70 + reliability_bonus
    elif criteria == "overall":
        # Weighted combination of all factors
        price_score = max(0, 100000 - price) / 1000
        performance_score = horsepower / 10
        efficiency_score = mpg
        safety_score = safety_rating * 20
        reliability_score = 70 + (20 if make.lower() in ["toyota", "honda", "lexus"] else 0)
        
        # Weighted average
        score = (price_score * 0.25 + performance_score * 0.20 + 
                efficiency_score * 0.20 + safety_score * 0.20 + reliability_score * 0.15)
    
    return round(score, 2)

def rank_cars(cars: List[Dict], criteria: str = "overall", top_n: int = 5) -> List[Dict]:
    """Rank cars by specified criteria"""
    if not cars:
        return []
    
    # Calculate scores for each car
    for car in cars:
        car["score"] = calculate_car_score(car, criteria)
    
    # Sort by score (descending)
    ranked_cars = sorted(cars, key=lambda x: x.get("score", 0), reverse=True)
    
    # Add ranking position
    for i, car in enumerate(ranked_cars[:top_n]):
        car["rank"] = i + 1
    
    return ranked_cars[:top_n]

def display_rankings(ranked_cars: List[Dict], criteria: str):
    """Display the ranked cars in a formatted way"""
    if not ranked_cars:
        print(f"No cars found for {criteria} ranking")
        return
    
    print(f"\n🚗 TOP 5 CARS BY {criteria.upper()} 🚗")
    print("=" * 60)
    
    for car in ranked_cars:
        make = car.get("make", "N/A")
        model = car.get("model", "N/A")
        year = car.get("year", "N/A")
        score = car.get("score", 0)
        rank = car.get("rank", 0)
        
        print(f"#{rank} - {make} {model} ({year})")
        print(f"   Score: {score}")
        
        # Show relevant details based on criteria
        if criteria == "price":
            price = car.get("price", "N/A")
            print(f"   Price: ${price:,}" if isinstance(price, (int, float)) else f"   Price: {price}")
        elif criteria == "performance":
            hp = car.get("horsepower", "N/A")
            print(f"   Horsepower: {hp} HP")
        elif criteria == "efficiency":
            mpg = car.get("mpg", "N/A")
            print(f"   MPG: {mpg}")
        elif criteria == "safety":
            safety = car.get("safety_rating", "N/A")
            print(f"   Safety Rating: {safety}/5")
        
        print()

def main():
    print("🏎️  CarSeer - Car Ranking System 🏎️")
    print("=" * 50)
    token = test_api()
    
    # Get cars from API (using popular makes)
    popular_makes = ["Toyota", "Honda", "Ford", "Chevrolet", "BMW", "Mercedes-Benz"]
    cars = get_cars_from_api(token, makes=popular_makes, min_year=2020)
    
    if not cars:
        print("No data from API. Using sample data for demonstration.")
        # Sample data for demonstration
        cars = [
            {"make": "Toyota", "model": "Camry", "year": 2023, "price": 25000, "horsepower": 203, "mpg": 28, "safety_rating": 5.0},
            {"make": "Honda", "model": "Accord", "year": 2023, "price": 26000, "horsepower": 192, "mpg": 30, "safety_rating": 5.0},
            {"make": "Ford", "model": "Mustang", "year": 2023, "price": 35000, "horsepower": 310, "mpg": 22, "safety_rating": 4.5},
            {"make": "BMW", "model": "3 Series", "year": 2023, "price": 43000, "horsepower": 255, "mpg": 25, "safety_rating": 5.0},
            {"make": "Toyota", "model": "Prius", "year": 2023, "price": 24000, "horsepower": 121, "mpg": 52, "safety_rating": 5.0},
            {"make": "Honda", "model": "CR-V", "year": 2023, "price": 28000, "horsepower": 190, "mpg": 28, "safety_rating": 5.0},
            {"make": "Chevrolet", "model": "Corvette", "year": 2023, "price": 65000, "horsepower": 495, "mpg": 19, "safety_rating": 4.8},
            {"make": "Mercedes-Benz", "model": "C-Class", "year": 2023, "price": 45000, "horsepower": 255, "mpg": 24, "safety_rating": 5.0},
        ]
    
    # Define ranking categories
    categories = {
        "overall": "Best Overall Cars",
        "price": "Best Value Cars", 
        "performance": "High Performance Cars",
        "efficiency": "Most Fuel Efficient",
        "safety": "Safest Cars",
        "reliability": "Most Reliable Cars"
    }
    
    print(f"\n📊 Found {len(cars)} cars to rank")
    print("\n" + "="*50)
    
    # Rank cars by each category
    for criteria, description in categories.items():
        ranked_cars = rank_cars(cars, criteria, top_n=5)
        display_rankings(ranked_cars, criteria)
        print("-" * 50)

if __name__ == "__main__":
    main()