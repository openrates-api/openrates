from collections import OrderedDict
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, func, exc
from sqlalchemy.orm import sessionmaker

import pandas
import requests

from db.models import Base, Currency

app = FastAPI()

SQLALCHEMY_DATABASE_URL = "sqlite:///data/currencies.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


async def download_rates(daily=True):
    """Downloads daily or historical data. Defaults to daily."""

    euro_forex_daily_url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip"
    euro_forex_all_url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip"

    if daily:
        zip_file = "eurofxref.zip"
        zip_file_path = f"data/{zip_file}"
        r = requests.get(euro_forex_daily_url)
        if r.status_code == 200:
            with open(zip_file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)
            f.close()
            await import_data(zip_file_path)
    else:
        zip_file = "eurofxref-hist.zip"
        zip_file_path = f"data/{zip_file}"
        r = requests.get(euro_forex_all_url)
        if r.status_code == 200:
            with open(zip_file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)
            f.close()
            await import_hist_data(zip_file_path)


async def import_data(csv_path):
    """Uses pandas to read daily CSV file.
    Parses data then imports into sqlite.
    """

    df = pandas.read_csv(csv_path)
    df_list = df.values
    currencies = [
        "USD",
        "JPY",
        "BGN",
        "CZK",
        "DKK",
        "GBP",
        "HUF",
        "PLN",
        "RON",
        "SEK",
        "CHF",
        "ISK",
        "NOK",
        "HRK",
        "RUB",
        "TRY",
        "AUD",
        "BRL",
        "CAD",
        "CNY",
        "HKD",
        "IDR",
        "ILS",
        "INR",
        "KRW",
        "MXN",
        "MYR",
        "NZD",
        "PHP",
        "SGD",
        "THB",
        "ZAR",
    ]
    todays_date = df_list[0][0]
    todays_date = datetime.strptime(todays_date, "%d %B %Y")
    for x in range(len(df_list[0]) - 2):
        print(f"{currencies[x]},{todays_date},{df_list[0][x+1]}")
        currency = Currency(
            currency=currencies[x], date=todays_date, rate=df_list[0][x + 1]
        )
        try:
            session.add(currency)
            session.commit()
        except exc.IntegrityError:
            session.rollback()
            print("Entry exists")
        finally:
            session.close


async def import_hist_data(csv_path):
    """Uses pandas to read historical CSV file.
    Parses data then imports into sqlite.
    """

    df = pandas.read_csv(csv_path)
    df_list = df.values
    currencies = [
        "USD",
        "JPY",
        "BGN",
        "CYP",
        "CZK",
        "DKK",
        "EEK",
        "GBP",
        "HUF",
        "LTL",
        "LVL",
        "MTL",
        "PLN",
        "ROL",
        "RON",
        "SEK",
        "SIT",
        "SKK",
        "CHF",
        "ISK",
        "NOK",
        "HRK",
        "RUB",
        "TRL",
        "TRY",
        "AUD",
        "BRL",
        "CAD",
        "CNY",
        "HKD",
        "IDR",
        "ILS",
        "INR",
        "KRW",
        "MXN",
        "MYR",
        "NZD",
        "PHP",
        "SGD",
        "THB",
        "ZAR",
    ]
    for row in df_list:
        for k, v in enumerate(row):
            if k == 0:
                the_date = datetime.strptime(v, "%Y-%m-%d")
            elif k == 41:
                break
            else:
                print(f"{currencies[k]},{the_date},{v}")
                currency = Currency(
                    currency=currencies[k], date=the_date, rate=v
                )
                try:
                    session.add(currency)
                    session.commit()
                except exc.IntegrityError:
                    session.rollback()
                    print("Entry exists")
                finally:
                    session.close


