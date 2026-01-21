from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.core.supabase import supabase
from app.dependencies.auth import get_current_user
from app.schemas.address import AddressCreate, AddressOut

router = APIRouter(prefix="/addresses", tags=["Addresses"])


# --------------------
# Helper: Ensure user exists in database
# --------------------
def ensure_user_exists(user_id: UUID, user_email: str):
    """Create user record if it doesn't exist"""
    try:
        # Check if user exists
        check = supabase.table("users").select("id").eq("id", str(user_id)).limit(1).execute()
        
        if not check.data or len(check.data) == 0:
            # User doesn't exist, create it
            supabase.table("users").insert({
                "id": str(user_id),
                "email": user_email,
            }).execute()
    except Exception as e:
        print(f"Warning: Could not ensure user exists: {str(e)}")
        pass  # Continue anyway


# --------------------
# Create Address
# --------------------
@router.post("/", response_model=AddressOut)
def create_address(
    address: AddressCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new address for the current user
    """
    user_id: UUID = current_user["id"]
    user_email: str = current_user.get("email", "")
    
    # Ensure user exists in database
    ensure_user_exists(user_id, user_email)

    try:
        # Combine line1 and line2 into address field
        address_text = address.line1
        if address.line2:
            address_text += " " + address.line2
        
        # Map to database column names
        address_payload = {
            "user_id": str(user_id),
            "address": address_text,
            "city": address.city,
            "state": address.state,
            "pincode": address.postal_code,
        }

        response = (
            supabase
            .table("addresses")
            .insert(address_payload)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        raise HTTPException(status_code=500, detail="Failed to create address")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------
# List User Addresses
# --------------------
@router.get("/", response_model=List[AddressOut])
def list_addresses(
    current_user: dict = Depends(get_current_user),
):
    """
    List all addresses for the current user
    """
    user_id: UUID = current_user["id"]

    try:
        response = (
            supabase
            .table("addresses")
            .select("*")
            .eq("user_id", str(user_id))
            .execute()
        )

        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------
# Get Address by ID
# --------------------
@router.get("/{address_id}", response_model=AddressOut)
def get_address(
    address_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific address (must belong to current user)
    """
    user_id: UUID = current_user["id"]

    try:
        response = (
            supabase
            .table("addresses")
            .select("*")
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Address not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------
# Delete Address
# --------------------
@router.delete("/{address_id}")
def delete_address(
    address_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an address (must belong to current user)
    """
    user_id: UUID = current_user["id"]

    try:
        # Verify ownership
        check_response = (
            supabase
            .table("addresses")
            .select("id")
            .eq("id", str(address_id))
            .eq("user_id", str(user_id))
            .limit(1)
            .execute()
        )

        if not check_response.data or len(check_response.data) == 0:
            raise HTTPException(status_code=404, detail="Address not found")

        # Delete
        supabase.table("addresses").delete().eq("id", str(address_id)).execute()

        return {"message": "Address deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
