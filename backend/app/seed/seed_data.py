"""
Seed data generator for LoanProspect AI CRM.
Generates 75 realistic Indian banking customers with full transaction history.

Run via:  python -m app.seed.run_seed
"""

import calendar
import json
import random
import uuid
from datetime import date, datetime, timedelta

from app.db.database import get_db_context
from app.db.models import (
    AuditLog,
    Campaign,
    ChatMessage,
    ChatSession,
    Customer,
    CustomerAccount,
    LoanSignal,
    OutreachHistory,
    ProductHolding,
    RMNote,
    Transaction,
)
from sqlalchemy import select

random.seed(42)

# ─── Reference date ───────────────────────────────────────────────────────────

TODAY = date.today()

# ─── Merchant lists ───────────────────────────────────────────────────────────

GROCERY_MERCHANTS = [
    "BigBasket",
    "Blinkit",
    "Zepto",
    "Reliance Fresh",
    "DMart",
    "Swiggy Instamart",
    "Spencer's",
    "Grofers",
]
RESTAURANT_MERCHANTS = [
    "Zomato",
    "Swiggy",
    "Barbeque Nation",
    "McDonald's",
    "Haldirams",
    "Cafe Coffee Day",
    "Domino's",
    "KFC",
    "Pizza Hut",
    "Starbucks",
    "Burger King",
    "Subway",
]
SHOPPING_MERCHANTS = [
    "Amazon",
    "Flipkart",
    "Myntra",
    "Ajio",
    "Meesho",
    "Nykaa",
    "H&M",
    "Zara",
    "Lifestyle",
    "Reliance Trends",
    "Pantaloons",
]
TRAVEL_MERCHANTS = [
    "MakeMyTrip",
    "IRCTC",
    "IndiGo",
    "Air India",
    "Ola",
    "Uber",
    "Rapido",
    "RedBus",
    "Goibibo",
    "Yatra",
    "EaseMyTrip",
]
MEDICAL_MERCHANTS = [
    "Apollo Pharmacy",
    "Medplus",
    "Fortis Hospital",
    "Max Healthcare",
    "Apollo Hospitals",
    "Practo",
    "Netmeds",
    "1mg",
    "Manipal Hospital",
]
RENOVATION_MERCHANTS = [
    "Asian Paints",
    "Pidilite",
    "Havells",
    "Kajaria Tiles",
    "Sleek Kitchen",
    "Godrej Interio",
    "Urban Ladder",
    "IKEA",
    "Pepperfry",
    "HomeLane",
]
EDUCATION_MERCHANTS = [
    "BYJU's",
    "Unacademy",
    "Coursera",
    "NTA Portal",
    "School Fee Portal",
    "College Fee Portal",
    "Vedantu",
    "upGrad",
]
INSURANCE_MERCHANTS = [
    "LIC",
    "HDFC Life",
    "ICICI Prudential",
    "Max Life",
    "SBI Life",
    "Bajaj Allianz",
    "Tata AIA",
]
INVESTMENT_MERCHANTS = [
    "Zerodha",
    "Groww",
    "Upstox",
    "Kuvera",
    "SBI MF",
    "HDFC MF",
    "ICICI Direct",
    "Mirae Asset",
]
FUEL_MERCHANTS = ["HPCL", "BPCL", "Indian Oil", "Shell", "Reliance BP"]
UTILITY_MERCHANTS = [
    "BESCOM",
    "MSEB",
    "Airtel",
    "Jio",
    "BSNL",
    "Hathway",
    "Tata Power",
    "Adani Electricity",
    "DU",
]
ELECTRONICS_MERCHANTS = [
    "Croma",
    "Vijay Sales",
    "Reliance Digital",
    "Apple Store",
    "Samsung Store",
    "Flipkart Electronics",
]
SUBSCRIPTION_MERCHANTS = [
    "Netflix",
    "Amazon Prime",
    "Disney+ Hotstar",
    "Spotify",
    "YouTube Premium",
    "ZEE5",
    "SonyLIV",
]
WEDDING_MERCHANTS = [
    "Grand Palace Wedding Venue",
    "Royal Catering Services",
    "Bridal House",
    "Photography Studio",
    "Event Management Co.",
    "DJ Services",
    "Flower Decorations",
    "Wedding Card Printing",
    "Band Baja Baraat",
]
FAMILY_MERCHANTS = [
    "NEFT - Family Transfer",
    "UPI - Parents Support",
    "PhonePe - Family",
    "Google Pay - Home",
]

# City → (min_rent, max_rent) in INR/month
CITY_RENT = {
    "Mumbai": (22000, 75000),
    "Delhi": (16000, 60000),
    "Bangalore": (16000, 52000),
    "Hyderabad": (13000, 40000),
    "Pune": (13000, 42000),
    "Chennai": (11000, 36000),
    "Kolkata": (10000, 28000),
    "Ahmedabad": (9000, 26000),
    "Jaipur": (7000, 20000),
    "Indore": (6000, 18000),
}

# ─── Customer definitions (75 customers) ─────────────────────────────────────
#
# Keys:
#   customer_id, full_name, age, gender, city, occupation, employment_type,
#   annual_income, credit_score_proxy, account_tenure_months, consent_marketing,
#   risk_segment, rm_assigned, dependents, kyc_status,
#   profile_type, account_type, start_balance,
#   pays_rent, has_home_loan, has_car_loan
#
# profile_type drives transaction generation:
#   high_intent_medical / high_intent_renovation / high_intent_education /
#   high_intent_wedding / tech_salaried / self_employed_doctor /
#   self_employed_ca / self_employed_lawyer / self_employed_architect /
#   business_owner / young_professional / deposit_heavy /
#   lifestyle_spender / dormant / high_risk