@app.on_event("startup")
async def initialize_scheduler():
    """Cron schedule to download daily file each weekday and
    historical file twice a month.
    """

    scheduler = AsyncIOScheduler()
    try:
        scheduler.add_job(
            download_rates,
            "cron",
            day_of_week="mon-fri",
            hour=16,
            minute=10,
            timezone="CET",
        )
        scheduler.start()
    except Exception:
        pass

    try:
        daily = False
        scheduler.add_job(
            download_rates,
            "cron",
            day='1,15',
            hour=2,
            minute=15,
            timezone="CET",
            args=[daily]
        )
    except Exception:
        pass


@app.get("/latest")
@app.get("/api/latest")
async def latest(base: Optional[str] = None,
                 symbols: Optional[str] = None):
    """API route for latest rates."""

    if not base:
        base = "EUR"
    latest_date = session.query(func.max(Currency.date)).first()
    latest_date = latest_date[0].strftime("%Y-%m-%d")
    base_rate = (
        session.query(Currency.rate, func.max(Currency.date))
        .filter(func.date(Currency.date) == latest_date, Currency.currency == base)
        .first()
    )
    if base_rate[0] is None:
        base = "EUR"
        base_rate = (
            session.query(Currency.rate, func.max(Currency.date))
            .filter(func.date(Currency.date) == latest_date,
           Currency.currency == base)
            .first()
        )
    currencies = (
        session.query(Currency.currency, Currency.rate)
        .filter(func.date(Currency.date) == latest_date)
        .all()
    )
    rates = {}
    for k, v in sorted(currencies):
        if k == base:
            pass
        elif base == "EUR":
            if symbols:
                cur_symbols = symbols.split(",")
                if k in cur_symbols:
                    rates.update({k: v})
            else:
                rates.update({k: v})
        else:
            new_rate = float(v) / float(base_rate[0])
            new_rate = round(new_rate, 5)
            if symbols:
                cur_symbols = symbols.split(",")
                if k in cur_symbols:
                    rates.update({k: new_rate})
            else:
                rates.update({k: new_rate})
    if base != "EUR":
        eur_rate = float(1) / float(base_rate[0])
        rates.update({"EUR": round(eur_rate, 5)})
        rates = OrderedDict(sorted(rates.items(), key=lambda t: t[0]))
    return {"base": base, "date": latest_date, "rates": rates}


@app.get("/{date}")
@app.get("/api/{date}")
async def historical(base: Optional[str] = None, date: Optional[str] = None):
    """API route for rates based on date input."""

    if not base:
        base = "EUR"

    if date:
        currencies = (
            session.query(Currency.currency, Currency.rate)
            .filter(func.date(Currency.date) == date)
            .all()
        )
        if not currencies:
            raise HTTPException(
                status_code=404, detail="Invalid date"
            )

    base_rate = (
        session.query(Currency.rate, func.max(Currency.date))
        .filter(func.date(Currency.date) == date, Currency.currency == base)
        .first()
    )
    if base_rate[0] is None:
        base = "EUR"
        base_rate = (
            session.query(Currency.rate, func.max(Currency.date))
            .filter(func.date(Currency.date) == date,
            Currency.currency == base)
            .first()
        )
    currencies = (
        session.query(Currency.currency, Currency.rate)
        .filter(func.date(Currency.date) == date)
        .all()
    )
    rates = {}
    for k, v in sorted(currencies):
        if k == base:
            pass
        elif base == "EUR":
            rates.update({k: v})
        else:
            new_rate = float(v) / float(base_rate[0])
            new_rate = round(new_rate, 5)
            rates.update({k: new_rate})
    if base != "EUR":
        eur_rate = float(1) / float(base_rate[0])
        rates.update({"EUR": round(eur_rate, 5)})
        rates = OrderedDict(sorted(rates.items(), key=lambda t: t[0]))
    return {"base": base, "date": date, "rates": rates}


@app.get("/")
async def index(request: Request):
    """Route for main page."""

    return templates.TemplateResponse("index.html", {"request": request})
