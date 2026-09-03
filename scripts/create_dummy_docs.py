# scripts/create_dummy_docs.py
import os
from datetime import datetime

def create_text_files():
    """Create text files instead of PDFs (simpler)"""
    
    output_dir = "data/knowledge_base"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Contract Template
    contract = """
    ACTIBOOST ENGINEERS & CONTRACTORS
    STANDARD CONSTRUCTION CONTRACT
    
    CONTRACT AGREEMENT
    
    This Contract is entered into on this 15th day of January, 2024,
    between Actiboost Engineers & Contractors (hereinafter "Contractor")
    and [Client Name] (hereinafter "Client").
    
    1. SCOPE OF WORK
    The Contractor agrees to provide the following services:
    - Site preparation and foundation work
    - Structural framing
    - Electrical and plumbing installation
    - Interior finishing
    
    2. PROJECT TIMELINE
    - Start Date: February 1, 2024
    - Completion Date: August 1, 2024
    - Total Duration: 180 days
    
    3. PAYMENT TERMS
    - Down Payment: 20% upon signing
    - Progress Payments: Monthly based on completion
    - Final Payment: 10% upon project completion
    
    4. MATERIAL SPECIFICATIONS
    - All materials shall meet or exceed industry standards
    - Contractor shall provide material warranties
    - Client approval required for material substitutions
    
    5. SAFETY REQUIREMENTS
    - All work shall comply with OSHA standards
    - Contractor shall maintain proper insurance
    - Site safety inspections shall be conducted weekly
    """
    
    with open(os.path.join(output_dir, "construction_contract.txt"), "w", encoding="utf-8") as f:
        f.write(contract)
    print("✅ Created: construction_contract.txt")
    
    # 2. Project Estimate
    estimate = """
    ACTIBOOST ENGINEERS & CONTRACTORS
    PROJECT ESTIMATE
    
    Project: Commercial Building Construction
    Location: Mumbai, Maharashtra
    
    COST BREAKDOWN
    
    1. Site Preparation: Rs. 7,00,000
    2. Foundation: Rs. 18,00,000
    3. Structural Framing: Rs. 27,00,000
    4. Exterior Finishes: Rs. 13,00,000
    5. Interior Finishes: Rs. 17,00,000
    6. MEP Services: Rs. 22,00,000
    
    TOTAL ESTIMATED COST: Rs. 1,04,00,000
    
    Notes:
    - Prices valid for 30 days
    - GST extra as applicable
    - Variations subject to change orders
    """
    
    with open(os.path.join(output_dir, "project_estimate.txt"), "w", encoding="utf-8") as f:
        f.write(estimate)
    print("✅ Created: project_estimate.txt")
    
    # 3. Material Specifications
    materials = """
    ACTIBOOST ENGINEERS & CONTRACTORS
    MATERIAL SPECIFICATIONS
    
    1. CEMENT: Portland Pozzolana Cement (PPC) - 43 Grade
    2. STEEL: TMT Steel Bars - Fe 500
    3. CONCRETE: M20 Grade (1:1.5:3)
    4. BRICKS: Fly Ash Bricks - 230mm x 110mm x 75mm
    5. AGGREGATES: Coarse (20mm down) & Fine (Zone II)
    6. WATER: Potable water for mixing
    
    QUALITY ASSURANCE
    - All materials tested as per IS codes
    - Test certificates provided
    - Third-party testing available
    """
    
    with open(os.path.join(output_dir, "material_specifications.txt"), "w", encoding="utf-8") as f:
        f.write(materials)
    print("✅ Created: material_specifications.txt")
    
    # 4. Safety Policy
    safety = """
    ACTIBOOST ENGINEERS & CONTRACTORS
    SAFETY POLICY MANUAL
    
    Our Commitment: Zero Harm
    
    1. PPE: Hard hats, safety boots, high-visibility vests, safety glasses
    2. FALL PROTECTION: Guardrails, safety nets, personal fall arrest systems
    3. ELECTRICAL SAFETY: Lockout/Tagout, GFCI protection, proper grounding
    4. FIRE SAFETY: Fire extinguishers, assembly points, regular drills
    5. EMERGENCY: First aid kits, designated responders, emergency contacts
    6. TRAINING: Mandatory orientation, monthly meetings, JSA for all tasks
    """
    
    with open(os.path.join(output_dir, "safety_policy.txt"), "w", encoding="utf-8") as f:
        f.write(safety)
    print("✅ Created: safety_policy.txt")
    
    print("✅ All documents created successfully!")

if __name__ == "__main__":
    create_text_files()