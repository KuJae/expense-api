from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.models import TransactionCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["transactions"])

# ── 임시 저장소 (4주차에 진짜 DB로 교체) ──────────
fake_db: list[dict] = []
_next_id = 1


def _find(transaction_id: int):
    # id로 거래 하나를 찾는다. 없으면 None.
    return next((r for r in fake_db if r["id"] == transaction_id), None)


@router.get("", response_model=list[TransactionOut])
def list_transactions(skip: int = 0, limit: int = 10):
    return fake_db[skip:skip + limit]   # 리스트 슬라이싱이 곧 페이지네이션


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate):
    global _next_id
    record = {"id": _next_id, "created_at": datetime.now(), **payload.model_dump()}
    fake_db.append(record)
    _next_id += 1
    return record


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int):
    row = _find(transaction_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{transaction_id}번 거래를 찾을 수 없습니다",
        )
    return row


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int):
    row = _find(transaction_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{transaction_id}번 거래를 찾을 수 없습니다",
        )
    fake_db.remove(row)