CUSTOMERS_DATA = [
    # ── HIGH-PRIORITY LOAN PROSPECTS (CUST001-CUST015) ───────────────────────
    {
        "customer_id": "CUST001",
        "full_name": "Aarav Sharma",
        "age": 32,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1500000,
        "credit_score_proxy": 760,
        "account_tenure_months": 48,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_intent_medical",
        "account_type": "salary",
        "start_balance": 480000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST002",
        "full_name": "Priya Patel",
        "age": 29,
        "gender": "F",
        "city": "Pune",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 1800000,
        "credit_score_proxy": 742,
        "account_tenure_months": 36,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "high_intent_education",
        "account_type": "salary",
        "start_balance": 520000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST003",
        "full_name": "Rohit Verma",
        "age": 35,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "banker",
        "employment_type": "salaried",
        "annual_income": 1200000,
        "credit_score_proxy": 722,
        "account_tenure_months": 60,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_intent_renovation",
        "account_type": "savings",
        "start_balance": 380000,
        "pays_rent": False,
        "has_home_loan": True,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST004",
        "full_name": "Sneha Gupta",
        "age": 34,
        "gender": "F",
        "city": "Delhi",
        "occupation": "consultant",
        "employment_type": "salaried",
        "annual_income": 1600000,
        "credit_score_proxy": 755,
        "account_tenure_months": 42,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "high_intent_wedding",
        "account_type": "savings",
        "start_balance": 620000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST005",
        "full_name": "Vikram Singh",
        "age": 38,
        "gender": "M",
        "city": "Hyderabad",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 2000000,
        "credit_score_proxy": 780,
        "account_tenure_months": 72,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_intent_medical",
        "account_type": "salary",
        "start_balance": 750000,
        "pays_rent": False,
        "has_home_loan": True,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST006",
        "full_name": "Kavya Nair",
        "age": 31,
        "gender": "F",
        "city": "Chennai",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 1100000,
        "credit_score_proxy": 712,
        "account_tenure_months": 30,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "high_intent_education",
        "account_type": "salary",
        "start_balance": 280000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST007",
        "full_name": "Rahul Joshi",
        "age": 37,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 2200000,
        "credit_score_proxy": 770,
        "account_tenure_months": 54,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_intent_renovation",
        "account_type": "savings",
        "start_balance": 680000,
        "pays_rent": False,
        "has_home_loan": True,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST008",
        "full_name": "Tanvi Mehta",
        "age": 33,
        "gender": "F",
        "city": "Pune",
        "occupation": "marketing manager",
        "employment_type": "salaried",
        "annual_income": 950000,
        "credit_score_proxy": 700,
        "account_tenure_months": 38,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_intent_medical",
        "account_type": "savings",
        "start_balance": 240000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST009",
        "full_name": "Amit Kumar",
        "age": 40,
        "gender": "M",
        "city": "Delhi",
        "occupation": "sales manager",
        "employment_type": "salaried",
        "annual_income": 1300000,
        "credit_score_proxy": 730,
        "account_tenure_months": 66,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_intent_education",
        "account_type": "savings",
        "start_balance": 420000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST010",
        "full_name": "Ananya Iyer",
        "age": 28,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1400000,
        "credit_score_proxy": 745,
        "account_tenure_months": 24,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "high_intent_wedding",
        "account_type": "salary",
        "start_balance": 350000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST011",
        "full_name": "Karthik Reddy",
        "age": 36,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1700000,
        "credit_score_proxy": 765,
        "account_tenure_months": 58,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_intent_renovation",
        "account_type": "savings",
        "start_balance": 540000,
        "pays_rent": False,
        "has_home_loan": True,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST012",
        "full_name": "Meera Pillai",
        "age": 32,
        "gender": "F",
        "city": "Chennai",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 650000,
        "credit_score_proxy": 695,
        "account_tenure_months": 44,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_intent_medical",
        "account_type": "savings",
        "start_balance": 185000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST013",
        "full_name": "Arjun Rao",
        "age": 39,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "consultant",
        "employment_type": "salaried",
        "annual_income": 2500000,
        "credit_score_proxy": 790,
        "account_tenure_months": 78,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_intent_renovation",
        "account_type": "savings",
        "start_balance": 920000,
        "pays_rent": False,
        "has_home_loan": True,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST014",
        "full_name": "Riya Mishra",
        "age": 27,
        "gender": "F",
        "city": "Delhi",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 980000,
        "credit_score_proxy": 705,
        "account_tenure_months": 22,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "high_intent_education",
        "account_type": "salary",
        "start_balance": 210000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST015",
        "full_name": "Ishaan Shah",
        "age": 34,
        "gender": "M",
        "city": "Ahmedabad",
        "occupation": "banker",
        "employment_type": "salaried",
        "annual_income": 1100000,
        "credit_score_proxy": 725,
        "account_tenure_months": 40,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-004",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_intent_wedding",
        "account_type": "savings",
        "start_balance": 320000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── SALARIED TECH PROFESSIONALS (CUST016-CUST027) ─────────────────────────
    {
        "customer_id": "CUST016",
        "full_name": "Nikhil Desai",
        "age": 28,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 2000000,
        "credit_score_proxy": 755,
        "account_tenure_months": 30,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 620000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST017",
        "full_name": "Swati Jain",
        "age": 30,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 1400000,
        "credit_score_proxy": 735,
        "account_tenure_months": 42,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 380000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST018",
        "full_name": "Tarun Agarwal",
        "age": 32,
        "gender": "M",
        "city": "Pune",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1800000,
        "credit_score_proxy": 760,
        "account_tenure_months": 48,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 520000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST019",
        "full_name": "Kapil Malhotra",
        "age": 29,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 2200000,
        "credit_score_proxy": 770,
        "account_tenure_months": 36,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 720000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST020",
        "full_name": "Nidhi Kapoor",
        "age": 27,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 1200000,
        "credit_score_proxy": 720,
        "account_tenure_months": 24,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 310000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST021",
        "full_name": "Rohan Bhat",
        "age": 31,
        "gender": "M",
        "city": "Pune",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1600000,
        "credit_score_proxy": 750,
        "account_tenure_months": 44,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 460000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST022",
        "full_name": "Shruti Shetty",
        "age": 26,
        "gender": "F",
        "city": "Bangalore",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 1000000,
        "credit_score_proxy": 710,
        "account_tenure_months": 18,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 220000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST023",
        "full_name": "Mohit Naik",
        "age": 33,
        "gender": "M",
        "city": "Hyderabad",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 2500000,
        "credit_score_proxy": 780,
        "account_tenure_months": 54,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 820000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST024",
        "full_name": "Divya Saxena",
        "age": 30,
        "gender": "F",
        "city": "Pune",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 1900000,
        "credit_score_proxy": 758,
        "account_tenure_months": 40,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 580000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST025",
        "full_name": "Sai Chatterjee",
        "age": 28,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1500000,
        "credit_score_proxy": 740,
        "account_tenure_months": 32,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 420000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST026",
        "full_name": "Reyansh Mukherjee",
        "age": 32,
        "gender": "M",
        "city": "Hyderabad",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 2100000,
        "credit_score_proxy": 768,
        "account_tenure_months": 46,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 680000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST027",
        "full_name": "Pooja Sen",
        "age": 29,
        "gender": "F",
        "city": "Pune",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 1300000,
        "credit_score_proxy": 728,
        "account_tenure_months": 34,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "tech_salaried",
        "account_type": "salary",
        "start_balance": 340000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── SELF-EMPLOYED PROFESSIONALS (CUST028-CUST037) ─────────────────────────
    {
        "customer_id": "CUST028",
        "full_name": "Rajesh Sharma",
        "age": 45,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "doctor",
        "employment_type": "self-employed",
        "annual_income": 4500000,
        "credit_score_proxy": 810,
        "account_tenure_months": 120,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_doctor",
        "account_type": "savings",
        "start_balance": 1800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST029",
        "full_name": "Kavita Verma",
        "age": 42,
        "gender": "F",
        "city": "Delhi",
        "occupation": "doctor",
        "employment_type": "self-employed",
        "annual_income": 3800000,
        "credit_score_proxy": 800,
        "account_tenure_months": 96,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "self_employed_doctor",
        "account_type": "savings",
        "start_balance": 1500000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST030",
        "full_name": "Sanjay Patel",
        "age": 48,
        "gender": "M",
        "city": "Ahmedabad",
        "occupation": "CA",
        "employment_type": "self-employed",
        "annual_income": 2800000,
        "credit_score_proxy": 795,
        "account_tenure_months": 108,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_ca",
        "account_type": "savings",
        "start_balance": 950000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST031",
        "full_name": "Sunita Gupta",
        "age": 40,
        "gender": "F",
        "city": "Mumbai",
        "occupation": "CA",
        "employment_type": "self-employed",
        "annual_income": 2200000,
        "credit_score_proxy": 785,
        "account_tenure_months": 84,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "self_employed_ca",
        "account_type": "savings",
        "start_balance": 720000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST032",
        "full_name": "Vijay Singh",
        "age": 50,
        "gender": "M",
        "city": "Delhi",
        "occupation": "lawyer",
        "employment_type": "self-employed",
        "annual_income": 3500000,
        "credit_score_proxy": 805,
        "account_tenure_months": 132,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_lawyer",
        "account_type": "savings",
        "start_balance": 1200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST033",
        "full_name": "Anita Kumar",
        "age": 44,
        "gender": "F",
        "city": "Bangalore",
        "occupation": "lawyer",
        "employment_type": "self-employed",
        "annual_income": 2600000,
        "credit_score_proxy": 788,
        "account_tenure_months": 90,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "self_employed_lawyer",
        "account_type": "savings",
        "start_balance": 880000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST034",
        "full_name": "Manoj Joshi",
        "age": 47,
        "gender": "M",
        "city": "Hyderabad",
        "occupation": "architect",
        "employment_type": "self-employed",
        "annual_income": 3000000,
        "credit_score_proxy": 792,
        "account_tenure_months": 102,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_architect",
        "account_type": "savings",
        "start_balance": 1050000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST035",
        "full_name": "Rekha Mehta",
        "age": 43,
        "gender": "F",
        "city": "Mumbai",
        "occupation": "doctor",
        "employment_type": "self-employed",
        "annual_income": 4200000,
        "credit_score_proxy": 808,
        "account_tenure_months": 98,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_doctor",
        "account_type": "savings",
        "start_balance": 1650000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST036",
        "full_name": "Girish Nair",
        "age": 46,
        "gender": "M",
        "city": "Chennai",
        "occupation": "CA",
        "employment_type": "self-employed",
        "annual_income": 2400000,
        "credit_score_proxy": 782,
        "account_tenure_months": 110,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "self_employed_ca",
        "account_type": "savings",
        "start_balance": 820000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST037",
        "full_name": "Lakshmi Iyer",
        "age": 41,
        "gender": "F",
        "city": "Bangalore",
        "occupation": "architect",
        "employment_type": "self-employed",
        "annual_income": 2800000,
        "credit_score_proxy": 789,
        "account_tenure_months": 88,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-001",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "self_employed_architect",
        "account_type": "savings",
        "start_balance": 980000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── BUSINESS OWNERS / ENTREPRENEURS (CUST038-CUST045) ────────────────────
    {
        "customer_id": "CUST038",
        "full_name": "Sunil Reddy",
        "age": 52,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "business owner",
        "employment_type": "business",
        "annual_income": 7500000,
        "credit_score_proxy": 820,
        "account_tenure_months": 144,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 3,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 4500000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST039",
        "full_name": "Mohan Pillai",
        "age": 48,
        "gender": "M",
        "city": "Delhi",
        "occupation": "entrepreneur",
        "employment_type": "business",
        "annual_income": 5000000,
        "credit_score_proxy": 812,
        "account_tenure_months": 120,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 2800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST040",
        "full_name": "Rajan Menon",
        "age": 55,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "business owner",
        "employment_type": "business",
        "annual_income": 8000000,
        "credit_score_proxy": 825,
        "account_tenure_months": 168,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 5200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST041",
        "full_name": "Harish Rao",
        "age": 50,
        "gender": "M",
        "city": "Delhi",
        "occupation": "entrepreneur",
        "employment_type": "business",
        "annual_income": 6000000,
        "credit_score_proxy": 815,
        "account_tenure_months": 132,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 3600000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST042",
        "full_name": "Deepa Mishra",
        "age": 45,
        "gender": "F",
        "city": "Mumbai",
        "occupation": "business owner",
        "employment_type": "business",
        "annual_income": 4500000,
        "credit_score_proxy": 805,
        "account_tenure_months": 108,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 2200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST043",
        "full_name": "Smita Banerjee",
        "age": 47,
        "gender": "F",
        "city": "Delhi",
        "occupation": "entrepreneur",
        "employment_type": "business",
        "annual_income": 3500000,
        "credit_score_proxy": 798,
        "account_tenure_months": 100,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 1800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST044",
        "full_name": "Ayaan Das",
        "age": 43,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "business owner",
        "employment_type": "business",
        "annual_income": 6500000,
        "credit_score_proxy": 818,
        "account_tenure_months": 116,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 3800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST045",
        "full_name": "Pranav Shah",
        "age": 49,
        "gender": "M",
        "city": "Ahmedabad",
        "occupation": "entrepreneur",
        "employment_type": "business",
        "annual_income": 5500000,
        "credit_score_proxy": 813,
        "account_tenure_months": 124,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "business_owner",
        "account_type": "current",
        "start_balance": 3200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    # ── YOUNG PROFESSIONALS (CUST046-CUST053) ─────────────────────────────────
    {
        "customer_id": "CUST046",
        "full_name": "Aarav Desai",
        "age": 23,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 900000,
        "credit_score_proxy": 680,
        "account_tenure_months": 12,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 85000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST047",
        "full_name": "Vivaan Jain",
        "age": 24,
        "gender": "M",
        "city": "Hyderabad",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 750000,
        "credit_score_proxy": 665,
        "account_tenure_months": 14,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 62000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST048",
        "full_name": "Priya Agarwal",
        "age": 22,
        "gender": "F",
        "city": "Pune",
        "occupation": "marketing manager",
        "employment_type": "salaried",
        "annual_income": 650000,
        "credit_score_proxy": 655,
        "account_tenure_months": 10,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 45000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST049",
        "full_name": "Ishaan Malhotra",
        "age": 25,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 1000000,
        "credit_score_proxy": 695,
        "account_tenure_months": 18,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 120000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST050",
        "full_name": "Riya Kapoor",
        "age": 26,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 1100000,
        "credit_score_proxy": 702,
        "account_tenure_months": 20,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 145000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST051",
        "full_name": "Aryan Bhat",
        "age": 24,
        "gender": "M",
        "city": "Pune",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 850000,
        "credit_score_proxy": 675,
        "account_tenure_months": 15,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 72000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST052",
        "full_name": "Nisha Shetty",
        "age": 23,
        "gender": "F",
        "city": "Bangalore",
        "occupation": "data analyst",
        "employment_type": "salaried",
        "annual_income": 700000,
        "credit_score_proxy": 660,
        "account_tenure_months": 11,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-001",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 55000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST053",
        "full_name": "Tanvi Naik",
        "age": 27,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "consultant",
        "employment_type": "salaried",
        "annual_income": 1200000,
        "credit_score_proxy": 708,
        "account_tenure_months": 22,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "young_professional",
        "account_type": "salary",
        "start_balance": 180000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── DEPOSIT-HEAVY CUSTOMERS (CUST054-CUST060) ─────────────────────────────
    {
        "customer_id": "CUST054",
        "full_name": "Girish Saxena",
        "age": 55,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "government employee",
        "employment_type": "salaried",
        "annual_income": 1200000,
        "credit_score_proxy": 745,
        "account_tenure_months": 240,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 2800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST055",
        "full_name": "Sunita Chatterjee",
        "age": 52,
        "gender": "F",
        "city": "Delhi",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 800000,
        "credit_score_proxy": 728,
        "account_tenure_months": 216,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 1900000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST056",
        "full_name": "Rajesh Mukherjee",
        "age": 58,
        "gender": "M",
        "city": "Kolkata",
        "occupation": "government employee",
        "employment_type": "salaried",
        "annual_income": 1100000,
        "credit_score_proxy": 750,
        "account_tenure_months": 264,
        "consent_marketing": False,
        "risk_segment": "low",
        "rm_assigned": "RM-005",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 3200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST057",
        "full_name": "Rekha Sen",
        "age": 54,
        "gender": "F",
        "city": "Mumbai",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 750000,
        "credit_score_proxy": 732,
        "account_tenure_months": 228,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 1650000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST058",
        "full_name": "Mohan Sharma",
        "age": 60,
        "gender": "M",
        "city": "Chennai",
        "occupation": "government employee",
        "employment_type": "salaried",
        "annual_income": 1300000,
        "credit_score_proxy": 755,
        "account_tenure_months": 288,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-003",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 3800000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST059",
        "full_name": "Anita Verma",
        "age": 57,
        "gender": "F",
        "city": "Kolkata",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 900000,
        "credit_score_proxy": 738,
        "account_tenure_months": 252,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-005",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 2200000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST060",
        "full_name": "Vijay Patel",
        "age": 56,
        "gender": "M",
        "city": "Ahmedabad",
        "occupation": "banker",
        "employment_type": "salaried",
        "annual_income": 1400000,
        "credit_score_proxy": 748,
        "account_tenure_months": 252,
        "consent_marketing": True,
        "risk_segment": "low",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "deposit_heavy",
        "account_type": "savings",
        "start_balance": 2600000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── HIGH-SPEND LIFESTYLE CUSTOMERS (CUST061-CUST066) ─────────────────────
    {
        "customer_id": "CUST061",
        "full_name": "Kapil Singh",
        "age": 34,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "sales manager",
        "employment_type": "salaried",
        "annual_income": 2000000,
        "credit_score_proxy": 720,
        "account_tenure_months": 60,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 280000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST062",
        "full_name": "Swati Kumar",
        "age": 31,
        "gender": "F",
        "city": "Delhi",
        "occupation": "marketing manager",
        "employment_type": "salaried",
        "annual_income": 1800000,
        "credit_score_proxy": 715,
        "account_tenure_months": 48,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 220000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST063",
        "full_name": "Rohan Gupta",
        "age": 35,
        "gender": "M",
        "city": "Bangalore",
        "occupation": "product manager",
        "employment_type": "salaried",
        "annual_income": 2500000,
        "credit_score_proxy": 730,
        "account_tenure_months": 66,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-001",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 380000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST064",
        "full_name": "Divya Joshi",
        "age": 30,
        "gender": "F",
        "city": "Mumbai",
        "occupation": "consultant",
        "employment_type": "salaried",
        "annual_income": 2200000,
        "credit_score_proxy": 718,
        "account_tenure_months": 52,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 240000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST065",
        "full_name": "Tarun Mehta",
        "age": 33,
        "gender": "M",
        "city": "Delhi",
        "occupation": "software engineer",
        "employment_type": "salaried",
        "annual_income": 2000000,
        "credit_score_proxy": 722,
        "account_tenure_months": 58,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-003",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 310000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": True,
    },
    {
        "customer_id": "CUST066",
        "full_name": "Pooja Nair",
        "age": 29,
        "gender": "F",
        "city": "Hyderabad",
        "occupation": "marketing manager",
        "employment_type": "salaried",
        "annual_income": 1600000,
        "credit_score_proxy": 712,
        "account_tenure_months": 42,
        "consent_marketing": True,
        "risk_segment": "medium",
        "rm_assigned": "RM-002",
        "dependents": 0,
        "kyc_status": "verified",
        "profile_type": "lifestyle_spender",
        "account_type": "savings",
        "start_balance": 195000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── DORMANT CUSTOMERS (CUST067-CUST071) ───────────────────────────────────
    {
        "customer_id": "CUST067",
        "full_name": "Manoj Iyer",
        "age": 45,
        "gender": "M",
        "city": "Jaipur",
        "occupation": "sales manager",
        "employment_type": "salaried",
        "annual_income": 800000,
        "credit_score_proxy": 665,
        "account_tenure_months": 84,
        "consent_marketing": False,
        "risk_segment": "medium",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "dormant",
        "account_type": "savings",
        "start_balance": 42000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST068",
        "full_name": "Kavita Reddy",
        "age": 42,
        "gender": "F",
        "city": "Indore",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 600000,
        "credit_score_proxy": 650,
        "account_tenure_months": 72,
        "consent_marketing": False,
        "risk_segment": "medium",
        "rm_assigned": "RM-005",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "dormant",
        "account_type": "savings",
        "start_balance": 28000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST069",
        "full_name": "Sunil Pillai",
        "age": 50,
        "gender": "M",
        "city": "Jaipur",
        "occupation": "government employee",
        "employment_type": "salaried",
        "annual_income": 900000,
        "credit_score_proxy": 670,
        "account_tenure_months": 96,
        "consent_marketing": False,
        "risk_segment": "medium",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "dormant",
        "account_type": "savings",
        "start_balance": 55000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST070",
        "full_name": "Smita Menon",
        "age": 48,
        "gender": "F",
        "city": "Indore",
        "occupation": "teacher",
        "employment_type": "salaried",
        "annual_income": 700000,
        "credit_score_proxy": 658,
        "account_tenure_months": 88,
        "consent_marketing": False,
        "risk_segment": "medium",
        "rm_assigned": "RM-005",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "dormant",
        "account_type": "savings",
        "start_balance": 35000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST071",
        "full_name": "Sanjay Saxena",
        "age": 55,
        "gender": "M",
        "city": "Jaipur",
        "occupation": "banker",
        "employment_type": "salaried",
        "annual_income": 1000000,
        "credit_score_proxy": 672,
        "account_tenure_months": 120,
        "consent_marketing": False,
        "risk_segment": "medium",
        "rm_assigned": "RM-004",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "dormant",
        "account_type": "savings",
        "start_balance": 68000,
        "pays_rent": False,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    # ── HIGH-RISK CUSTOMERS (CUST072-CUST075) ─────────────────────────────────
    {
        "customer_id": "CUST072",
        "full_name": "Rahul Chatterjee",
        "age": 38,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "entrepreneur",
        "employment_type": "business",
        "annual_income": 2500000,
        "credit_score_proxy": 580,
        "account_tenure_months": 42,
        "consent_marketing": False,
        "risk_segment": "high",
        "rm_assigned": "RM-002",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_risk",
        "account_type": "savings",
        "start_balance": 45000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST073",
        "full_name": "Nisha Mukherjee",
        "age": 35,
        "gender": "F",
        "city": "Delhi",
        "occupation": "sales manager",
        "employment_type": "salaried",
        "annual_income": 1200000,
        "credit_score_proxy": 565,
        "account_tenure_months": 36,
        "consent_marketing": False,
        "risk_segment": "high",
        "rm_assigned": "RM-003",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_risk",
        "account_type": "savings",
        "start_balance": 32000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST074",
        "full_name": "Mohit Sen",
        "age": 40,
        "gender": "M",
        "city": "Kolkata",
        "occupation": "business owner",
        "employment_type": "business",
        "annual_income": 3000000,
        "credit_score_proxy": 560,
        "account_tenure_months": 48,
        "consent_marketing": False,
        "risk_segment": "high",
        "rm_assigned": "RM-005",
        "dependents": 2,
        "kyc_status": "verified",
        "profile_type": "high_risk",
        "account_type": "savings",
        "start_balance": 28000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
    {
        "customer_id": "CUST075",
        "full_name": "Reyansh Sharma",
        "age": 36,
        "gender": "M",
        "city": "Mumbai",
        "occupation": "consultant",
        "employment_type": "salaried",
        "annual_income": 1800000,
        "credit_score_proxy": 570,
        "account_tenure_months": 40,
        "consent_marketing": False,
        "risk_segment": "high",
        "rm_assigned": "RM-002",
        "dependents": 1,
        "kyc_status": "verified",
        "profile_type": "high_risk",
        "account_type": "savings",
        "start_balance": 38000,
        "pays_rent": True,
        "has_home_loan": False,
        "has_car_loan": False,
    },
]

assert len(CUSTOMERS_DATA) == 75, f"Expected 75 customers, got {len(CUSTOMERS_DATA)}"

# ─── Helper functions ─────────────────────────────────────────────────────────


def _phone(cid: str) -> str:
    """Deterministic phone number from customer ID."""
    n = int(cid.replace("CUST", ""))
    base = 7000000000 + n * 9871
    return str(base % 10000000000).zfill(10)


def _email(name: str, cid: str) -> str:
    slug = name.lower().replace(" ", ".").replace("'", "")
    n = int(cid.replace("CUST", ""))
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com"]
    return f"{slug}{n}@{domains[n % len(domains)]}"


def _last_contact(profile: str, base_ago_days: int) -> date:
    if profile == "dormant":
        return TODAY - timedelta(days=random.randint(90, 170))
    return TODAY - timedelta(days=random.randint(1, 30))


def _rand_date(
    year: int, month: int, day_min: int = 1, day_max: int | None = None
) -> date:
    max_day = calendar.monthrange(year, month)[1]
    if day_max is None or day_max > max_day:
        day_max = max_day
    day_min = max(1, min(day_min, day_max))
    return date(year, month, random.randint(day_min, day_max))


def _months_back(n: int) -> list[tuple[int, int]]:
    """Return list of (year, month) tuples for last n months, oldest first."""
    result = []
    for i in range(n - 1, -1, -1):
        m = TODAY.month - i
        y = TODAY.year
        while m <= 0:
            m += 12
            y -= 1
        result.append((y, m))
    return result


# ─── Transaction generation ────────────────────────────────────────────────────


def generate_transactions(
    c: dict,
    account_id: str,
) -> tuple[list[dict], float, float, float, float]:
    """
    Build a realistic 6-month transaction history.

    Returns:
        (txn_list, final_balance, avg_monthly_balance, monthly_inflow, monthly_outflow)
    """
    profile = c["profile_type"]
    emp_type = c["employment_type"]
    monthly_income = c["annual_income"] / 12
    city = c["city"]
    cid = c["customer_id"]
    balance = float(c["start_balance"])

    all_txns: list[dict] = []
    monthly_credits: list[float] = []
    monthly_debits: list[float] = []

    rent_lo, rent_hi = CITY_RENT.get(city, (10000, 28000))
    monthly_rent = random.uniform(rent_lo, rent_hi)

    home_emi = (
        monthly_income * random.uniform(0.22, 0.35) if c.get("has_home_loan") else 0.0
    )
    car_emi = (
        monthly_income * random.uniform(0.08, 0.13) if c.get("has_car_loan") else 0.0
    )
    personal_loan_emi = (
        (monthly_income * random.uniform(0.22, 0.38)) if profile == "high_risk" else 0.0
    )

    # Month index at which the "big special" transaction happens (for high_intent profiles)
    special_month_idx = random.randint(2, 4)
    special_done = False

    def add(
        txn_date: date,
        txn_type: str,
        category: str,
        amount: float,
        channel: str,
        merchant: str | None = None,
        desc: str | None = None,
        recurring: bool = False,
    ) -> bool:
        nonlocal balance
        amount = round(max(amount, 1.0), 2)
        if txn_type == "debit":
            # For high-risk allow slight overdraft; others keep min balance
            min_bal = -5000 if profile == "high_risk" else 2000
            if balance - amount < min_bal:
                return False
            balance = round(balance - amount, 2)
        else:
            balance = round(balance + amount, 2)

        all_txns.append(
            {
                "transaction_id": str(uuid.uuid4()),
                "customer_id": cid,
                "account_id": account_id,
                "txn_date": txn_date,
                "txn_type": txn_type,
                "category": category,
                "amount": amount,
                "balance_after": balance,
                "channel": channel,
                "merchant_name": merchant,
                "description": desc,
                "is_recurring": recurring,
            }
        )
        return True

    for month_idx, (year, month) in enumerate(_months_back(6)):
        max_day = calendar.monthrange(year, month)[1]
        is_current = year == TODAY.year and month == TODAY.month
        last_day = TODAY.day if is_current else max_day
        if last_day < 1:
            continue

        slice_start = len(all_txns)

        # ── DORMANT: minimal activity ──────────────────────────────────────────
        if profile == "dormant":
            # Only in the first 3 months and rarely
            if month_idx < 3:
                if random.random() < 0.65:
                    d = random.randint(1, last_day)
                    add(
                        date(year, month, d),
                        "debit",
                        "cash_withdrawal",
                        random.uniform(5000, 20000),
                        "atm",
                        "ATM Withdrawal",
                        "Cash Withdrawal",
                    )
                if random.random() < 0.25 and last_day >= 2:
                    d = random.randint(1, min(5, last_day))
                    add(
                        date(year, month, d),
                        "credit",
                        "salary",
                        monthly_income,
                        "netbanking",
                        "Employer",
                        "Monthly Salary",
                        True,
                    )
            slice_txns = all_txns[slice_start:]
            monthly_credits.append(
                sum(t["amount"] for t in slice_txns if t["txn_type"] == "credit")
            )
            monthly_debits.append(
                sum(t["amount"] for t in slice_txns if t["txn_type"] == "debit")
            )
            continue

        # ── INCOME ────────────────────────────────────────────────────────────
        if emp_type == "salaried":
            sal_day = random.randint(1, min(5, last_day))
            sal_amount = monthly_income * random.uniform(0.97, 1.03)
            add(
                date(year, month, sal_day),
                "credit",
                "salary",
                sal_amount,
                "netbanking",
                "Employer NEFT",
                "Monthly Salary Credit",
                True,
            )
            # Occasional bonus (5 % chance)
            if random.random() < 0.05 and last_day >= 10:
                bd = random.randint(10, last_day)
                add(
                    date(year, month, bd),
                    "credit",
                    "salary",
                    sal_amount * random.uniform(0.4, 1.5),
                    "netbanking",
                    "Employer NEFT",
                    "Performance Bonus",
                )

        elif emp_type == "self-employed":
            n_inc = random.randint(1, 3)
            for _ in range(n_inc):
                if last_day < 5:
                    continue
                d = random.randint(5, last_day)
                inc = (monthly_income * random.uniform(0.4, 2.0)) / max(n_inc, 1)
                add(
                    date(year, month, d),
                    "credit",
                    "business_income",
                    inc,
                    "neft",
                    random.choice(
                        ["Client Payment", "Consulting Fee", "Professional Fee"]
                    ),
                    "Professional Income",
                )

        elif emp_type == "business":
            n_inc = random.randint(1, 5)
            for _ in range(n_inc):
                if last_day < 3:
                    continue
                d = random.randint(3, last_day)
                inc = (monthly_income * random.uniform(0.3, 2.5)) / max(n_inc, 1)
                add(
                    date(year, month, d),
                    "credit",
                    "business_income",
                    inc,
                    "neft",
                    "Business Account",
                    "Business Revenue Transfer",
                )

        # ── FIXED MONTHLY EXPENSES ────────────────────────────────────────────

        # Rent
        if c.get("pays_rent") and last_day >= 3:
            rd = random.randint(2, min(7, last_day))
            add(
                date(year, month, rd),
                "debit",
                "rent",
                monthly_rent,
                "netbanking",
                "Landlord",
                "Monthly Rent",
                True,
            )

        # Home loan EMI
        if home_emi > 0 and last_day >= 5:
            ed = random.randint(5, min(10, last_day))
            add(
                date(year, month, ed),
                "debit",
                "EMI",
                home_emi,
                "netbanking",
                "HDFC Home Loan EMI",
                "Home Loan EMI",
                True,
            )

        # Car loan EMI
        if car_emi > 0 and last_day >= 7:
            ed = random.randint(7, min(12, last_day))
            add(
                date(year, month, ed),
                "debit",
                "EMI",
                car_emi,
                "netbanking",
                "Car Loan EMI",
                "Car Loan EMI",
                True,
            )

        # Personal loan EMI (high-risk)
        if personal_loan_emi > 0 and last_day >= 8:
            ed = random.randint(8, min(15, last_day))
            add(
                date(year, month, ed),
                "debit",
                "EMI",
                personal_loan_emi,
                "netbanking",
                "Personal Loan EMI",
                "Personal Loan EMI",
                True,
            )
            # Extra credit card payment for high-risk
            if random.random() < 0.6 and last_day >= 15:
                cd = random.randint(12, min(20, last_day))
                add(
                    date(year, month, cd),
                    "debit",
                    "EMI",
                    random.uniform(8000, 25000),
                    "netbanking",
                    "Credit Card Payment",
                    "Credit Card Bill",
                    True,
                )

        # Utilities
        if last_day >= 8:
            ud = random.randint(8, min(15, last_day))
            add(
                date(year, month, ud),
                "debit",
                "utilities",
                random.uniform(2000, 7000),
                "upi",
                random.choice(UTILITY_MERCHANTS),
                "Utility Bill",
                True,
            )

        # Subscription
        if random.random() < 0.82 and last_day >= 2:
            sd = random.randint(1, min(5, last_day))
            add(
                date(year, month, sd),
                "debit",
                "subscription",
                random.uniform(200, 1500),
                "netbanking",
                random.choice(SUBSCRIPTION_MERCHANTS),
                "Subscription",
                True,
            )

        # Insurance (every 3 months or randomly)
        if month_idx % 3 == 0 and random.random() < 0.75:
            id_ = random.randint(10, last_day) if last_day >= 10 else last_day
            add(
                date(year, month, id_),
                "debit",
                "insurance",
                random.uniform(3000, 20000),
                "netbanking",
                random.choice(INSURANCE_MERCHANTS),
                "Insurance Premium",
                True,
            )

        # ── GROCERY (4-7 visits per month) ────────────────────────────────────
        n_groc = random.randint(4, 7)
        if last_day >= n_groc:
            groc_days = sorted(
                random.sample(range(1, last_day + 1), min(n_groc, last_day))
            )
            for gd in groc_days:
                add(
                    date(year, month, gd),
                    "debit",
                    "grocery",
                    random.uniform(600, 3800),
                    random.choice(["upi", "pos"]),
                    random.choice(GROCERY_MERCHANTS),
                    "Grocery Shopping",
                )

        # ── RESTAURANT ────────────────────────────────────────────────────────
        n_rest_map = {
            "lifestyle_spender": (12, 22),
            "tech_salaried": (7, 15),
            "young_professional": (8, 14),
            "deposit_heavy": (1, 4),
            "high_risk": (2, 7),
        }
        rest_lo, rest_hi = n_rest_map.get(profile, (4, 10))
        n_rest = random.randint(rest_lo, rest_hi)
        rest_amt_range = (1000, 8000) if profile == "lifestyle_spender" else (300, 3500)
        for _ in range(n_rest):
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "restaurant",
                random.uniform(*rest_amt_range),
                random.choice(["upi", "pos"]),
                random.choice(RESTAURANT_MERCHANTS),
                "Food / Dining",
            )

        # ── SHOPPING ─────────────────────────────────────────────────────────
        n_shop_map = {
            "lifestyle_spender": (6, 12),
            "young_professional": (3, 8),
            "tech_salaried": (2, 6),
            "deposit_heavy": (0, 2),
            "high_risk": (1, 4),
            "dormant": (0, 0),
        }
        slo, shi = n_shop_map.get(profile, (1, 5))
        n_shop = random.randint(slo, shi)
        shop_amt_map = {
            "lifestyle_spender": (2000, 28000),
            "tech_salaried": (1000, 18000),
            "business_owner": (2000, 20000),
            "young_professional": (500, 8000),
            "deposit_heavy": (500, 5000),
            "high_risk": (500, 6000),
        }
        salo, sahi = shop_amt_map.get(profile, (1000, 12000))
        for _ in range(n_shop):
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "shopping",
                random.uniform(salo, sahi),
                random.choice(["upi", "pos", "netbanking"]),
                random.choice(SHOPPING_MERCHANTS),
                "Online / Retail Shopping",
            )

        # ── FUEL ─────────────────────────────────────────────────────────────
        if random.random() < 0.72 and last_day >= 3:
            n_fuel = random.randint(1, 3)
            for _ in range(n_fuel):
                d = random.randint(1, last_day)
                add(
                    date(year, month, d),
                    "debit",
                    "fuel",
                    random.uniform(1200, 4500),
                    "pos",
                    random.choice(FUEL_MERCHANTS),
                    "Fuel",
                )

        # ── INVESTMENT ───────────────────────────────────────────────────────
        if profile in ("deposit_heavy", "tech_salaried") and last_day >= 5:
            inv_d = random.randint(5, min(15, last_day))
            inv_amt_map = {
                "deposit_heavy": (25000, 90000),
                "tech_salaried": (5000, 35000),
            }
            ilo, ihi = inv_amt_map.get(profile, (5000, 20000))
            add(
                date(year, month, inv_d),
                "debit",
                "investment",
                random.uniform(ilo, ihi),
                "netbanking",
                random.choice(INVESTMENT_MERCHANTS),
                "SIP / MF Investment",
                True,
            )
        elif (
            emp_type in ("self-employed", "business")
            and random.random() < 0.4
            and last_day >= 5
        ):
            inv_d = random.randint(5, last_day)
            add(
                date(year, month, inv_d),
                "debit",
                "investment",
                random.uniform(15000, 120000),
                "netbanking",
                random.choice(INVESTMENT_MERCHANTS),
                "Investment",
            )

        # ── TRAVEL ───────────────────────────────────────────────────────────
        if profile == "lifestyle_spender" and random.random() < 0.78:
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "travel",
                random.uniform(8000, 55000),
                random.choice(["netbanking", "upi"]),
                random.choice(TRAVEL_MERCHANTS),
                "Travel Booking",
            )
        elif random.random() < 0.14:
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "travel",
                random.uniform(2000, 18000),
                random.choice(["netbanking", "upi"]),
                random.choice(TRAVEL_MERCHANTS),
                "Travel",
            )

        # ── UPI TRANSFERS ─────────────────────────────────────────────────────
        if random.random() < 0.38:
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "upi_transfer",
                random.uniform(500, 15000),
                "upi",
                "PhonePe / GPay",
                "UPI Transfer",
            )

        # ── FAMILY SUPPORT ────────────────────────────────────────────────────
        if c.get("dependents", 0) > 0 and random.random() < 0.28:
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "family_support",
                random.uniform(5000, 35000),
                "upi",
                random.choice(FAMILY_MERCHANTS),
                "Family Support / Remittance",
            )

        # ── BUSINESS EXPENSES ─────────────────────────────────────────────────
        if emp_type in ("self-employed", "business"):
            n_biz = random.randint(2, 6)
            for _ in range(n_biz):
                d = random.randint(1, last_day)
                bcat = random.choice(["upi_transfer", "shopping", "utilities"])
                add(
                    date(year, month, d),
                    "debit",
                    bcat,
                    random.uniform(5000, 80000),
                    "neft",
                    "Business Vendor",
                    "Business Expense",
                )

        # ── HIGH-RISK: ATM cash withdrawal ────────────────────────────────────
        if profile == "high_risk" and random.random() < 0.55:
            d = random.randint(1, last_day)
            add(
                date(year, month, d),
                "debit",
                "cash_withdrawal",
                random.uniform(10000, 45000),
                "atm",
                "ATM",
                "Cash Withdrawal",
            )

        # ── HIGH-INTENT SPECIAL TRANSACTION ──────────────────────────────────
        if (
            profile.startswith("high_intent_")
            and not special_done
            and month_idx == special_month_idx
        ):
            intent = profile.replace("high_intent_", "")

            if intent == "medical":
                med_d = random.randint(10, min(25, last_day))
                add(
                    date(year, month, med_d),
                    "debit",
                    "medical",
                    random.uniform(80000, 300000),
                    "netbanking",
                    random.choice(MEDICAL_MERCHANTS),
                    "Medical Treatment / Surgery",
                )
                if last_day > med_d:
                    pd = random.randint(med_d + 1, last_day)
                    add(
                        date(year, month, pd),
                        "debit",
                        "medical",
                        random.uniform(5000, 30000),
                        "upi",
                        "Apollo Pharmacy",
                        "Post-treatment Medicines",
                    )
                special_done = True

            elif intent == "renovation":
                n_ren = random.randint(3, 6)
                ren_total = random.uniform(150000, 500000)
                for _ in range(n_ren):
                    rd = random.randint(1, last_day)
                    add(
                        date(year, month, rd),
                        "debit",
                        "home_renovation",
                        (ren_total / n_ren) * random.uniform(0.6, 1.4),
                        "netbanking",
                        random.choice(RENOVATION_MERCHANTS),
                        "Home Renovation",
                    )
                special_done = True

            elif intent == "education":
                edu_d = random.randint(1, min(20, last_day))
                add(
                    date(year, month, edu_d),
                    "debit",
                    "education",
                    random.uniform(60000, 200000),
                    "netbanking",
                    random.choice(EDUCATION_MERCHANTS),
                    "Education Fee Payment",
                )
                if random.random() < 0.5 and last_day > edu_d:
                    ed2 = random.randint(edu_d + 1, last_day)
                    add(
                        date(year, month, ed2),
                        "debit",
                        "education",
                        random.uniform(20000, 80000),
                        "netbanking",
                        random.choice(EDUCATION_MERCHANTS),
                        "Study Material / Exam Fee",
                    )
                special_done = True

            elif intent == "wedding":
                n_wed = random.randint(3, 6)
                wed_total = random.uniform(150000, 400000)
                for _ in range(n_wed):
                    wd = random.randint(1, last_day)
                    add(
                        date(year, month, wd),
                        "debit",
                        "wedding",
                        (wed_total / n_wed) * random.uniform(0.5, 1.5),
                        "netbanking",
                        random.choice(WEDDING_MERCHANTS),
                        "Wedding Expense",
                    )
                special_done = True

        # ── Track monthly stats ───────────────────────────────────────────────
        slice_txns = all_txns[slice_start:]
        monthly_credits.append(
            sum(t["amount"] for t in slice_txns if t["txn_type"] == "credit")
        )
        monthly_debits.append(
            sum(t["amount"] for t in slice_txns if t["txn_type"] == "debit")
        )

    # Sort chronologically
    all_txns.sort(key=lambda x: x["txn_date"])

    final_balance = balance
    avg_monthly_balance = round((c["start_balance"] + final_balance) / 2, 2)
    monthly_inflow = round(sum(monthly_credits) / max(len(monthly_credits), 1), 2)
    monthly_outflow = round(sum(monthly_debits) / max(len(monthly_debits), 1), 2)

    return all_txns, final_balance, avg_monthly_balance, monthly_inflow, monthly_outflow


# ─── Product holdings generation ─────────────────────────────────────────────


def generate_product_holdings(c: dict) -> list[dict]:
    profile = c["profile_type"]
    cid = c["customer_id"]
    mi = c["annual_income"] / 12  # monthly income
    tenure = c["account_tenure_months"]

    def _h(
        product_type: str,
        status: str = "active",
        outstanding: float = 0.0,
        limit_amount: float = 0.0,
        emi: float = 0.0,
        months_ago: int | None = None,
    ) -> dict:
        if months_ago is None:
            months_ago = random.randint(6, min(tenure, 60))
        sd = TODAY - timedelta(days=months_ago * 30)
        return {
            "holding_id": str(uuid.uuid4()),
            "customer_id": cid,
            "product_type": product_type,
            "product_status": status,
            "outstanding_amount": round(outstanding, 2),
            "limit_amount": round(limit_amount, 2),
            "emi_amount": round(emi, 2),
            "start_date": sd,
        }

    holdings: list[dict] = []

    # All customers have their primary account product
    acc_type = (
        "savings_account"
        if c["account_type"] in ("savings", "salary")
        else "current_account"
    )
    holdings.append(_h(acc_type))

    if profile.startswith("high_intent_"):
        # Deliberately NO personal_loan – that's the gap we want to fill
        pool = ["credit_card", "fd", "mutual_fund", "insurance", "car_loan"]
        chosen = random.sample(pool, random.randint(1, 3))
        for p in chosen:
            if p == "credit_card":
                lim = mi * random.uniform(1, 3)
                holdings.append(
                    _h(p, outstanding=lim * random.uniform(0.1, 0.45), limit_amount=lim)
                )
            elif p == "fd":
                amt = mi * random.uniform(3, 10)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            elif p == "mutual_fund":
                amt = mi * random.uniform(4, 14)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            elif p == "car_loan" and c.get("has_car_loan"):
                out = mi * random.uniform(6, 18)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.08, 0.13))
                )
            else:
                holdings.append(_h(p))
        if c.get("has_home_loan"):
            out = mi * random.uniform(24, 60)
            holdings.append(
                _h("home_loan", outstanding=out, emi=mi * random.uniform(0.22, 0.35))
            )

    elif profile == "tech_salaried":
        pool = ["credit_card", "fd", "mutual_fund", "insurance", "car_loan"]
        chosen = random.sample(pool, random.randint(2, 4))
        for p in chosen:
            if p == "credit_card":
                lim = mi * random.uniform(1.5, 3.5)
                holdings.append(
                    _h(p, outstanding=lim * random.uniform(0.1, 0.4), limit_amount=lim)
                )
            elif p == "car_loan":
                out = mi * random.uniform(8, 20)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.09, 0.15))
                )
            elif p in ("fd", "mutual_fund"):
                amt = mi * random.uniform(4, 18)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            else:
                holdings.append(_h(p))

    elif profile in (
        "self_employed_doctor",
        "self_employed_ca",
        "self_employed_lawyer",
        "self_employed_architect",
    ):
        pool = [
            "credit_card",
            "fd",
            "mutual_fund",
            "insurance",
            "home_loan",
            "car_loan",
        ]
        chosen = random.sample(pool, random.randint(2, 4))
        for p in chosen:
            if p == "credit_card":
                lim = mi * random.uniform(2, 6)
                holdings.append(
                    _h(p, outstanding=lim * random.uniform(0.05, 0.3), limit_amount=lim)
                )
            elif p == "home_loan":
                out = mi * random.uniform(36, 84)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.20, 0.35))
                )
            elif p == "car_loan":
                out = mi * random.uniform(10, 30)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.09, 0.16))
                )
            elif p in ("fd", "mutual_fund"):
                amt = mi * random.uniform(12, 40)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            else:
                holdings.append(_h(p))

    elif profile == "business_owner":
        pool = [
            "credit_card",
            "fd",
            "home_loan",
            "car_loan",
            "insurance",
            "mutual_fund",
        ]
        chosen = random.sample(pool, random.randint(3, 5))
        for p in chosen:
            if p == "credit_card":
                lim = mi * random.uniform(3, 9)
                holdings.append(
                    _h(p, outstanding=lim * random.uniform(0.1, 0.5), limit_amount=lim)
                )
            elif p == "home_loan":
                out = mi * random.uniform(48, 120)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.15, 0.28))
                )
            elif p == "car_loan":
                out = mi * random.uniform(15, 40)
                holdings.append(
                    _h(p, outstanding=out, emi=mi * random.uniform(0.08, 0.14))
                )
            elif p in ("fd", "mutual_fund"):
                amt = mi * random.uniform(24, 72)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            else:
                holdings.append(_h(p))

    elif profile == "young_professional":
        pool = ["credit_card", "insurance", "mutual_fund"]
        chosen = random.sample(pool, random.randint(1, 2))
        for p in chosen:
            if p == "credit_card":
                lim = mi * random.uniform(0.5, 2)
                holdings.append(
                    _h(p, outstanding=lim * random.uniform(0.2, 0.65), limit_amount=lim)
                )
            elif p == "mutual_fund":
                amt = mi * random.uniform(1, 4)
                holdings.append(_h(p, outstanding=amt, limit_amount=amt))
            else:
                holdings.append(_h(p))

    elif profile == "deposit_heavy":
        n_fd = random.randint(2, 4)
        for _ in range(n_fd):
            amt = random.uniform(200000, 1200000)
            holdings.append(_h("fd", outstanding=amt, limit_amount=amt))
        mf_amt = random.uniform(500000, 2500000)
        holdings.append(_h("mutual_fund", outstanding=mf_amt, limit_amount=mf_amt))
        holdings.append(_h("insurance"))
        if random.random() < 0.35:
            out = mi * random.uniform(12, 36)
            holdings.append(_h("home_loan", outstanding=out, emi=mi * 0.18))

    elif profile == "lifestyle_spender":
        lim = mi * random.uniform(2, 6)
        out = lim * random.uniform(0.4, 0.8)
        holdings.append(_h("credit_card", outstanding=out, limit_amount=lim))
        if c.get("has_car_loan"):
            out2 = mi * random.uniform(12, 30)
            holdings.append(_h("car_loan", outstanding=out2, emi=mi * 0.12))
        if random.random() < 0.4:
            holdings.append(_h("insurance"))

    elif profile == "dormant":
        if random.random() < 0.4:
            amt = random.uniform(50000, 250000)
            holdings.append(_h("fd", outstanding=amt, limit_amount=amt))
        holdings.append(_h("insurance"))

    elif profile == "high_risk":
        # Personal loan + nearly-maxed credit card
        pl_out = mi * random.uniform(12, 30)
        holdings.append(
            _h("personal_loan", outstanding=pl_out, emi=mi * random.uniform(0.25, 0.40))
        )
        lim = mi * random.uniform(2, 4)
        holdings.append(
            _h(
                "credit_card",
                outstanding=lim * random.uniform(0.65, 0.97),
                limit_amount=lim,
            )
        )
        if random.random() < 0.4:
            out = mi * random.uniform(30, 60)
            holdings.append(
                _h("home_loan", outstanding=out, emi=mi * random.uniform(0.20, 0.32))
            )

    return holdings


