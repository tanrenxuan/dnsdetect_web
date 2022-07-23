from sqlalchemy.orm import Session

from sql_app import models
from sql_app import schemas


def get_alart_by_domain(db: Session, domain: str):
    return db.query(models.Alart).filter(models.Alart.domain == domain).all()


def get_alart_by_ip(db: Session, ip: str):
    return db.query(models.Alart).filter(models.Alart.client_ip == ip).all()


def create_alart(db: Session, alart: schemas.AlartCreate, detectObject):
    detetc_log = {'requestDomain': alart.domain, 'startTimeNs': alart.access_time, 'clientIp': alart.client_ip}
    res = detectObject.detect(detetc_log)
    if res is None:
        return None
    else:
        db_alart = models.Alart(client_ip=res['client_ip'], domain=res['domain'], access_time=res['access_time'],
                                warn_info=res['warn_info'], warn_level=res['warn_level'], warn_time=res['warn_time'])
        db.add(db_alart)
        db.commit()
        db.refresh(db_alart)
        return db_alart


def get_all(db: Session):
    return db.query(models.Alart).all()
