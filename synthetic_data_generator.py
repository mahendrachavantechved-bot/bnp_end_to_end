"""
synthetic_data_generator.py
============================
Generates 10,000 unique Retail + 10,000 unique SME applicants.
All names are guaranteed unique using a combination pool strategy.

Usage:
    python synthetic_data_generator.py

Outputs:
    retail_applicants.json   (10,000 records)
    sme_applicants.json      (10,000 records)
    retail_applicants.csv    (10,000 records)
    sme_applicants.csv       (10,000 records)
"""

import json
import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(2026)  # reproducible for demos

# ─────────────────────────────────────────────────────────────────────────────
# Name pools – large enough to generate 10,000 unique full names
# ─────────────────────────────────────────────────────────────────────────────
FIRST_NAMES = [
    # South Indian
    "Aarav","Aditya","Akash","Akshay","Amith","Anand","Anil","Anjali","Ankit","Anush",
    "Arjun","Aruna","Ashish","Ashok","Ashwini","Bharath","Bhavana","Chandra","Chetan","Deepa",
    "Deepak","Dhruv","Divya","Geetha","Girish","Gopal","Govind","Harish","Harsha","Hemanth",
    "Indira","Jagadish","Jaya","Jayesh","Kalpana","Karthik","Kiran","Krishnan","Kumar","Lakshmi",
    "Lavanya","Lekha","Madhav","Madhuri","Mahesh","Mamatha","Manoj","Meena","Meghna","Mohan",
    "Mrinal","Murali","Nagesh","Nandini","Naresh","Naveen","Neha","Nikhil","Nilesh","Nisha",
    "Pallavi","Pavan","Pooja","Pradeep","Prasad","Prasanna","Preethi","Priya","Priyanshi","Rahul",
    "Rajesh","Rakesh","Ramesh","Ranjith","Ravi","Rekha","Reshma","Rohit","Roopa","Rupesh",
    "Sachin","Sahana","Samir","Sandeep","Sangeetha","Sanjay","Santhosh","Sarath","Saritha","Satish",
    "Savitha","Shashi","Shiva","Shruti","Smitha","Sneha","Sowmya","Sridhar","Srikanth","Srini",
    "Srinivas","Subash","Sudhir","Sumanth","Sumitra","Sunil","Sunita","Suresh","Sushma","Swati",
    "Tejaswi","Thejesh","Uday","Usha","Vaishnavi","Varun","Vasanth","Veena","Venkat","Vidya",
    "Vijay","Vikas","Vikram","Vinay","Vishnu","Vishal","Yamuna","Yogesh","Yashwanth","Zara",
    # North Indian
    "Aarohi","Aayush","Abhijit","Abhilasha","Abhimanyu","Abhishek","Aishwarya","Akanksha","Alok","Amarjeet",
    "Amisha","Amrita","Anchita","Angad","Ankita","Anshika","Anshul","Antara","Anurag","Aparna",
    "Archana","Arpit","Astha","Avni","Ayesha","Bhavesh","Bhumi","Chanchal","Chirag","Deepika",
    "Devika","Dheeraj","Disha","Esha","Fatima","Gaurav","Gauri","Gunjan","Gurpreet","Harsh",
    "Himanshu","Ishaan","Ishika","Jatin","Juhi","Kabir","Kajal","Kapil","Kavita","Khushi",
    "Komal","Kritika","Kunal","Latika","Madhav","Manish","Manisha","Manjeet","Meghana","Mili",
    "Mitali","Mohit","Muskan","Namita","Nandita","Namrata","Naomi","Natasha","Nidhi","Nikita",
    "Nimisha","Nisha","Nupur","Pallak","Pankaj","Parth","Payal","Pinky","Prachi","Pramod",
    "Pranav","Pranita","Pranjal","Prashanth","Preeti","Puja","Rachna","Radhika","Rajan","Rajni",
    "Rashi","Raunak","Riya","Rohini","Ruhi","Saanvi","Sabina","Sacchit","Saloni","Sanchi",
    "Seema","Shaily","Shikha","Shivani","Simran","Sonam","Sonia","Srishti","Stuti","Swara",
    "Tanisha","Tanvi","Tarun","Trisha","Tushita","Urvashi","Utkarsh","Vaibhav","Vandana","Vanshika",
    "Varsha","Vedant","Vibha","Vivek","Vrinda","Yash","Yashika","Zeenat","Zubaida","Zubair",
    # Additional unique names
    "Aabha","Aachal","Aadhira","Aadhvik","Aagam","Aahan","Aaira","Aakash","Aaliya","Aamani",
    "Aanal","Aanya","Aarchi","Aaryan","Aashna","Aatmaj","Aatrey","Aavya","Aayat","Aazeen",
    "Abeer","Abha","Abhaya","Abhi","Abhirup","Abirami","Achal","Achintya","Acyuta","Adesh",
    "Adhavan","Adheera","Adhiraj","Adhira","Adhiti","Aditi","Adithi","Advaita","Advaith","Advika",
]