# ─── Loan signal generation ───────────────────────────────────────────────────


def generate_loan_signals(c: dict, txns: list[dict]) -> list[dict]:
    profile = c["profile_type"]
    cid = c["customer_id"]
    mi = c["annual_income"] / 12
    signals: list[dict] = []

    def _sig(signal_type: str, value: float, source: str, confidence: float) -> dict:
        return {
            "signal_id": str(uuid.uuid4()),
            "customer_id": cid,
            "signal_type": signal_type,
            "signal_value": round(value, 2),
            "signal_source": source,
            "confidence_score": round(min(confidence, 1.0), 4),
            "detected_at": datetime.now() - timedelta(days=random.randint(1, 30)),
        }

    def _txn_total(category: str) -> float:
        return sum(
            t["amount"]
            for t in txns
            if t["category"] == category and t["txn_type"] == "debit"
        )

    if profile == "high_intent_medical":
        med_total = _txn_total("medical")
        signals.append(
            _sig(
                "large_medical_spend",
                med_total or mi * 2,
                "transaction_analysis",
                random.uniform(0.82, 0.96),
            )
        )
        signals.append(
            _sig(
                "stable_salary_income",
                mi,
                "income_analysis",
                random.uniform(0.88, 0.98),
            )
        )
        signals.append(
            _sig(
                "no_personal_loan_detected",
                0,
                "product_analysis",
                random.uniform(0.90, 0.98),
            )
        )

    elif profile == "high_intent_renovation":
        ren_total = _txn_total("home_renovation")
        signals.append(
            _sig(
                "home_renovation_spend",
                ren_total or mi * 3,
                "transaction_analysis",
                random.uniform(0.85, 0.96),
            )
        )
        signals.append(
            _sig(
                "stable_salary_income",
                mi,
                "income_analysis",
                random.uniform(0.87, 0.97),
            )
        )
        signals.append(
            _sig(
                "no_personal_loan_detected",
                0,
                "product_analysis",
                random.uniform(0.90, 0.98),
            )
        )

    elif profile == "high_intent_education":
        edu_total = _txn_total("education")
        signals.append(
            _sig(
                "education_fee_pattern",
                edu_total or mi * 1.5,
                "transaction_analysis",
                random.uniform(0.80, 0.94),
            )
        )
        signals.append(
            _sig(
                "stable_salary_income",
                mi,
                "income_analysis",
                random.uniform(0.87, 0.97),
            )
        )
        signals.append(
            _sig(
                "no_personal_loan_detected",
                0,
                "product_analysis",
                random.uniform(0.88, 0.97),
            )
        )

    elif profile == "high_intent_wedding":
        wed_total = _txn_total("wedding")
        signals.append(
            _sig(
                "wedding_expense_pattern",
                wed_total or mi * 2,
                "transaction_analysis",
                random.uniform(0.82, 0.95),
            )
        )
        signals.append(
            _sig(
                "stable_salary_income",
                mi,
                "income_analysis",
                random.uniform(0.86, 0.97),
            )
        )
        signals.append(
            _sig(
                "no_personal_loan_detected",
                0,
                "product_analysis",
                random.uniform(0.89, 0.97),
            )
        )

    elif profile == "tech_salaried":
        signals.append(
            _sig(
                "stable_salary_income",
                mi,
                "income_analysis",
                random.uniform(0.90, 0.99),
            )
        )
        signals.append(
            _sig(
                "low_emi_to_income_ratio",
                0.12,
                "debt_analysis",
                random.uniform(0.80, 0.92),
            )
        )

    elif profile in (
        "self_employed_doctor",
        "self_employed_ca",
        "self_employed_lawyer",
        "self_employed_architect",
    ):
        signals.append(
            _sig(
                "high_income_professional",
                mi,
                "income_analysis",
                random.uniform(0.78, 0.93),
            )
        )
        signals.append(
            _sig(
                "irregular_income_pattern",
                mi,
                "transaction_analysis",
                random.uniform(0.72, 0.86),
            )
        )

    elif profile == "business_owner":
        signals.append(
            _sig(
                "high_business_cashflow",
                mi,
                "transaction_analysis",
                random.uniform(0.77, 0.92),
            )
        )
        signals.append(
            _sig(
                "high_average_balance",
                c["start_balance"],
                "account_analysis",
                random.uniform(0.84, 0.95),
            )
        )

    elif profile == "young_professional":
        signals.append(
            _sig(
                "rising_income_trend", mi, "income_analysis", random.uniform(0.72, 0.88)
            )
        )
        if random.random() < 0.5:
            signals.append(
                _sig(
                    "education_loan_candidate",
                    1.0,
                    "profile_analysis",
                    random.uniform(0.65, 0.82),
                )
            )

    elif profile == "deposit_heavy":
        signals.append(
            _sig(
                "high_deposit_balance",
                c["start_balance"],
                "account_analysis",
                random.uniform(0.90, 0.98),
            )
        )
        signals.append(
            _sig(
                "investment_product_opportunity",
                mi,
                "portfolio_analysis",
                random.uniform(0.82, 0.93),
            )
        )

    elif profile == "lifestyle_spender":
        signals.append(
            _sig(
                "high_discretionary_spend",
                _txn_total("shopping") + _txn_total("travel"),
                "transaction_analysis",
                random.uniform(0.80, 0.93),
            )
        )
        signals.append(
            _sig(
                "elevated_credit_utilization",
                0.65,
                "credit_analysis",
                random.uniform(0.80, 0.91),
            )
        )

    elif profile == "dormant":
        signals.append(
            _sig(
                "account_dormancy_detected",
                1.0,
                "activity_analysis",
                random.uniform(0.86, 0.96),
            )
        )
        signals.append(
            _sig(
                "reactivation_opportunity",
                0.5,
                "engagement_analysis",
                random.uniform(0.68, 0.82),
            )
        )

    elif profile == "high_risk":
        signals.append(
            _sig(
                "high_emi_burden_ratio",
                0.58,
                "debt_analysis",
                random.uniform(0.82, 0.94),
            )
        )
        signals.append(
            _sig(
                "volatile_income_pattern",
                mi,
                "income_analysis",
                random.uniform(0.76, 0.90),
            )
        )
        signals.append(
            _sig(
                "low_credit_score_proxy",
                c["credit_score_proxy"],
                "credit_bureau_proxy",
                random.uniform(0.84, 0.96),
            )
        )

    # Ensure at least 1 signal
    if not signals:
        signals.append(
            _sig("customer_profiled", 1.0, "crm_system", random.uniform(0.70, 0.85))
        )

    return signals


