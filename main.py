from fastapi import FastAPI, HTTPException
import requests
import time

app = FastAPI()

API_BASE_URL = "https://api.exchangerate-api.com/v4/latest/"


@app.get("/")
async def root():
    return {"message": "Welcome to the Crypto Price API"}

async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    response = requests.get(f"{API_BASE_URL}{from_currency.upper()}") 
    if response.status_code == 200:
        data = response.json()
        if to_currency.upper() in data["rates"]:
            return data["rates"][to_currency.upper()]
        else:
            raise HTTPException(status_code=400, detail="To currency not supported")
    else:
        raise HTTPException(status_code=400, detail="From currency not supported")


@app.get("/exchange_rate")
async def exchange_rate(from_currency: str, to_currency: str) -> dict:
    rate = await get_exchange_rate(from_currency, to_currency)
    return {
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "exchange_rate": rate,
    }


@app.get("/convert_amount")
async def convert_amount(from_currency: str, to_currency: str, amount: float) -> dict:
    rate = await get_exchange_rate(from_currency, to_currency)
    converted_amount = amount * rate
    return {
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "amount": amount,
        "converted_amount": converted_amount,
    }
  
# @CODE : AN ENDPOINT THAT TAKES A STRING AND CONFIRMS IT HAS
# AT LEAST ONE UPPERCASE LETTER, ONE LOWERCASE LETTER, ONE NUMBER, AND IS 8 OR MORE CHARACTERS
# Make sure the return type matches the function signature, FastAPI enforces that it does!
@app.get("/check_password_strength")
async def check_password_strength(password: str) -> bool:
#    """
#    Coded By: Sharmeen Ananna
#    This function checks whether a given password is strong enough, i.e., it contains at least one digit, 
#    one lowercase letter, one uppercase letter, and is 8 characters long.
#    """
    has_uppercase, has_lowercase, has_digit = False, False, False

    for char in password:
        if char.isupper():
            has_uppercase = True
        if char.islower():
            has_lowercase = True
        if char.isdigit():
            has_digit = True

        if has_uppercase and has_lowercase and has_digit and len(password) >= 8:
            return True

    return False


# @CODE : ADD ENDPOINT TO LIST ALL AVAILABLE CURRENCIES  
# NOTE : FastAPI enforces that the return type of the function matches the function signature!  
#        This is a common error!
#@app.get("/available_currencies")
#async def available_currencies(from_currency: str) -> dict:
#    """
#    Coded by: Nasim Samei
#    This endpoint returns a list of available fiat currencies that can be paired with the @from_currency parameter.  
#    @from_currency : str - you must specify a currency to see what currencies it can be compared against.
#    """
async def get_available_currencies(from_currency: str) -> list:

 response = requests.get(f"{API_BASE_URL}{from_currency.upper()}") 
 if response.status_code == 200:
    data = response.json()
    return list(data["rates"].keys())

 else:
     raise HTTPException(status_code=400, detail="From currency not supported")

@app.get("/available_currencies")

async def available_currencies(from_currency: str) -> dict:

    Available_Curr = await get_available_currencies(from_currency)
    return {
        "available_currencies": Available_Curr        
    }



# @CODE : ADD ENDPOINT TO GET LIST OF CRYPTO CURRENCIES
# You can use this API https://docs.cloud.coinbase.com/sign-in-with-coinbase/docs/api-currencies
# Search for the endpoint that returns all the crypto currencies.
@app.get("/available_crypto")
async def available_crypto() -> dict:
#    """
#    Coded by: Hanieh Mohseni
#    This endpoint allows you to see what crypto-currencies are available  
#    """
# URL of the Coinbase API to get the list of cryptocurrencies
    api_url = "https://api.coinbase.com/v2/currencies/crypto"

    # Send a GET request to the API
    response = requests.get(api_url)

    # Check if the response status code is 200 (OK)
    if response.status_code == 200:
        # Parse the response JSON data
        data = response.json()

        # Extract the currency IDs from the JSON data
        currencies = {currency["code"]: currency["name"] for currency in data['data']}

        # Return a JSON response containing the available currency IDs
        return currencies
    else:
        # Return an error message if the API request fails
        raise HTTPException(status_code=response.status_code, detail="Failed to retrieve available cryptocurrencies.")
        