LAST_NAMES = [
    # Karnataka / South
    "Rao","Reddy","Nair","Iyer","Iyengar","Pillai","Menon","Krishnamurthy","Venkataraman","Subramaniam",
    "Gowda","Hegde","Shetty","Kamath","Bhat","Naik","Prabhu","Pai","Kulkarni","Joshi",
    "Patil","Desai","Naidu","Chetty","Mudaliar","Aiyar","Bhatt","Sharma","Verma","Gupta",
    "Singh","Kumar","Patel","Shah","Mehta","Chopra","Malhotra","Khanna","Kapoor","Arora",
    # Other South
    "Murthy","Rajan","Krishnan","Sundaram","Subramanian","Balakrishnan","Annamalai","Thiruvengadam",
    "Ramaswamy","Venkatesan","Gopalakrishnan","Natarajan","Chandrasekaran","Ramachandran","Sivaramakrishnan",
    # Bengal/East
    "Banerjee","Chatterjee","Mukherjee","Ghosh","Das","Bose","Roy","Sen","Dey","Chakraborty",
    "Ganguly","Sarkar","Mandal","Biswas","Paul","Nandi","Mondal","Chaudhury","Bhattacharya","Datta",
    # West/North
    "Jain","Agrawal","Bajaj","Birla","Maheshwari","Mittal","Khandelwal","Singhania","Oswal","Lodha",
    "Doshi","Zaveri","Sanghvi","Parekh","Modi","Trivedi","Pandya","Bhavsar","Raval","Thakkar",
    "Yadav","Mishra","Pandey","Tiwari","Dubey","Shukla","Srivastava","Dwivedi","Tripathi","Chaturvedi",
    "Awasthi","Bajpai","Upadhyay","Chauhan","Rajput","Rathore","Shekhawat","Bhati","Tanwar","Sisodia",
    "Ahlawat","Dagar","Hooda","Khatri","Saini","Dhull","Sangwan","Beniwal","Phogat","Godara",
    # Punjab
    "Gill","Grewal","Sandhu","Sidhu","Dhaliwal","Dhillon","Brar","Mann","Sekhon","Virk",
    "Randhawa","Sohal","Toor","Kang","Thind","Nijjar","Bains","Hayer","Pannu","Deol",
    # Maharashtra
    "Shinde","Jadhav","Pawar","More","Bhosale","Thorat","Kale","Deshpande","Phadke","Gokhale",
    "Apte","Limaye","Marathe","Ranade","Savarkar","Tilak","Dalvi","Gawde","Salunkhe","Waghmare",
    "Kamble","Mane","Patil","Bhalerao","Kshirsagar","Jog","Vedak","Datar","Chitale","Gupte",
    # Tamil Nadu
    "Arunachalam","Duraisamy","Govindasamy","Karuppusamy","Muthusamy","Palaniswamy","Ramasamy","Shanmugam",
    "Subramaniam","Thirumeni","Veerasamy","Arumugam","Chidambaram","Devarajan","Ganesan","Hariharan",
    # Additional
    "Abraham","George","Thomas","Philip","Mathew","Joseph","John","James","Peter","Paul",
    "Xavier","Fernandes","D'Souza","Pereira","Noronha","Pinto","Monteiro","Sequeira","Rodrigues","Gomes",
]