# ─── RM Notes generation ──────────────────────────────────────────────────────

_RM_NOTES: dict[str, list[str]] = {
    "high_intent_medical": [
        "Customer recently incurred major hospital expenses. Enquired about personal loan options to cover medical bills.",
        "Stable salaried professional with good repayment track record. Medical loan is a strong match.",
        "Hospital receipts shared by customer. Good loan prospect — no existing personal loan.",
    ],
    "high_intent_renovation": [
        "Customer planning major home renovation. Has quoted ₹3–5 lakh budget. Asked about home improvement loan.",
        "Already spending on renovation materials. Likely needs additional financing. Follow up this week.",
        "Pre-approved home renovation loan can be pitched. Customer is responsive.",
    ],
    "high_intent_education": [
        "Customer is funding higher education (self/child). Asked specifically about education loan with moratorium.",
        "Education fees are high this year. Good candidate for education loan. No existing personal loan.",
        "Enquired about education loan for MBA abroad. Has 6-month salary credit history.",
    ],
    "high_intent_wedding": [
        "Family wedding coming up next quarter. Significant bookings being made. Personal loan is ideal.",
        "Wedding expenses are mounting. Customer may need ₹5–10L personal loan. Has solid repayment capacity.",
        "Proactively asked about personal loan for wedding arrangements. No existing personal loan.",
    ],
    "tech_salaried": [
        "Salaried tech professional with stable income. Good candidate for credit card limit enhancement.",
        "Customer is considering a gadget upgrade. Consumer durable loan may be relevant.",
        "High income, clean repayment history. Ideal for mutual fund or SIP cross-sell.",
    ],
    "self_employed_doctor": [
        "Doctor with established practice. High income. Can be pitched medical equipment loan or FD.",
        "Interested in expanding clinic. Business expansion loan or OD facility may be relevant.",
        "Premium customer with very strong financial profile. Wealth management referral recommended.",
    ],
    "self_employed_ca": [
        "CA with own practice. Seasonal income pattern observed. Good FD or MF candidate.",
        "Interested in investment products after tax season. Relationship deepening opportunity.",
        "Strong financial profile. Premium credit card or wealth management product appropriate.",
    ],
    "self_employed_lawyer": [
        "Senior lawyer with established practice. High and growing income.",
        "Asked about property loan for new office space expansion.",
        "Long-tenure customer. Preferred banking upgrade should be considered.",
    ],
    "self_employed_architect": [
        "Architect with project-based income. Cash flow can be irregular — OD facility may help.",
        "Enquired about business loan for office equipment setup.",
        "Good repayment discipline on existing products. Relationship in good standing.",
    ],
    "business_owner": [
        "Business owner with strong cash flow. Potential for working capital or business loan.",
        "Has multiple business transactions. Could benefit from trade finance or current account upgrade.",
        "Premium customer. Wealth management introduction meeting should be scheduled.",
    ],
    "young_professional": [
        "New to banking — recently opened account. Strong future potential. Cross-sell insurance and SIP.",
        "Young professional at a reputed company. Should be nurtured as long-term customer.",
        "Entry-level income but from top employer. Premium account upgrade in 12 months.",
    ],
    "deposit_heavy": [
        "Long-tenure conservative investor. Has significant FD portfolio. Offer better FD rates proactively.",
        "Prefers fixed income products. Premium senior citizen FD scheme may be relevant soon.",
        "Excellent savings behaviour. Low churn risk. Suitable for wealth advisory introduction.",
    ],
    "lifestyle_spender": [
        "High spender with significant credit card usage. Limit enhancement may reduce churn risk.",
        "Frequent traveller. Premium travel credit card with lounge access could be offered.",
        "High lifestyle expenses. Balance transfer from other bank credit cards could be pitched.",
    ],
    "dormant": [
        "Account has been inactive for several months. WhatsApp reactivation campaign recommended.",
        "Customer not responding to calls. Try email and SMS. Account review pending.",
        "Low balance dormant account. Re-engagement offer (zero-balance waiver, cashback) may help.",
    ],
    "high_risk": [
        "Multiple active EMIs observed. Debt consolidation loan proposal may help customer.",
        "Credit score proxy is low. Flag for enhanced monitoring. Do not offer unsecured loans.",
        "Irregular income and payment delays flagged. Escalate to risk team if pattern continues.",
    ],
}


