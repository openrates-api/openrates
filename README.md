# OpenRates API

OpenRates is a free and open-source API for current and historical foreign exchange (forex) rates. All currency data is sourced from the European Central Bank and updated daily at around 4:00PM CET.

The OpenRates API allows for historical queries back to 1999 and supports 30+ currencies.

## Installation
```shell
git clone https://github.com/openrates-api/openrates.git
cd openrates
poetry install
poetry shell
cd openrates
uvicorn openrates:app --reload
```

## Features
* **Python <a href="https://github.com/tiangolo/fastapi" class="external-link" target="_blank">**FastAPI**</a> backend**
* **SQLAlchemy** models
* **Open source** Everything from this repo is listed under the Creative Commons license

## Usage

### Latest and Historical Rates
Query the API for the latest available rates.
```http
GET /latest
```

Query the API for historical rates since January 4, 1999. The date format is YYYY-MM-DD.
```http
GET /2001-01-03
```

Query the API for historical rates since January 4, 1999 using a different base. The date format is YYYY-MM-DD.
```http
GET /2001-01-03?base=JPY
```

The default base currency is Euro. Change the base currency using a 3-letter currency code.
```http
GET /latest?base=JPY
```

You can also limit the API result to specific currencies. In order to do so, specify the symbols parameter and set it to your preferred list of comma-separated 3-letter currency codes.
```http
GET /latest?symbols=JPY,GBP
```

You can also limit the API result to specific currencies with a different base. In order to do so, specify the symbols parameter and set it to your preferred list of comma-separated 3-letter currency codes followed by a different base.
```http
GET /latest?symbols=JPY,GBP&base=NZD
```
