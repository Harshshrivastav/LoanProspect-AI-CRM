from app.services.customer_service import get_customer_detail, get_customers_list
from app.utils.logger import get_logger
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/customers", tags=["customers"])
logger = get_logger(__name__)


@router.get("")
def list_customers(page: int = Query(1, ge=1), per_page: int = Query(20, le=100)):
    """Returns paginated list of all customers."""
    return get_customers_list(page=page, per_page=per_page)


@router.get("/{customer_id}")
def get_customer(customer_id: str):
    """Returns complete customer detail for the client portal."""
    detail = get_customer_detail(customer_id.upper())
    if not detail:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return detail
