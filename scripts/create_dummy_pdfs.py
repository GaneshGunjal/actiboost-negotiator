# scripts/create_dummy_pdfs.py
from fpdf import FPDF
import os
from datetime import datetime

class ActiboostPDFGenerator:
    """Generate dummy PDF documents for RAG testing"""
    
    def __init__(self, output_dir: str = "data/dummy_pdfs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_contract_template(self):
        pdf = FPDF()
        pdf.add_page()
        
        # Use Unicode font
        pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
        pdf.set_font('DejaVu', '', 14)
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ACTIBOOST ENGINEERS & CONTRACTORS", 0, 1, "C")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "STANDARD CONSTRUCTION CONTRACT", 0, 1, "C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, """
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
        """)
        
        filename = os.path.join(self.output_dir, "construction_contract.pdf")
        pdf.output(filename)
        print(f"✅ Created: {filename}")
        return filename
    
    def create_project_estimate(self):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ACTIBOOST ENGINEERS & CONTRACTORS", 0, 1, "C")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "PROJECT ESTIMATE", 0, 1, "C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, """
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
        """)
        
        filename = os.path.join(self.output_dir, "project_estimate.pdf")
        pdf.output(filename)
        print(f"✅ Created: {filename}")
        return filename
    
    def create_material_specs(self):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ACTIBOOST ENGINEERS & CONTRACTORS", 0, 1, "C")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "MATERIAL SPECIFICATIONS", 0, 1, "C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, """
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
        """)
        
        filename = os.path.join(self.output_dir, "material_specifications.pdf")
        pdf.output(filename)
        print(f"✅ Created: {filename}")
        return filename
    
    def create_safety_policy(self):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ACTIBOOST ENGINEERS & CONTRACTORS", 0, 1, "C")
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "SAFETY POLICY", 0, 1, "C")
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)
        
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, """
        SAFETY POLICY MANUAL
        
        Our Commitment: Zero Harm
        
        1. PPE: Hard hats, safety boots, high-visibility vests, safety glasses
        2. FALL PROTECTION: Guardrails, safety nets, personal fall arrest systems
        3. ELECTRICAL SAFETY: Lockout/Tagout, GFCI protection, proper grounding
        4. FIRE SAFETY: Fire extinguishers, assembly points, regular drills
        5. EMERGENCY: First aid kits, designated responders, emergency contacts
        6. TRAINING: Mandatory orientation, monthly meetings, JSA for all tasks
        """)
        
        filename = os.path.join(self.output_dir, "safety_policy.pdf")
        pdf.output(filename)
        print(f"✅ Created: {filename}")
        return filename
    
    def generate_all(self):
        print("📄 Generating Actiboost dummy PDFs...")
        self.create_contract_template()
        self.create_project_estimate()
        self.create_material_specs()
        self.create_safety_policy()
        print("✅ All PDFs created successfully!")

if __name__ == "__main__":
    generator = ActiboostPDFGenerator()
    generator.generate_all()