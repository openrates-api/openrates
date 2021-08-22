from datetime import date
from sqlalchemy import Column, String, Float, Integer
from sqlalchemy import UniqueConstraint, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Currency(Base):
    __tablename__ = 'exchangerates'
    __table_args__ = (
        UniqueConstraint('currency', 'date', name='uniq_currency_date'),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column('currency', String(3), nullable=False)
    date = Column('date', Date, default=date.today, nullable=False)
    rate = Column('rate', Float, nullable=False)