def generate_rm_notes(c: dict) -> list[dict]:
    profile = c["profile_type"]
    cid = c["customer_id"]
    pool = _RM_NOTES.get(profile, ["General follow-up required.", "Customer reviewed."])
    n = random.randint(1, 2)
    chosen = random.sample(pool, min(n, len(pool)))
    return [
        {
            "note_id": str(uuid.uuid4()),
            "customer_id": cid,
            "rm_id": c["rm_assigned"],
            "note_text": text,
            "created_at": datetime.now() - timedelta(days=random.randint(1, 60)),
        }
        for text in chosen
    ]


# ─── Outreach history generation ──────────────────────────────────────────────

_OUTREACH_MSGS: dict[str, list[str]] = {
    "high_intent_medical": [
        "Dear {name}, we noticed recent medical expenses on your account. Our Medical Personal Loan offers up to ₹10 Lakhs at 10.5% p.a. — no collateral, funds in 24 hours. Reply YES to learn more.",
        "Hi {name}, managing large hospital bills can be stressful. Our Quick Medical Loan ensures instant funds with flexible EMIs. Interested? Call 1800-XXX-XXXX or reply YES.",
    ],
    "high_intent_renovation": [
        "Dear {name}, planning a home renovation? Our Home Renovation Loan offers up to ₹20 Lakhs at competitive rates with EMIs as low as ₹2,100/lakh. Pre-approved for you! Reply YES.",
        "Hi {name}, your dream home awaits! Our renovation loan can fund your makeover. Zero processing fee this month. Call us or reply YES to proceed.",
    ],
    "high_intent_education": [
        "Dear {name}, invest in education with our Education Loan — up to ₹15 Lakhs, no collateral for amounts up to ₹7.5L, tax benefits under 80E. Apply today!",
        "Hi {name}, education is the best investment. Our loan covers tuition, books, and living expenses. 0% interest during the course period. Reply YES for details.",
    ],
    "high_intent_wedding": [
        "Dear {name}, congratulations on the upcoming celebration! Our Wedding Loan offers up to ₹15 Lakhs at 10.99% p.a. — make your special day unforgettable. Reply YES.",
        "Hi {name}, make your family celebrations grand! Pre-approved personal loan up to ₹10 Lakhs with instant disbursal. WhatsApp YES to proceed.",
    ],
    "tech_salaried": [
        "Hi {name}, your credit card limit enhancement is approved! New limit: ₹{limit}. Activate benefits including 5X reward points on electronics and travel.",
        "Dear {name}, exclusive offer for you: Pre-approved personal loan at 11.25% p.a. up to ₹5 Lakhs. No paperwork. 100% digital process. Reply YES.",
    ],
    "deposit_heavy": [
        "Dear {name}, our Flexi-Deposit scheme offers 7.8% p.a. on FD with quarterly payouts. Based on your savings profile, you qualify for our premium FD. Interested?",
        "Hi {name}, your loyalty means the world to us. Exclusive Senior Citizen FD rate of 8.0% p.a. now available. Contact your RM to book today.",
    ],
    "lifestyle_spender": [
        "Hi {name}, upgrade to our Platinum Travel Card! Unlimited airport lounge access, 5X miles on travel, and zero forex charges. You're pre-approved!",
        "Dear {name}, your spending pattern qualifies you for our Premium Cashback Card — 5% on dining, 3% on travel, and ₹1,000 welcome bonus. Apply now!",
    ],
    "dormant": [
        "Hi {name}, we miss you! Reactivate your account and get ₹500 cashback on your next 3 transactions. Zero maintenance fee waiver for 6 months. We're here for you.",
        "Dear {name}, your account has been inactive. We have exciting offers waiting for you. Visit your nearest branch or call 1800-XXX-XXXX to reconnect.",
    ],
}