# Business name components for SME
BIZ_PREFIXES = [
    "Aarav","Aditya","Akshara","Amrit","Anand","Apex","Arjun","Arunodaya","Arya","Ashoka",
    "Atharva","Avanti","Ayush","Bharat","Bright","Celestial","Chandra","Chetan","Crest","Crown",
    "Crystal","Dakshin","Deep","Delta","Devi","Dharma","Dhruv","Disha","Dynamic","Eagle",
    "Eastern","Elite","Emerald","Empire","Excel","First","Fortune","Galaxy","Ganesh","Garuda",
    "Global","Gold","Golden","Gopala","Green","Guru","Harmony","Himalaya","Horizon","Indra",
    "Indus","Infinity","Innova","Inspire","Integrated","Jain","Jayalakshmi","Jyoti","Kailash","Kalpa",
    "Kamala","Karthikeya","Kaveri","Keystone","Konkan","Krishna","Lakshmi","Landmark","Legend","Link",
    "Lotus","Madhav","Mahindra","Majestic","Malabar","Maruthi","Matrix","Maxim","Mega","Metro",
    "Modern","Mukunda","Nandana","National","Nature","Navadurga","Naveen","Next","Noble","Omega",
    "Omni","One","Pacific","Padmavathi","Peak","Pioneer","Prabhu","Pragati","Prakash","Premier",
    "Pride","Prime","Pro","Progressive","Pushpa","Quality","Radha","Raj","Raja","Rajendra",
    "Rajguru","Rajlakshmi","Ranjit","Ravi","Reliance","Rich","Riddhi","Rising","Royal","Sagar",
    "Sahyadri","Samrudhi","Saraswati","Sarvam","Satyam","Savita","Shakti","Shankar","Shiva","Shree",
    "Shri","Siddhi","Silicon","Sky","Smart","Sri","Standard","Star","Sterling","Summit",
    "Sunrise","Superior","Supreme","Supriya","Surya","Swift","Synergy","Tech","Techno","Triumph",
    "Tulasi","Uma","United","Universal","Usha","Vaishnavi","Vajra","Vega","Venkat","Vidya",
    "Vijay","Vikas","Vishnu","Vista","Vivek","Western","White","Wisdom","World","Yashoda",
    "Zenith","Zest","Alpha","Beta","Gamma","Sigma","Titan","Turbo","Ultra","Venture",
]

BIZ_SUFFIXES = [
    "Solutions","Enterprises","Industries","Exports","Manufacturing","Traders","Foods",
    "Fashions","Technologies","Systems","Services","Logistics","Infrastructure","Projects",
    "Constructions","International","Chemicals","Pharmaceuticals","Textiles","Agro",
    "Motors","Electronics","Electricals","Engineering","Consultancy","Finance","Realty",
    "Builders","Developers","Healthcare","Hospital","Diagnostics","Labs","Research",
    "Packaging","Plastics","Polymers","Metals","Steel","Alloys","Castings","Forgings",
    "Auto Components","Spares","Accessories","Garments","Apparels","Yarns","Fabrics",
    "Paper","Print","Media","Studios","Events","Advertising","Marketing","Digital",
    "Software","Infotech","Telecom","Networks","Security","Automation","Robotics","Power",
]

BIZ_TYPES = ["Pvt Ltd", "LLP", "& Co", "Associates", "Group", "Co-op", "OPC Pvt Ltd", "Pvt Ltd"]

# ─────────────────────────────────────────────────────────────────────────────
# Geography & reference data
# ─────────────────────────────────────────────────────────────────────────────
# (city, weight, state_code)
CITY_DATA = [
    ("Bengaluru", 45, "29"), ("Mumbai", 10, "27"), ("Delhi", 9, "07"),
    ("Hyderabad", 7, "36"), ("Chennai", 6, "33"), ("Pune", 5, "27"),
    ("Ahmedabad", 4, "24"), ("Kolkata", 3, "19"), ("Coimbatore", 2, "33"),
    ("Indore", 2, "23"), ("Surat", 2, "24"), ("Nagpur", 1, "27"),
    ("Jaipur", 1, "08"), ("Lucknow", 1, "09"), ("Bhopal", 1, "23"),
    ("Kochi", 1, "32"),
]
CITIES_LIST   = [c[0] for c in CITY_DATA]
CITY_WEIGHTS  = [c[1] for c in CITY_DATA]
STATE_CODES   = {c[0]: c[2] for c in CITY_DATA}