# @CODE : ADD ENDPOINT TO GET Price of crypto  
# Use the coinbase API from above
# @app.get("/convert_crypto")
# async def convert_crypto(from_crypto: str, to_currency: str) -> dict:
#    """
#    Coded by: <Hanieh Mohseni>  
#    This endpoint allows you to get a quote for a crypto in any supported currency  
#    @from_crypto - chose a crypto currency (eg. BTC, or ETH)  
#    @to_currency - chose a currency to obtain the price in (eg. USD, or CAD)  
#    """
async def get_crypto_price(from_crypto: str, to_currency: str) -> float:
    api_url = "https://api.coinbase.com/v2/exchange-rates"
    response = requests.get(f"{api_url}?currency={from_crypto.upper()}")
    if response.status_code == 200:
        data = response.json()["data"]
        price = data["rates"][to_currency.upper()]
        return price
    else:
        raise HTTPException(status_code=400, detail="Failed to fetch crypto price")

@app.get("/convert_crypto")
async def convert_crypto(from_crypto: str, to_currency: str) -> dict:
    price = await get_crypto_price(from_crypto, to_currency)
    return {
        "from_crypto": from_crypto.upper(),
        "to_currency": to_currency.upper(),
        "price": price,
    }


# @CODE : ADD ENDPOINT TO UPDATE PRICE OF ASSET IN ORDERBOOK DB
# The code below starts you off using SQLAlchemy ORM
# Dependencies should already be installed from your requirements.txt file
# Using the ORM instead of raw SQL is safer and less coupled: it is best practice!
@app.get("/update_orderbookdb_asset_price")
async def update_orderbookdb_asset_price(symbol: str, new_price: float) -> dict:
    """
    Coded by: <name>  
    This endpoint allows us to update the price of the assets in the app  
    @symbol - pick a symbol to update the price of in the orderbook app  
    @new_price - The new price of the symbol  
    """
    
    # import sqlalchemy
    from sqlalchemy import create_engine, Table, Column, String, DateTime, Numeric, update, MetaData
    from sqlalchemy.orm import sessionmaker
    
    # create an engine for building sessions
    engine = create_engine('mysql+pymysql://wiley:wiley123@orderbookdb/orderbook')

    # create an ORM object that maps to the Product table
    metadata = MetaData()
    product_table = Table('Product', metadata,
        Column('symbol', String(16), primary_key=True),
        Column('price', Numeric(precision=15, scale=2)),
        Column('productType', String(12)),
        Column('name', String(128)),
        Column('lastUpdate', DateTime)
    )
    metadata.create_all(engine)

    # create a database session maker
    Session = sessionmaker(bind=engine)

    try:
        # Instantiate the session
        session = Session()
        # create the statement to udpate
        stmt = update(product_table).where(product_table.c.symbol == symbol).values(price=new_price)
        # execute commit and flush the statement
        session.execute(stmt)
        session.commit()
        session.flush()
        return {"update_report": "success", "symbol": symbol, "new_price": new_price}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="An error occurred, make sure symbol exists and price is numeric")
    finally:
        session.close()

    
# @CODE : ADD ENDPOINT FOR INSERTING A CRYPTO CURRENCY INTO THE ORDERBOOK APP
# HINT: Make use of the convert_crypto function from above! 
#       You will need to use the await keyword to wait for the result (otherwise it will run async and not wait for the result)
@app.get("/add_crypto_to_orderbook")
async def add_crypto_to_orderbook(symbol: str) -> dict:
#    """
#     Coded by: Sharmeen Ananna  
#     This endpoint uses the `convert_crypto` function above to get the price of a crypto-currency  
#     and inserts that currency and price into the orderbook database 
#    """

    converted_crypto = await convert_crypto(symbol, "USD")
    available_cryptos = await available_crypto()

    # import sqlalchemy
    from sqlalchemy import create_engine, Table, Column, String, DateTime, Numeric, MetaData
    from sqlalchemy.orm import sessionmaker
    
    # create an engine for building sessions
    engine = create_engine('mysql+pymysql://wiley:wiley123@orderbookdb/orderbook')

    # create an ORM object that maps to the Product table
    metadata = MetaData()
    product_table = Table('Product', metadata,
        Column('symbol', String(16), primary_key=True),
        Column('price', Numeric(precision=15, scale=2)),
        Column('productType', String(12)),
        Column('name', String(128)),
        Column('lastUpdate', DateTime)
    )
    metadata.create_all(engine)

    # create a database session maker
    Session = sessionmaker(bind=engine)

    try:
        # Instantiate the session
        session = Session()
        # Create an object of the Product class
        new_product = {
            'symbol': symbol,
            'price': converted_crypto["price"],
            'productType': "Crypto Curr",
            'name': available_cryptos[symbol],
            'lastUpdate': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        # create the statement to insert
        stmt = product_table.insert().values(new_product)
        # execute commit and flush the statement
        session.execute(stmt)
        session.commit()
        session.flush()
        return {"insert_report": "success", "symbol": symbol, 'price': converted_crypto["price"]}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="An error occurred, make sure symbol exists")
    finally:
        session.close()
