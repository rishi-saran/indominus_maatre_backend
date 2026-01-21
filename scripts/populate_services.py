#!/usr/bin/env python3
"""
Script to populate services in Supabase
"""
from app.core.supabase import supabase

services = [
    {
        "name": "Ayusha Homam",
        "description": "Ayusha Homam is performed to revere divine energies for vitality, wellness, and longevity.",
        "base_price": 9999.00,
        "is_virtual": False,
        "category_id": None,
        "provider_id": None,
    },
    {
        "name": "Rudrabisekam",
        "description": "Rudrabisekam is a sacred ritual dedicated to Lord Shiva for blessings and prosperity.",
        "base_price": 11999.00,
        "is_virtual": False,
        "category_id": None,
        "provider_id": None,
    },
    {
        "name": "Satyanarayan Pooja",
        "description": "Satyanarayan Pooja is performed for prosperity, wealth, and fulfillment of desires.",
        "base_price": 5999.00,
        "is_virtual": False,
        "category_id": None,
        "provider_id": None,
    },
    {
        "name": "Lakshmi Pooja",
        "description": "Lakshmi Pooja is a ritual to invoke the blessings of Goddess Lakshmi for wealth and abundance.",
        "base_price": 7999.00,
        "is_virtual": False,
        "category_id": None,
        "provider_id": None,
    },
]

def populate_services():
    """Insert services into the database"""
    try:
        # Get first category
        cat_response = supabase.table("service_categories").select("id").limit(1).execute()
        
        if not cat_response.data:
            print("✗ No categories found. Please create a category first.")
            return
        
        category_id = cat_response.data[0]["id"]
        
        # Get first provider
        prov_response = supabase.table("service_providers").select("id").limit(1).execute()
        
        if not prov_response.data:
            print("✗ No providers found. Please create a provider first.")
            return
        
        provider_id = prov_response.data[0]["id"]
        
        print(f"Using category ID: {category_id}")
        print(f"Using provider ID: {provider_id}\n")
        
        for service in services:
            service["category_id"] = category_id
            service["provider_id"] = provider_id
            response = supabase.table("services").insert(service).execute()
            if response.data:
                print(f"✓ Added: {service['name']} (ID: {response.data[0]['id']})")
            else:
                print(f"✗ Failed to add: {service['name']}")
        print("\nAll services added successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    populate_services()
