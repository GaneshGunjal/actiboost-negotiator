# src/utils/price_loader.py
import csv
import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class PriceDatabase:
    """Load and query pricing data from CSV"""
    
    def __init__(self, csv_path: str = "data/actiboost_pricing.csv"):
        self.csv_path = csv_path
        self.data = []
        self._load_data()
    
    def _load_data(self):
        """Load data from CSV file"""
        if not os.path.exists(self.csv_path):
            logger.warning(f"CSV file not found: {self.csv_path}")
            self._create_sample_data()
            return
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.data = list(reader)
        
        logger.info(f"Loaded {len(self.data)} pricing records")
    
    def _create_sample_data(self):
        """Create sample data if CSV doesn't exist"""
        self.data = [
            {"category": "flat", "subcategory": "2BHK", "location": "Hinjawadi", 
             "size_range": "800-1200", "base_price_per_sqft": "6500", 
             "negotiation_floor_percent": "10", "description": "Standard 2BHK in Hinjawadi"},
            {"category": "flat", "subcategory": "2BHK", "location": "Hinjawadi", 
             "size_range": "1200-1600", "base_price_per_sqft": "7000", 
             "negotiation_floor_percent": "12", "description": "Premium 2BHK with balcony"},
            {"category": "flat", "subcategory": "2BHK", "location": "Baner", 
             "size_range": "800-1200", "base_price_per_sqft": "7500", 
             "negotiation_floor_percent": "10", "description": "Standard 2BHK in Baner"},
        ]
    
    def search(self, category: str, subcategory: str, location: str, 
               size: float) -> List[Dict]:
        """Search for pricing data"""
        results = []
        for row in self.data:
            if row['category'].lower() != category.lower():
                continue
            if row['subcategory'].lower() != subcategory.lower():
                continue
            if row['location'].lower() != location.lower():
                continue
            
            # Check size range
            size_min, size_max = map(float, row['size_range'].split('-'))
            if size_min <= size <= size_max:
                results.append(row)
        
        return results
    
    def get_best_match(self, category: str, subcategory: str, 
                       location: str, size: float) -> Optional[Dict]:
        """Get the best matching price record"""
        results = self.search(category, subcategory, location, size)
        if results:
            return results[0]
        return None
    
    def calculate_price(self, category: str, subcategory: str, 
                        location: str, size: float) -> Tuple[float, float]:
        """Calculate base price and floor price"""
        match = self.get_best_match(category, subcategory, location, size)
        
        if not match:
            # Fallback to default
            base_price = 6500
            floor_percent = 10
        else:
            base_price = float(match['base_price_per_sqft'])
            floor_percent = float(match['negotiation_floor_percent'])
        
        total_base = base_price * size
        floor_price = total_base * (1 - floor_percent / 100)
        
        return total_base, floor_price

price_db = PriceDatabase()