def generate_outreach(c: dict, campaign_ids: list[str]) -> list[dict]:
    profile = c["profile_type"]
    cid = c["customer_id"]
    name = c["full_name"].split()[0]  # first name

    # High-risk and dormant (without consent) get no outreach
    if profile == "high_risk" or not c.get("consent_marketing", True):
        return []

    msgs = _OUTREACH_MSGS.get(profile, [])
    if not msgs:
        return []

    n = random.randint(0, min(2, len(msgs)))
    if n == 0:
        return []

    chosen_msgs = random.sample(msgs, n)
    channels = ["whatsapp", "email", "sms"]
    records = []
    for msg in chosen_msgs:
        text = msg.replace("{name}", name).replace(
            "{limit}", str(random.randint(5, 15) * 10000)
        )
        camp_id = random.choice(campaign_ids) if campaign_ids else None
        records.append(
            {
                "outreach_id": str(uuid.uuid4()),
                "customer_id": cid,
                "campaign_id": camp_id,
                "channel": random.choice(channels),
                "message_text": text,
                "generated_by_agent": "OutreachWriterAgent",
                "sent_status": random.choice(["draft", "sent", "sent"]),
                "approved_by_rm": random.random() < 0.6,
                "created_at": datetime.now() - timedelta(days=random.randint(1, 45)),
            }
        )
    return records