INDUSTRIES = [
    "IT / Software Services","Manufacturing","Retail Trade","Textiles & Garments",
    "Food Processing","Pharmaceuticals","Construction","Automobile Components",
    "Logistics","Agriculture","Healthcare","E-commerce","Education",
    "Chemicals","Steel & Metals","Printing & Packaging","Real Estate","Hospitality",
]
INDUSTRY_WEIGHTS = [20,16,13,11,9,8,7,6,5,3,2,2,1,1,1,1,1,1]

LOAN_PURPOSES_RETAIL = [
    "Home renovation","Vehicle purchase","Personal expenses","Wedding",
    "Medical emergency","Education","Debt consolidation","Travel","Business expansion",
    "Consumer durables","Home appliances","Solar panel installation",
]
LOAN_PURPOSES_SME = [
    "Business expansion","Machinery purchase","Working capital","Invoice financing",
    "Shop renovation","Inventory purchase","New branch setup","Technology upgrade",
    "Export financing","Project finance","Capacity expansion","Trade finance",
]
EMPLOYMENT_TYPES = ["salaried","self_employed_professional","self_employed_non_professional"]
GENDERS = ["M","F","O"]
EMAIL_DOMAINS = ["gmail.com","outlook.com","yahoo.co.in","rediffmail.com","hotmail.com"]

RETAIL_LOAN_TYPES = ["personal_loan","home_loan","auto_loan","gold_loan","education_loan"]
SME_LOAN_TYPES    = ["term_loan","working_capital","equipment_finance","invoice_discounting","project_finance"]

# ─────────────────────────────────────────────────────────────────────────────
# Helper generators
# ─────────────────────────────────────────────────────────────────────────────

def fake_pan():
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return (
        "".join(random.choices(letters, k=5)) +
        str(random.randint(1000, 9999)) +
        random.choice(letters)
    )

def fake_mobile():
    return f"9{random.randint(100000000, 999999999)}"

def fake_email(name_part: str, idx: int) -> str:
    clean = name_part.lower().replace(" ", ".").replace("'", "")
    return f"{clean}{idx}@{random.choice(EMAIL_DOMAINS)}"

def fake_gstin(city: str, pan: str) -> str:
    state = STATE_CODES.get(city, "29")
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"{state}{pan[:5]}{random.randint(1000,9999)}{random.choice(letters)}Z{random.choice(letters)}"

def fake_date_of_birth(age: int) -> str:
    year = datetime.now().year - age
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"

def fake_loan_account():
    return f"LA{random.randint(10000000, 99999999)}"

def random_date_in_past(days_back=730) -> str:
    d = datetime.now() - timedelta(days=random.randint(0, days_back))
    return d.strftime("%Y-%m-%d")

# ─────────────────────────────────────────────────────────────────────────────
# Unique name generators
# ─────────────────────────────────────────────────────────────────────────────

def build_unique_retail_names(count: int):
    """Generate `count` unique full names for retail applicants."""
    used = set()
    names = []
    i = 0
    while len(names) < count:
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        # add a middle initial when name space is exhausted
        if i > len(FIRST_NAMES) * len(LAST_NAMES) * 0.6:
            mid_initial = random.choice("ABCDEFGHJKLMNPRSTV") + "."
            full = f"{first} {mid_initial} {last}"
        else:
            full = f"{first} {last}"
        if full not in used:
            used.add(full)
            names.append(full)
        i += 1
    return names

def build_unique_sme_names(count: int):
    """Generate `count` unique business names for SME applicants."""
    used = set()
    names = []
    i = 0
    while len(names) < count:
        prefix  = random.choice(BIZ_PREFIXES)
        suffix  = random.choice(BIZ_SUFFIXES)
        btype   = random.choice(BIZ_TYPES)
        if i > len(BIZ_PREFIXES) * len(BIZ_SUFFIXES) * 0.5:
            # add a city qualifier to break collisions
            city_q = random.choice(["India","Global","Group","International","National"])
            full = f"{prefix} {suffix} {city_q} {btype}".strip()
        else:
            full = f"{prefix} {suffix} {btype}".strip()
        if full not in used:
            used.add(full)
            names.append(full)
        i += 1
    return names

