from typing import Dict

class PricingEngine:
    # Default Density values (g/cm3)
    DENSITY: Dict[str, float] = {
        "PLA": 1.24,
        "PETG": 1.27,
        "ABS": 1.04,
        "TPU": 1.21,
    }
    
    # Default Pricing ($/g)
    COST_PER_GRAM: Dict[str, float] = {
        "PLA": 0.05,
        "PETG": 0.06,
        "ABS": 0.05,
        "TPU": 0.10,
    }
    
    # Machine Costs
    SETUP_FEE: float = 5.00  # Startup/Handling fee
    MACHINE_RATE_PER_HR: float = 3.00  # $3/hr machine time

    def calculate_price(
        self, 
        volume_cm3: float, 
        material: str, 
        quantity: int, 
        est_hours: float = 1.0
    ) -> float:
        material = material.upper()
        
        # Get Density & Cost
        density = self.DENSITY.get(material, 1.24)
        cost_g = self.COST_PER_GRAM.get(material, 0.05)
        
        # Calculate Weight
        weight_g = volume_cm3 * density
        
        # Calculate Material Cost
        material_cost = weight_g * cost_g
        
        # Calculate Machine Cost
        machine_cost = est_hours * self.MACHINE_RATE_PER_HR
        
        # Calculate Total per Unit
        unit_price = material_cost + machine_cost + self.SETUP_FEE
        
        # Total
        total_price = unit_price * quantity
        
        return round(total_price, 2)