# ─── Campaigns ────────────────────────────────────────────────────────────────


def get_campaigns() -> list[dict]:
    return [
        {
            "campaign_id": "CAMP-001",
            "campaign_name": "Q3 Medical & Emergency Loan Drive",
            "product_type": "personal_loan",
            "segment_name": "medical_high_spend",
            "status": "active",
            "approved_by_rm": True,
            "target_count": 15,
            "success_count": 4,
            "meta_json": json.dumps(
                {
                    "target_profiles": ["high_intent_medical"],
                    "interest_rate": "10.5%",
                    "max_amount": 1000000,
                    "tenure_months": [12, 24, 36],
                }
            ),
        },
        {
            "campaign_id": "CAMP-002",
            "campaign_name": "Home Renovation Special 2024",
            "product_type": "personal_loan",
            "segment_name": "renovation_buyers",
            "status": "active",
            "approved_by_rm": True,
            "target_count": 12,
            "success_count": 3,
            "meta_json": json.dumps(
                {
                    "target_profiles": ["high_intent_renovation"],
                    "interest_rate": "10.99%",
                    "max_amount": 2000000,
                    "tenure_months": [24, 36, 48, 60],
                }
            ),
        },
        {
            "campaign_id": "CAMP-003",
            "campaign_name": "Education Excellence Loan Campaign",
            "product_type": "education_loan",
            "segment_name": "education_spenders",
            "status": "draft",
            "approved_by_rm": False,
            "target_count": 10,
            "success_count": 0,
            "meta_json": json.dumps(
                {
                    "target_profiles": ["high_intent_education"],
                    "interest_rate": "9.75%",
                    "max_amount": 1500000,
                    "moratorium": "course_duration + 6 months",
                }
            ),
        },
    ]


# ─── Chat sessions + messages ─────────────────────────────────────────────────


def get_chat_sessions() -> list[dict]:
    now = datetime.now()
    return [
        {
            "session_id": "SESS-001",
            "title": "Analyze Aarav Sharma – Loan Prospect",
            "is_pinned": True,
            "is_archived": False,
            "customer_context": "CUST001",
            "created_at": now - timedelta(hours=3),
            "updated_at": now - timedelta(hours=2),
            "messages": [
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Tell me about CUST001 and whether they are a good loan prospect.",
                    "agent_steps": None,
                    "created_at": now - timedelta(hours=3),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "**Aarav Sharma (CUST001)** is a 32-year-old software engineer at Bangalore "
                        "earning ₹15L/year with a credit score proxy of 760. Analysis of his last 6 months "
                        "shows a ₹1.8L+ medical expenditure pattern, no existing personal loan, and stable "
                        "monthly salary credits of ~₹1.25L. He is an **excellent personal loan prospect** — "
                        "high repayment capacity, low debt ratio, and a clear funding need."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "get_customer_profile",
                                "input": {"customer_id": "CUST001"},
                                "output": "Customer found: Aarav Sharma, Bangalore, ₹15L income",
                            },
                            {
                                "tool": "get_transaction_summary",
                                "input": {"customer_id": "CUST001", "days": 180},
                                "output": "₹1.8L medical spend detected, 6 salary credits, no EMI for personal loan",
                            },
                            {
                                "tool": "get_product_holdings",
                                "input": {"customer_id": "CUST001"},
                                "output": "savings_account, credit_card, car_loan — no personal loan",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(hours=2, minutes=58),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Draft a WhatsApp message for him.",
                    "agent_steps": None,
                    "created_at": now - timedelta(hours=2, minutes=30),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "Here is a drafted WhatsApp message for Aarav:\n\n"
                        "*Dear Aarav, we noticed you recently managed significant medical expenses. "
                        "Our Medical Personal Loan offers up to ₹10 Lakhs at 10.5% p.a. — no collateral, "
                        "funds in 24 hours, flexible EMIs. You are pre-approved! Reply YES to proceed or "
                        "call your RM directly.*\n\n"
                        "This message has been saved as a draft pending your approval."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "generate_outreach_message",
                                "input": {
                                    "customer_id": "CUST001",
                                    "intent": "medical_loan",
                                    "channel": "whatsapp",
                                },
                                "output": "Draft message generated and saved",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(hours=2, minutes=28),
                },
            ],
        },
        {
            "session_id": "SESS-002",
            "title": "Top Loan Prospects This Week",
            "is_pinned": True,
            "is_archived": False,
            "customer_context": None,
            "created_at": now - timedelta(days=1),
            "updated_at": now - timedelta(days=1, hours=1),
            "messages": [
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Who are the top 5 loan prospects I should contact this week?",
                    "agent_steps": None,
                    "created_at": now - timedelta(days=1),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "Based on transaction signal analysis, here are your **Top 5 High-Priority Prospects**:\n\n"
                        "1. **Aarav Sharma (CUST001)** — ₹1.8L medical spend, no personal loan, credit score 760\n"
                        "2. **Vikram Singh (CUST005)** — ₹2.4L medical bills, stable ₹2L income, credit score 780\n"
                        "3. **Arjun Rao (CUST013)** — ₹3.5L+ renovation spend, consultant, credit score 790\n"
                        "4. **Rahul Joshi (CUST007)** — Multiple renovation transactions, PM salary ₹2.2L, score 770\n"
                        "5. **Ananya Iyer (CUST010)** — Wedding expense pattern ₹2.8L, no personal loan, score 745\n\n"
                        "Recommend prioritising CUST001 and CUST013 for this week's outreach."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "get_all_customers",
                                "input": {"limit": 75},
                                "output": "75 customers retrieved",
                            },
                            {
                                "tool": "get_loan_signals",
                                "input": {"filters": {"confidence_min": 0.85}},
                                "output": "15 high-confidence signals found",
                            },
                            {
                                "tool": "rank_prospects",
                                "input": {"n": 5},
                                "output": "Top 5 prospects ranked by signal strength + repayment capacity",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(days=1, minutes=2),
                },
            ],
        },
        {
            "session_id": "SESS-003",
            "title": "Campaign Planning – Renovation Q3",
            "is_pinned": False,
            "is_archived": False,
            "customer_context": None,
            "created_at": now - timedelta(days=2),
            "updated_at": now - timedelta(days=2, hours=2),
            "messages": [
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Create a campaign targeting all customers who have renovation spending patterns.",
                    "agent_steps": None,
                    "created_at": now - timedelta(days=2),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "I've created **Campaign: Home Renovation Special 2024** targeting 12 customers "
                        "with home_renovation spending signals. The campaign offers Personal Loans up to "
                        "₹20 Lakhs at 10.99% p.a. Campaign ID: CAMP-002. Awaiting your approval to activate."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "search_customers_by_signal",
                                "input": {
                                    "signal_type": "home_renovation_spend",
                                    "min_confidence": 0.80,
                                },
                                "output": "12 customers matched",
                            },
                            {
                                "tool": "create_campaign",
                                "input": {
                                    "name": "Home Renovation Special 2024",
                                    "segment": "renovation_buyers",
                                },
                                "output": "Campaign CAMP-002 created in draft status",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(days=2, minutes=3),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Approve this campaign and generate outreach messages for the top 3 customers.",
                    "agent_steps": None,
                    "created_at": now - timedelta(days=2, hours=1),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "Campaign CAMP-002 is now **Active** ✅\n\n"
                        "Outreach drafts generated for:\n"
                        "- **CUST007 Rahul Joshi** — WhatsApp message drafted\n"
                        "- **CUST011 Karthik Reddy** — Email drafted\n"
                        "- **CUST013 Arjun Rao** — WhatsApp message drafted\n\n"
                        "All 3 messages are in draft status. Please review and approve for sending."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "approve_campaign",
                                "input": {"campaign_id": "CAMP-002"},
                                "output": "Campaign activated",
                            },
                            {
                                "tool": "generate_outreach_message",
                                "input": {
                                    "customer_ids": ["CUST007", "CUST011", "CUST013"],
                                    "campaign_id": "CAMP-002",
                                },
                                "output": "3 draft outreach messages created",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(days=2, hours=1, minutes=2),
                },
            ],
        },
        {
            "session_id": "SESS-004",
            "title": "Risk Profile – Rahul Chatterjee",
            "is_pinned": False,
            "is_archived": False,
            "customer_context": "CUST072",
            "created_at": now - timedelta(days=3),
            "updated_at": now - timedelta(days=3, hours=1),
            "messages": [
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Analyse CUST072 risk profile. Should we offer them any new product?",
                    "agent_steps": None,
                    "created_at": now - timedelta(days=3),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "**Rahul Chatterjee (CUST072)** risk analysis:\n\n"
                        "🔴 **High Risk** — Credit score proxy: 580\n"
                        "- EMI-to-income ratio: ~58% (very high)\n"
                        "- Personal loan outstanding: ₹18L+\n"
                        "- Credit card utilisation: ~87% of limit\n"
                        "- Volatile business income (Mumbai, entrepreneur)\n"
                        "- Low account balance: ₹45,000\n\n"
                        "**Recommendation:** Do NOT offer additional unsecured credit. "
                        "Consider debt consolidation consultation. Flag for risk monitoring."
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "get_customer_profile",
                                "input": {"customer_id": "CUST072"},
                                "output": "High-risk customer, score 580",
                            },
                            {
                                "tool": "get_product_holdings",
                                "input": {"customer_id": "CUST072"},
                                "output": "personal_loan ₹18L outstanding, credit card 87% utilised",
                            },
                            {
                                "tool": "get_transaction_summary",
                                "input": {"customer_id": "CUST072"},
                                "output": "High EMI debits, volatile income, cash withdrawals",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(days=3, minutes=3),
                },
            ],
        },
        {
            "session_id": "SESS-005",
            "title": "Weekly RM Dashboard Summary",
            "is_pinned": False,
            "is_archived": True,
            "customer_context": None,
            "created_at": now - timedelta(days=7),
            "updated_at": now - timedelta(days=7, hours=1),
            "messages": [
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Generate a weekly summary of my customer portfolio.",
                    "agent_steps": None,
                    "created_at": now - timedelta(days=7),
                },
                {
                    "message_id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": (
                        "**Weekly Portfolio Summary**\n\n"
                        "📊 **Total Customers:** 75\n"
                        "🟢 **Low Risk:** 48 | 🟡 **Medium Risk:** 23 | 🔴 **High Risk:** 4\n\n"
                        "**Opportunity Highlights:**\n"
                        "- 15 high-intent loan prospects identified\n"
                        "- 3 active campaigns (CAMP-001, CAMP-002, CAMP-003 pending)\n"
                        "- 5 dormant customers flagged for reactivation\n"
                        "- 12 salaried tech professionals eligible for credit card upgrade\n\n"
                        "**Actions Needed:**\n"
                        "- Approve 7 outreach messages in draft\n"
                        "- Approve Campaign CAMP-003 (Education Loan)\n"
                        "- Follow up on CUST001, CUST005, CUST007 (hot prospects)"
                    ),
                    "agent_steps": json.dumps(
                        [
                            {
                                "tool": "get_all_customers",
                                "input": {"limit": 100},
                                "output": "75 customers retrieved and summarised",
                            },
                            {
                                "tool": "get_all_campaigns",
                                "input": {},
                                "output": "3 campaigns: 2 active, 1 draft",
                            },
                            {
                                "tool": "get_audit_logs",
                                "input": {"limit": 50},
                                "output": "Recent activity summarised",
                            },
                        ]
                    ),
                    "created_at": now - timedelta(days=7, minutes=4),
                },
            ],
        },
    ]


