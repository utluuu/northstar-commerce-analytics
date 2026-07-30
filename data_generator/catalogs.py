"""Stable reference catalogs used by the synthetic data generator."""

SEGMENTS = [
    (1, "Occasional", "Low-frequency customers with broad category interests.", 0.45, 0.70),
    (2, "Loyal", "Repeat customers with above-average order frequency.", 0.30, 1.45),
    (3, "VIP", "High-value customers with strong repeat behavior and larger baskets.", 0.10, 2.20),
    (4, "Deal Seeker", "Price-sensitive customers responsive to promotions.", 0.15, 1.10),
]

CHANNELS = [(1, "Website"), (2, "Mobile App"), (3, "Marketplace"), (4, "Social Commerce")]
ORDER_STATUSES = [(1, "Pending"), (2, "Processing"), (3, "Shipped"), (4, "Delivered"), (5, "Cancelled")]

CATEGORY_TREE = {
    "Electronics": ["Audio", "Computing", "Mobile Accessories", "Smart Home"],
    "Home & Living": ["Kitchen", "Bedding", "Decor", "Organization"],
    "Fitness": ["Yoga", "Strength", "Cardio", "Recovery"],
    "Fashion": ["Bags", "Jewelry", "Eyewear", "Seasonal Accessories"],
    "Beauty": ["Skincare", "Haircare", "Personal Care", "Wellness"],
    "Outdoor": ["Camping", "Travel", "Cycling", "Hiking"],
}

PRODUCT_NOUNS = [
    "Headphones", "Speaker", "Adapter", "Keyboard", "Mouse", "Charger", "Lamp", "Bottle",
    "Pillow", "Basket", "Scale", "Diffuser", "Blanket", "Mug", "Mat", "Bands", "Dumbbell",
    "Roller", "Tracker", "Rope", "Backpack", "Wallet", "Stand", "Organizer", "Towel", "Kettle",
    "Brush", "Serum", "Case", "Pouch", "Tripod", "Lantern", "Gloves", "Sunglasses", "Massager",
]
PRODUCT_ADJECTIVES = [
    "Essential", "Premium", "Compact", "Smart", "Classic", "Active", "Urban", "Pro", "Eco",
    "Everyday", "Travel", "Studio", "Performance", "Comfort", "Wireless", "Lightweight",
]
BRANDS = ["Northstar", "Aster", "BluePeak", "Cedar & Co", "Flux", "Kinetic", "Luma", "Morrow", "Orbit", "Vela"]

CITIES = [
    ("New York", "NY", "Northeast", "10001", 0.105), ("Los Angeles", "CA", "West", "90001", 0.085),
    ("Chicago", "IL", "Midwest", "60601", 0.060), ("Houston", "TX", "South", "77001", 0.055),
    ("Phoenix", "AZ", "West", "85001", 0.040), ("Philadelphia", "PA", "Northeast", "19019", 0.040),
    ("San Antonio", "TX", "South", "78201", 0.035), ("San Diego", "CA", "West", "92101", 0.035),
    ("Dallas", "TX", "South", "75201", 0.040), ("San Jose", "CA", "West", "95101", 0.030),
    ("Austin", "TX", "South", "73301", 0.035), ("Jacksonville", "FL", "South", "32099", 0.025),
    ("Seattle", "WA", "West", "98101", 0.035), ("Denver", "CO", "West", "80201", 0.030),
    ("Boston", "MA", "Northeast", "02108", 0.030), ("Atlanta", "GA", "South", "30301", 0.035),
    ("Portland", "OR", "West", "97201", 0.025), ("Miami", "FL", "South", "33101", 0.030),
    ("Detroit", "MI", "Midwest", "48201", 0.020), ("Minneapolis", "MN", "Midwest", "55401", 0.020),
    ("Charlotte", "NC", "South", "28201", 0.025), ("Nashville", "TN", "South", "37201", 0.020),
    ("Baltimore", "MD", "Northeast", "21201", 0.020), ("Salt Lake City", "UT", "West", "84101", 0.015),
    ("Kansas City", "MO", "Midwest", "64101", 0.015), ("Columbus", "OH", "Midwest", "43004", 0.020),
    ("Indianapolis", "IN", "Midwest", "46201", 0.020), ("Milwaukee", "WI", "Midwest", "53201", 0.015),
    ("New Orleans", "LA", "South", "70112", 0.010), ("Pittsburgh", "PA", "Northeast", "15201", 0.015),
]

FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery", "Cameron", "Drew", "Quinn", "Parker", "Sam", "Reese", "Rowan", "Skyler"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Anderson", "Thomas", "Moore", "Martin", "Lee", "Clark", "Lewis"]

ACQUISITION_SOURCES = ["Organic", "Paid Search", "Social", "Referral", "Email", "Marketplace"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Gift Card"]
CARRIERS = ["UPS", "FedEx", "USPS", "DHL"]
RETURN_REASONS = ["Damaged", "Wrong Item", "Not as Described", "Changed Mind", "Too Late", "Defective"]

MONTH_MULTIPLIERS = {1: 0.82, 2: 0.86, 3: 0.94, 4: 0.97, 5: 1.00, 6: 1.03,
                     7: 0.99, 8: 1.02, 9: 1.07, 10: 1.12, 11: 1.25, 12: 1.35}
