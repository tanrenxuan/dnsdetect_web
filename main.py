import json

from fastapi import Depends, FastAPI, APIRouter, UploadFile
from sqlalchemy.orm import Session
from typing import List
from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
from detect_util.detect import DetectDomain

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

d = DetectDomain()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router_dns = APIRouter(
    prefix="/dns",
    tags=["dns"],
)


@router_dns.post("/", response_model=schemas.Alart)
def create_alart(alart: schemas.AlartCreate, db: Session = Depends(get_db)):
    ans = crud.create_alart(db=db, alart=alart, detectObject=d)
    if ans is not None:
        return ans


@router_dns.get("/ip", response_model=List[schemas.Alart])
def read_alart_by_ip(ip: str, db: Session = Depends(get_db)):
    alarts = crud.get_alart_by_ip(db, ip)
    return alarts


@router_dns.get("/domain", response_model=List[schemas.Alart])
def read_alart_by_domain(domain: str, db: Session = Depends(get_db)):
    alarts = crud.get_alart_by_domain(db, domain)
    return alarts


@router_dns.get("/all", response_model=List[schemas.Alart])
def read_all(db: Session = Depends(get_db)):
    alarts = crud.get_all(db)
    return alarts


@router_dns.post("/file", response_model=List[schemas.Alart])
def create_many_alart(file: UploadFile, db: Session = Depends(get_db)):
    alart_list = []
    for line in file.file:
        j_contents = json.loads(line)
        raw_message_json = json.loads(j_contents['raw_message'])
        domain = raw_message_json['requestDomain']
        client_ip = raw_message_json['clientIp']
        access_time = raw_message_json['startTimeNs']
        alart = schemas.AlartCreate(client_ip=client_ip, access_time=access_time, domain=domain)
        ans = crud.create_alart(db=db, alart=alart, detectObject=d)
        if ans is not None:
            alart_list.append(ans)
    return alart_list


app.include_router(router_dns)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
