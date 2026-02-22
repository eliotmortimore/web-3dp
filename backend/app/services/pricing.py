from typing import Dict, Any

class PricingService:
    # Filament Registry (To be moved to DB later)
    # Price per kg in USD
    FILAMENTS = {
        "PLA": {
            "density": 1.24, # g/cm3
            "price_per_kg": 20.00,
            "colors": ["Red", "Blue", "White", "Black", "Grey", "Green", "Yellow", "Orange"]
        },
        "PETG": {
            "density": 1.27,
            "price_per_kg": 22.00,
            "colors": ["Transparent", "Black", "White", "Grey"]
        },
        "ABS": {
            "density": 1.04,
            "price_per_kg": 25.00,
            "colors": ["Black", "White", "Grey"]
        },
        "TPU": {
            "density": 1.21,
            "price_per_kg": 35.00,
            "colors": ["Black", "Red"]
        }
    }

    # Overhead Costs
    SETUP_FEE = 5.00 # $5.00 per unique file (handling, slicing setup)
    MACHINE_HOURLY_RATE = 3.00 # $3.00 per hour of print time

    def calculate_price(
        self, 
        volume_cm3: float, 
        material: str, 
        estimated_time_s: int,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Calculates the final price based on material usage and machine time.
        
        Formula:
        Material Cost = (Volume * Density) * (Price / 1000)
        Machine Cost = Hours * Hourly Rate
        Total Unit Cost = Material Cost + Machine Cost
        Total Price = (Total Unit Cost * Quantity) + Setup Fee
        """
        mat_info = self.FILAMENTS.get(material.upper(), self.FILAMENTS["PLA"])
        density = mat_info["density"]
        price_per_kg = mat_info["price_per_kg"]
        
        # 1. Material Cost
        weight_g = volume_cm3 * density
        material_cost_unit = weight_g * (price_per_kg / 1000.0)
        
        # 2. Machine Cost
        hours = estimated_time_s / 3600.0
        machine_cost_unit = hours * self.MACHINE_HOURLY_RATE
        
        # 3. Total
        unit_cost = material_cost_unit + machine_cost_unit
        
        # Apply margin/markup if desired (currently 1.0)
        final_unit_price = unit_cost * 1.0 
        
        # Ensure minimum price per part (e.g., $1.00)
        final_unit_price = max(final_unit_price, 1.00)
        
        total_price = (final_unit_price * quantity) + self.SETUP_FEE
        
        return {
            "total_price": round(total_price, 2),
            "unit_price": round(final_unit_price, 2),
            "breakdown": {
                "material_cost": round(material_cost_unit * quantity, 2),
                "machine_cost": round(machine_cost_unit * quantity, 2),
                "setup_fee": self.SETUP_FEE,
                "weight_g": round(weight_g * quantity, 2)
            }
        }

pricing_service = PricingService()
