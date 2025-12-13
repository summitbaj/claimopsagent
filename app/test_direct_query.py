"""
Check if there's any data in the smvs_claim table
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dataverse.mcp_client import get_mcp_client


async def verify_data():
    """Check if data exists in smvs_claim table"""
    
    print("🔍 Checking for data in smvs_claim table")
    print("=" * 60)
    
    mcp = get_mcp_client()
    await mcp.initialize()
    
    try:
        # Test 1: Count total records
        print("\n1️⃣  Counting total records...")
        count_query = "SELECT COUNT(*) as total FROM smvs_claim"
        count_result = await mcp.read_query(count_query)
        print(f"   Result: {count_result}")
        
        # Test 2: Get any record
        print("\n2️⃣  Trying to get ANY record...")
        any_query = "SELECT TOP 10 smvs_claimid, smvs_name FROM smvs_claim"
        any_result = await mcp.read_query(any_query)
        print(f"   Result: {any_result}")
        print(f"   Found {len(any_result) if any_result else 0} records")
        
        # Test 3: Try your specific claim ID
        print("\n3️⃣  Looking for your specific claim...")
        claim_id = "6c38fb51-3611-f011-9988-000d3a30044f"
        specific_query = f"SELECT * FROM smvs_claim WHERE smvs_claimid = '{claim_id}'"
        specific_result = await mcp.read_query(specific_query)
        print(f"   Result: {specific_result}")
        
        if not any_result or len(any_result) == 0:
            print("\n" + "="*60)
            print("❌ NO DATA FOUND IN smvs_claim TABLE")
            print("="*60)
            print("\n🔧 Next steps:")
            print("1. Verify that your Dataverse environment has claims data")
            print("2. Check if data is in a different table")
            print("3. Import sample claims data for testing")
            print("\n💡 The table exists but is empty!")
        else:
            print("\n" + "="*60)
            print("✅ DATA EXISTS!")
            print("="*60)
            print(f"Found {len(any_result)} records")
            if any_result:
                print(f"Sample record: {any_result[0]}")
        
    finally:
        await mcp.close()


if __name__ == "__main__":
    asyncio.run(verify_data())