# ─── Audit logs ───────────────────────────────────────────────────────────────


def get_audit_logs() -> list[dict]:
    now = datetime.now()

    def _log(
        actor_type: str,
        actor_name: str,
        action_type: str,
        entity_type: str,
        entity_id: str | None,
        tool_name: str | None,
        req: dict,
        resp: dict,
        ago_hours: float,
    ) -> dict:
        return {
            "audit_id": str(uuid.uuid4()),
            "actor_type": actor_type,
            "actor_name": actor_name,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "request_payload": json.dumps(req),
            "response_payload": json.dumps(resp),
            "tool_name": tool_name,
            "created_at": now - timedelta(hours=ago_hours),
        }

    return [
        _log(
            "agent",
            "CustomerAnalysisAgent",
            "fetch_profile",
            "customer",
            "CUST001",
            "get_customer_profile",
            {"customer_id": "CUST001"},
            {"status": "ok", "customer": "Aarav Sharma"},
            2.5,
        ),
        _log(
            "agent",
            "TransactionAnalysisAgent",
            "analyze_transactions",
            "customer",
            "CUST001",
            "get_transaction_summary",
            {"customer_id": "CUST001", "days": 180},
            {"status": "ok", "medical_spend": 185000, "salary_months": 6},
            2.4,
        ),
        _log(
            "agent",
            "OutreachWriterAgent",
            "generate_outreach",
            "outreach",
            "CUST001",
            "create_outreach_draft",
            {"customer_id": "CUST001", "channel": "whatsapp"},
            {"status": "ok", "draft_saved": True},
            2.3,
        ),
        _log(
            "user",
            "RM-001",
            "approve_outreach",
            "outreach",
            "CUST001",
            None,
            {"outreach_id": "draft-001", "action": "approve"},
            {"status": "ok", "sent": True},
            2.0,
        ),
        _log(
            "agent",
            "CustomerAnalysisAgent",
            "fetch_profile",
            "customer",
            "CUST005",
            "get_customer_profile",
            {"customer_id": "CUST005"},
            {"status": "ok", "customer": "Vikram Singh"},
            5.0,
        ),
        _log(
            "agent",
            "SignalDetectionAgent",
            "detect_loan_signal",
            "customer",
            "CUST005",
            "upsert_loan_signal",
            {"customer_id": "CUST005", "signal_type": "large_medical_spend"},
            {"status": "ok", "confidence": 0.92},
            4.8,
        ),
        _log(
            "user",
            "RM-002",
            "create_rm_note",
            "customer",
            "CUST005",
            None,
            {"customer_id": "CUST005", "note": "Medical loan prospect - follow up"},
            {"status": "ok"},
            4.5,
        ),
        _log(
            "user",
            "RM-002",
            "create_campaign",
            "campaign",
            "CAMP-001",
            None,
            {"campaign_name": "Q3 Medical Loan Drive"},
            {"status": "ok", "campaign_id": "CAMP-001"},
            24.0,
        ),
        _log(
            "user",
            "RM-002",
            "approve_campaign",
            "campaign",
            "CAMP-001",
            None,
            {"campaign_id": "CAMP-001"},
            {"status": "ok", "new_status": "active"},
            23.5,
        ),
        _log(
            "system",
            "scheduler",
            "scheduled_signal_refresh",
            "system",
            None,
            "run_signal_detection",
            {"scope": "all_customers"},
            {"status": "ok", "signals_refreshed": 75},
            6.0,
        ),
        _log(
            "agent",
            "TransactionAnalysisAgent",
            "analyze_transactions",
            "customer",
            "CUST007",
            "get_transaction_summary",
            {"customer_id": "CUST007", "days": 90},
            {"status": "ok", "renovation_spend": 340000},
            8.0,
        ),
        _log(
            "agent",
            "ProductRecommendationAgent",
            "recommend_product",
            "customer",
            "CUST007",
            "get_product_recommendations",
            {"customer_id": "CUST007"},
            {"status": "ok", "recommended": "home_renovation_loan"},
            7.8,
        ),
        _log(
            "user",
            "RM-001",
            "send_outreach",
            "outreach",
            "CUST007",
            None,
            {"outreach_id": "draft-007", "channel": "whatsapp"},
            {"status": "ok", "delivered": True},
            7.5,
        ),
        _log(
            "agent",
            "ReportAgent",
            "generate_weekly_report",
            "report",
            None,
            "generate_portfolio_report",
            {"rm_id": "RM-001", "period": "weekly"},
            {"status": "ok", "prospects": 15, "campaigns": 3},
            48.0,
        ),
        _log(
            "user",
            "RM-001",
            "review_dashboard",
            "dashboard",
            None,
            None,
            {"rm_id": "RM-001"},
            {"status": "ok"},
            47.0,
        ),
        _log(
            "agent",
            "RiskAgent",
            "analyze_risk",
            "customer",
            "CUST072",
            "get_risk_profile",
            {"customer_id": "CUST072"},
            {"status": "ok", "risk_level": "high", "score_proxy": 580},
            72.0,
        ),
        _log(
            "system",
            "dormancy_detector",
            "flag_dormant",
            "customer",
            "CUST067",
            "flag_dormant_account",
            {"customer_id": "CUST067", "days_inactive": 145},
            {"status": "ok", "flagged": True},
            96.0,
        ),
        _log(
            "agent",
            "OutreachWriterAgent",
            "generate_outreach",
            "outreach",
            "CUST012",
            "create_outreach_draft",
            {"customer_id": "CUST012", "intent": "medical_loan"},
            {"status": "ok", "draft_saved": True},
            12.0,
        ),
        _log(
            "user",
            "RM-003",
            "edit_outreach",
            "outreach",
            "CUST012",
            None,
            {"outreach_id": "draft-012", "action": "edit"},
            {"status": "ok", "edited": True},
            11.5,
        ),
        _log(
            "system",
            "credit_refresh_job",
            "refresh_credit_proxy",
            "system",
            None,
            "refresh_credit_scores",
            {"count": 75},
            {"status": "ok", "refreshed": 75},
            120.0,
        ),
    ]


# ─── Main seed function ───────────────────────────────────────────────────────


def run_seed() -> None:
    with get_db_context() as db:
        # Guard: skip if already seeded
        existing = db.execute(select(Customer).limit(1)).scalars().first()
        if existing:
            print(
                f"  Database already seeded ({existing.customer_id} found). Skipping."
            )
            return

        # ── Campaigns ──────────────────────────────────────────────────────────
        print("  Inserting campaigns...")
        campaign_rows = get_campaigns()
        campaign_ids: list[str] = []
        for cdata in campaign_rows:
            camp = Campaign(**cdata)
            db.add(camp)
            campaign_ids.append(cdata["campaign_id"])
        db.flush()

        # ── Customers, accounts, transactions, holdings, signals, notes, outreach ─
        print("  Inserting customers and related data...")
        total_txns = 0
        for idx, cdata in enumerate(CUSTOMERS_DATA, start=1):
            cid = cdata["customer_id"]
            acc_id = f"ACC{cid.replace('CUST', '').zfill(3)}"

            # ── Customer ────────────────────────────────────────────────────
            opening = TODAY - timedelta(days=cdata["account_tenure_months"] * 30)
            lc_date = _last_contact(cdata["profile_type"], 0)

            customer = Customer(
                customer_id=cid,
                full_name=cdata["full_name"],
                age=cdata["age"],
                gender=cdata["gender"],
                city=cdata["city"],
                occupation=cdata["occupation"],
                employment_type=cdata["employment_type"],
                annual_income=float(cdata["annual_income"]),
                credit_score_proxy=cdata["credit_score_proxy"],
                account_tenure_months=cdata["account_tenure_months"],
                consent_marketing=cdata["consent_marketing"],
                last_contact_date=lc_date,
                risk_segment=cdata["risk_segment"],
                rm_assigned=cdata["rm_assigned"],
                phone=_phone(cid),
                email=_email(cdata["full_name"], cid),
                kyc_status=cdata["kyc_status"],
                dependents=cdata["dependents"],
            )
            db.add(customer)
            db.flush()

            # ── Transactions ────────────────────────────────────────────────
            txns_data, final_bal, avg_bal, inflow, outflow = generate_transactions(
                cdata, acc_id
            )
            total_txns += len(txns_data)

            # ── Account ─────────────────────────────────────────────────────
            account = CustomerAccount(
                account_id=acc_id,
                customer_id=cid,
                account_type=cdata["account_type"],
                opening_date=opening,
                current_balance=round(final_bal, 2),
                avg_monthly_balance=round(avg_bal, 2),
                monthly_inflow=round(inflow, 2),
                monthly_outflow=round(outflow, 2),
                status="active" if cdata["profile_type"] != "dormant" else "dormant",
            )
            db.add(account)
            db.flush()

            # Insert transaction rows
            for td in txns_data:
                db.add(Transaction(**td))

            # ── Product holdings ────────────────────────────────────────────
            for hdata in generate_product_holdings(cdata):
                db.add(ProductHolding(**hdata))

            # ── Loan signals ────────────────────────────────────────────────
            for sdata in generate_loan_signals(cdata, txns_data):
                db.add(LoanSignal(**sdata))

            # ── RM Notes ────────────────────────────────────────────────────
            for ndata in generate_rm_notes(cdata):
                db.add(RMNote(**ndata))

            # ── Outreach ────────────────────────────────────────────────────
            for odata in generate_outreach(cdata, campaign_ids):
                db.add(OutreachHistory(**odata))

            if idx % 10 == 0:
                print(f"    ...{idx}/75 customers processed")
            db.flush()

        # ── Chat sessions + messages ───────────────────────────────────────
        print("  Inserting chat sessions...")
        for sess_data in get_chat_sessions():
            messages = sess_data.pop("messages")
            session = ChatSession(**sess_data)
            db.add(session)
            db.flush()
            for mdata in messages:
                msg = ChatMessage(session_id=sess_data["session_id"], **mdata)
                db.add(msg)

        # ── Audit logs ─────────────────────────────────────────────────────
        print("  Inserting audit logs...")
        for alog in get_audit_logs():
            db.add(AuditLog(**alog))

        db.flush()
        print(
            f"  Seed complete: 75 customers, {total_txns} transactions, "
            f"{len(campaign_rows)} campaigns, 5 chat sessions, 20 audit entries."
        )


if __name__ == "__main__":
    from app.db.database import init_db

    init_db()
    run_seed()
