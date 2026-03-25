# SmartStore ERP — Demo Dealers Seed Script
# Run: python seed_dealers.py

from app.core.database import SessionLocal, engine, Base
from app.models.dealer import Dealer

Base.metadata.create_all(bind=engine)
db = SessionLocal()

existing = db.query(Dealer).count()
if existing > 0:
    print(f"Database mein already {existing} dealers hain. Skip.")
    db.close()
    exit()

dealers = [
    Dealer(name="Sharma General Store", phone="9876543210", address="MG Road, Pune", dealer_type="customer", credit_limit=5000, outstanding=1200),
    Dealer(name="Patel Kirana", phone="9876543211", address="FC Road, Pune", dealer_type="customer", credit_limit=10000, outstanding=3500),
    Dealer(name="Amul Distributor", phone="9876543212", address="Shivaji Nagar, Pune", gstin="27AABCU9603R1ZM", dealer_type="supplier", credit_limit=50000, outstanding=0),
    Dealer(name="Gupta Wholesale", phone="9876543213", address="Market Yard, Pune", dealer_type="both", credit_limit=20000, outstanding=8000),
    Dealer(name="Joshi Medical & General", phone="9876543214", address="Kothrud, Pune", dealer_type="customer", credit_limit=3000, outstanding=0),
    Dealer(name="Deshmukh Traders", phone="9876543215", address="Hadapsar, Pune", gstin="27AADCD1234F1ZP", dealer_type="supplier", credit_limit=30000, outstanding=0),
    Dealer(name="Rajesh Pan Corner", phone="9876543216", address="Camp, Pune", dealer_type="customer", credit_limit=2000, outstanding=1800),
    Dealer(name="ITC Distributor", phone="9876543217", address="Hinjewadi, Pune", gstin="27AAACI1681G1ZI", dealer_type="supplier", credit_limit=100000, outstanding=0),
]

db.add_all(dealers)
db.commit()
print(f"DONE! {len(dealers)} dealers added!")
db.close()
