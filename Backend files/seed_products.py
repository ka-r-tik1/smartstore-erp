# SmartStore ERP — Demo Products Seed Script
# Ye script database mein sample FMCG products daalega
# Run: python seed_products.py

from app.core.database import SessionLocal, engine, Base
from app.models.product import Product

# Tables banao (agar nahi hain)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Pehle check karo — agar products already hain toh skip karo
existing = db.query(Product).count()
if existing > 0:
    print(f"Database mein already {existing} products hain. Skip kar raha hun.")
    db.close()
    exit()

# 20 FMCG products — real Indian kirana store jaisa
products = [
    Product(name="Amul Butter 500g", name_mr="अमूल बटर 500g", barcode="8901030010064", category="Dairy", brand="Amul", unit="pcs", mrp=290, selling_price=280, purchase_price=260, gst_rate=5, stock_qty=50, reorder_level=10),
    Product(name="Tata Salt 1kg", name_mr="टाटा मीठ 1kg", barcode="8901725115159", category="Grocery", brand="Tata", unit="pcs", mrp=28, selling_price=28, purchase_price=22, gst_rate=0, stock_qty=100, reorder_level=20),
    Product(name="Maggi 2-Min Noodles", name_mr="मॅगी नूडल्स", barcode="8901058810035", category="Snacks", brand="Nestle", unit="pcs", mrp=14, selling_price=14, purchase_price=11, gst_rate=12, stock_qty=200, reorder_level=50),
    Product(name="Parle-G Biscuit 250g", name_mr="पार्ले-जी बिस्कीट", barcode="8901840112355", category="Biscuits", brand="Parle", unit="pcs", mrp=30, selling_price=30, purchase_price=25, gst_rate=18, stock_qty=150, reorder_level=30),
    Product(name="Amul Milk 500ml", name_mr="अमूल दूध 500ml", barcode="8901030010071", category="Dairy", brand="Amul", unit="pcs", mrp=30, selling_price=30, purchase_price=26, gst_rate=0, stock_qty=80, reorder_level=20),
    Product(name="Fortune Sunflower Oil 1L", name_mr="फॉर्च्यून तेल 1L", barcode="8901058002317", category="Oil", brand="Fortune", unit="litre", mrp=180, selling_price=175, purchase_price=155, gst_rate=5, stock_qty=40, reorder_level=10),
    Product(name="Aashirvaad Atta 5kg", name_mr="आशीर्वाद आटा 5kg", barcode="8901063010116", category="Grocery", brand="ITC", unit="pcs", mrp=295, selling_price=290, purchase_price=260, gst_rate=0, stock_qty=30, reorder_level=8),
    Product(name="Coca-Cola 750ml", name_mr="कोका-कोला 750ml", barcode="8901764010017", category="Beverages", brand="Coca-Cola", unit="pcs", mrp=40, selling_price=40, purchase_price=32, gst_rate=28, stock_qty=100, reorder_level=25),
    Product(name="Surf Excel 1kg", name_mr="सर्फ एक्सेल 1kg", barcode="8901030020063", category="Cleaning", brand="HUL", unit="pcs", mrp=220, selling_price=215, purchase_price=190, gst_rate=18, stock_qty=35, reorder_level=10),
    Product(name="Haldiram Namkeen 200g", name_mr="हळदीराम नमकीन", barcode="8904004403008", category="Snacks", brand="Haldiram", unit="pcs", mrp=60, selling_price=58, purchase_price=48, gst_rate=12, stock_qty=60, reorder_level=15),
    Product(name="Red Label Tea 500g", name_mr="रेड लेबल चहा 500g", barcode="8901030622878", category="Beverages", brand="Brooke Bond", unit="pcs", mrp=285, selling_price=280, purchase_price=250, gst_rate=5, stock_qty=45, reorder_level=10),
    Product(name="Vim Dishwash Bar", name_mr="विम बार", barcode="8901030030062", category="Cleaning", brand="HUL", unit="pcs", mrp=10, selling_price=10, purchase_price=8, gst_rate=18, stock_qty=200, reorder_level=50),
    Product(name="Dettol Soap 75g", name_mr="डेटॉल साबण 75g", barcode="8901396352006", category="Personal Care", brand="Reckitt", unit="pcs", mrp=42, selling_price=40, purchase_price=34, gst_rate=18, stock_qty=80, reorder_level=20),
    Product(name="Britannia Bread", name_mr="ब्रिटानिया ब्रेड", barcode="8901063060111", category="Bakery", brand="Britannia", unit="pcs", mrp=45, selling_price=45, purchase_price=38, gst_rate=0, stock_qty=25, reorder_level=8),
    Product(name="Kurkure Masala Munch", name_mr="कुरकुरे मसाला", barcode="8901491101677", category="Snacks", brand="PepsiCo", unit="pcs", mrp=20, selling_price=20, purchase_price=16, gst_rate=12, stock_qty=120, reorder_level=30),
    Product(name="Colgate Toothpaste 100g", name_mr="कोलगेट टूथपेस्ट", barcode="8901314010117", category="Personal Care", brand="Colgate", unit="pcs", mrp=55, selling_price=52, purchase_price=42, gst_rate=18, stock_qty=60, reorder_level=15),
    Product(name="Thums Up 2L", name_mr="थम्स अप 2L", barcode="8901764012011", category="Beverages", brand="Coca-Cola", unit="pcs", mrp=90, selling_price=88, purchase_price=72, gst_rate=28, stock_qty=40, reorder_level=10),
    Product(name="Clinic Plus Shampoo 175ml", name_mr="क्लिनिक प्लस शॅम्पू", barcode="8901030550027", category="Personal Care", brand="HUL", unit="pcs", mrp=95, selling_price=92, purchase_price=78, gst_rate=18, stock_qty=35, reorder_level=10),
    Product(name="Sugar 1kg (Loose)", name_mr="साखर 1kg", barcode=None, category="Grocery", brand=None, unit="kg", mrp=48, selling_price=46, purchase_price=40, gst_rate=0, stock_qty=200, reorder_level=50),
    Product(name="Lay's Classic Salted 52g", name_mr="लेज क्लासिक", barcode="8901491100182", category="Snacks", brand="PepsiCo", unit="pcs", mrp=20, selling_price=20, purchase_price=16, gst_rate=12, stock_qty=90, reorder_level=25),
]

db.add_all(products)
db.commit()
print(f"DONE! {len(products)} products successfully added!")
db.close()