# ─────────────────────────────────────────────────────────────────────────────
# Record generators
# ─────────────────────────────────────────────────────────────────────────────

def generate_retail_applicant(idx: int, name: str) -> dict:
    city    = random.choices(CITIES_LIST, weights=CITY_WEIGHTS, k=1)[0]
    lt      = random.choices(
        RETAIL_LOAN_TYPES,
        weights=[35, 30, 20, 10, 5], k=1
    )[0]
    emp     = random.choice(EMPLOYMENT_TYPES)
    age     = random.randint(22, 60)
    gender  = random.choice(GENDERS)
    pan     = fake_pan()

    # Income bands
    income_band = random.choices([1, 2, 3], weights=[45, 38, 17], k=1)[0]
    if income_band == 1:
        income = random.randint(22000, 65000)
    elif income_band == 2:
        income = random.randint(65001, 150000)
    else:
        income = random.randint(150001, 400000)

    if lt == "home_loan":
        loan_amt = random.randint(10, 80) * 100000
        tenure   = random.choice([120, 180, 240, 300])
    elif lt == "auto_loan":
        loan_amt = random.randint(3, 20) * 100000
        tenure   = random.choice([36, 48, 60, 72])
    elif lt == "gold_loan":
        loan_amt = random.randint(5, 25) * 10000
        tenure   = random.choice([6, 12, 18, 24])
    elif lt == "education_loan":
        loan_amt = random.randint(5, 30) * 100000
        tenure   = random.choice([60, 84, 120])
    else:
        loan_amt = random.randint(1, 25) * 100000
        tenure   = random.choice([12, 24, 36, 48, 60])

    cibil  = random.choices(
        list(range(550, 900)),
        weights=[1 if s < 650 else 3 if s < 700 else 5 if s < 750 else 8 if s < 800 else 6
                 for s in range(550, 900)],
        k=1
    )[0]
    existing_emi = random.randint(0, income // 3)
    rate = round(random.uniform(9.5, 18.5), 2)

    return {
        "id":               f"RET-{idx:06d}",
        "application_id":   f"RET-{idx:06d}",
        "name":             name,
        "full_name":        name,
        "pan":              pan,
        "mobile":           fake_mobile(),
        "email":            fake_email(name.split()[0], idx),
        "gender":           gender,
        "age":              age,
        "date_of_birth":    fake_date_of_birth(age),
        "cibil":            cibil,
        "cibil_score":      cibil,
        "monthly_income":   income,
        "loan_amt":         loan_amt,
        "loan_amount_requested": loan_amt,
        "tenure_months":    tenure,
        "existing_emi":     existing_emi,
        "type":             lt,
        "loan_type":        lt,
        "city":             city,
        "employment_type":  emp,
        "loan_purpose":     random.choice(LOAN_PURPOSES_RETAIL),
        "indicative_rate":  rate,
        "property_type":    random.choice(["ready_to_move","under_construction"]) if lt == "home_loan" else None,
        "created":          random_date_in_past(730),
    }


def generate_sme_applicant(idx: int, name: str) -> dict:
    city    = random.choices(CITIES_LIST, weights=CITY_WEIGHTS, k=1)[0]
    lt      = random.choices(
        SME_LOAN_TYPES,
        weights=[35, 30, 15, 12, 8], k=1
    )[0]
    pan     = fake_pan()
    gstin   = fake_gstin(city, pan)

    turnover_band = random.choices([1, 2, 3], weights=[42, 40, 18], k=1)[0]
    if turnover_band == 1:
        turnover = random.randint(15, 55) * 100000
    elif turnover_band == 2:
        turnover = random.randint(55, 220) * 100000
    else:
        turnover = random.randint(220, 950) * 100000

    loan_amt = random.randint(5, max(6, int(turnover * 0.6 / 100000))) * 100000
    loan_amt = min(loan_amt, int(turnover * 1.5))

    vintage = random.randint(2, 22)
    cibil   = random.choices(
        list(range(550, 900)),
        weights=[1 if s < 620 else 2 if s < 650 else 4 if s < 700 else 7 if s < 750 else 9 if s < 800 else 5
                 for s in range(550, 900)],
        k=1
    )[0]

    collateral = (
        0 if lt in ["working_capital", "invoice_discounting"]
        else round(turnover * random.uniform(0.4, 1.5), -4)
    )
    industry = random.choices(INDUSTRIES, weights=INDUSTRY_WEIGHTS, k=1)[0]

    # Promoter name (unique combination)
    promoter_first = random.choice(FIRST_NAMES)
    promoter_last  = random.choice(LAST_NAMES)
    promoter_name  = f"{promoter_first} {promoter_last}"

    return {
        "id":                     f"SME-{idx:06d}",
        "application_id":         f"SME-{idx:06d}",
        "name":                   name,
        "business_name":          name,
        "pan":                    pan,
        "gstin":                  gstin,
        "mobile":                 fake_mobile(),
        "email":                  fake_email(name.split()[0].lower(), idx),
        "promoter_name":          promoter_name,
        "promoter_cibil_score":   cibil,
        "cibil":                  cibil,
        "annual_turnover":        turnover,
        "turnover":               turnover,
        "loan_amt":               loan_amt,
        "loan_amount_requested":  loan_amt,
        "business_vintage_years": vintage,
        "vintage":                vintage,
        "type":                   lt,
        "loan_type":              lt,
        "collateral":             collateral,
        "collateral_value":       collateral,
        "city":                   city,
        "industry":               industry,
        "loan_purpose":           random.choice(LOAN_PURPOSES_SME),
        "created":                random_date_in_past(730),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_and_save(count: int = 10000):
    print(f"🔄  Generating {count:,} Retail applicants with unique names …")
    retail_names = build_unique_retail_names(count)
    retail_list  = [generate_retail_applicant(i + 1, retail_names[i]) for i in range(count)]

    print(f"🔄  Generating {count:,} SME applicants with unique business names …")
    sme_names = build_unique_sme_names(count)
    sme_list  = [generate_sme_applicant(i + 1, sme_names[i]) for i in range(count)]

    # ── JSON output ──────────────────────────────────────────────────────────
    with open("retail_applicants.json", "w", encoding="utf-8") as f:
        json.dump(retail_list, f, indent=2, ensure_ascii=False)
    with open("sme_applicants.json", "w", encoding="utf-8") as f:
        json.dump(sme_list, f, indent=2, ensure_ascii=False)

    # ── CSV output ───────────────────────────────────────────────────────────
    retail_fields = [
        "id","application_id","name","full_name","pan","mobile","email","gender",
        "age","date_of_birth","cibil","cibil_score","monthly_income","loan_amt",
        "loan_amount_requested","tenure_months","existing_emi","type","loan_type",
        "city","employment_type","loan_purpose","indicative_rate","property_type","created"
    ]
    with open("retail_applicants.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=retail_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(retail_list)

    sme_fields = [
        "id","application_id","name","business_name","pan","gstin","mobile","email",
        "promoter_name","promoter_cibil_score","cibil","annual_turnover","turnover",
        "loan_amt","loan_amount_requested","business_vintage_years","vintage",
        "type","loan_type","collateral","collateral_value","city","industry",
        "loan_purpose","created"
    ]
    with open("sme_applicants.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sme_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sme_list)

    # ── Summary ──────────────────────────────────────────────────────────────
    bengaluru_r = sum(1 for a in retail_list if a["city"] == "Bengaluru")
    bengaluru_s = sum(1 for a in sme_list   if a["city"] == "Bengaluru")
    print(f"\n✅  Done!")
    print(f"   Retail: {len(retail_list):,} records  ({bengaluru_r:,} Bengaluru = {bengaluru_r*100//count}%)")
    print(f"   SME:    {len(sme_list):,} records  ({bengaluru_s:,} Bengaluru = {bengaluru_s*100//count}%)")
    print(f"\n   Files written:")
    print(f"   • retail_applicants.json  ({len(retail_list):,} rows)")
    print(f"   • sme_applicants.json     ({len(sme_list):,} rows)")
    print(f"   • retail_applicants.csv   ({len(retail_list):,} rows)")
    print(f"   • sme_applicants.csv      ({len(sme_list):,} rows)")
    print(f"\n   All names are unique ✔")


if __name__ == "__main__":
    generate_and_save(10000)
