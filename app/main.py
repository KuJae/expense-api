from fastapi import FastAPI

from app.routers import transactions

app = FastAPI(title="지출 관리 API")


@app.get("/")
def read_root():
    return {"message": "지출 관리 API에 오신 것을 환영합니다"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(transactions.router)
