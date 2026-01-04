"""
Payment Methods Routes
Manage payment methods (cards, bank accounts) for deposits
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Annotated
import logging

from ..services.payments.free_subscription_service import free_subscription_service
from ..dependencies.auth import get_current_user
from ..utils.route_helpers import _get_user_id
from ..middleware.cache_manager import cached
from ..utils.query_optimizer import QueryOptimizer
from ..utils.response_optimizer import ResponseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment-methods", tags=["Payment Methods"])


class CreateSetupIntentRequest(BaseModel):
    """Request to create a setup intent for saving payment methods"""

    payment_method_type: str = "card"  # 'card' or 'ach'


class AttachPaymentMethodRequest(BaseModel):
    """Request to attach a payment method"""

    payment_method_id: str


@router.post("/setup-intent")
async def create_setup_intent(
    request: CreateSetupIntentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict:
    """Create a setup intent for saving payment methods"""
    try:
        user_id = _get_user_id(current_user)

        # Get or create Stripe customer
        customer = free_subscription_service.create_customer(
            email=current_user.get("email", ""),
            name=current_user.get("name"),
            metadata={"user_id": str(user_id)},
        )

        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")

        # Payment methods not needed for free subscriptions
        # Return a mock setup intent for backward compatibility
        setup_intent = {
            "id": f"seti_{customer['id']}",
            "client_secret": None,  # Not needed for free subscriptions
        }

        return setup_intent

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create setup intent")


@router.post("/attach")
async def attach_payment_method(
    request: AttachPaymentMethodRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict:
    """Attach a payment method to user's account"""
    try:
        user_id = _get_user_id(current_user)

        # Get or create Stripe customer
        customer = free_subscription_service.create_customer(
            email=current_user.get("email", ""),
            name=current_user.get("name"),
            metadata={"user_id": str(user_id)},
        )

        if not customer:
            raise HTTPException(status_code=500, detail="Failed to create customer")

        # Payment methods not needed for free subscriptions
        # Return success for backward compatibility
        result = {
            "success": True,
            "id": request.payment_method_id,
            "customer_id": customer["id"],
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error attaching payment method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to attach payment method")


@router.get("/")
@cached(ttl=120, prefix="payment_methods")  # 120s TTL for payment methods list
async def list_payment_methods(
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    payment_method_type: Optional[str] = None,
) -> List[Dict]:
    """List user's payment methods with pagination"""
    try:
        user_id = _get_user_id(current_user)

        # Get or create Stripe customer
        customer = free_subscription_service.create_customer(
            email=current_user.get("email", ""),
            name=current_user.get("name"),
            metadata={"user_id": str(user_id)},
        )

        if not customer:
            return []

        # Payment methods not needed for free subscriptions
        # Return empty list for backward compatibility
        payment_methods = []

        # Apply pagination (empty list, so always returns empty)
        return payment_methods

    except Exception as e:
        logger.error(f"Error listing payment methods: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list payment methods")


@router.delete("/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Dict:
    """Delete a payment method"""
    try:
        # Payment methods not needed for free subscriptions
        # Return success for backward compatibility
        success = True
        # success = free_subscription_service.delete_payment_method(payment_method_id)

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to delete payment method"
            )

        return {"success": True, "payment_method_id": payment_method_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete payment method")
