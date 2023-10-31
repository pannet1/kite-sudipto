import requests
import dateutil.parser


class KiteApp:
    PRODUCT_MIS = "MIS"
    PRODUCT_CNC = "CNC"
    PRODUCT_NRML = "NRML"
    PRODUCT_CO = "CO"
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_SLM = "SL-M"
    ORDER_TYPE_SL = "SL"
    VARIETY_REGULAR = "regular"
    VARIETY_CO = "co"
    VARIETY_AMO = "amo"
    TRANSACTION_TYPE_BUY = "BUY"
    TRANSACTION_TYPE_SELL = "SELL"
    VALIDITY_DAY = "DAY"
    VALIDITY_IOC = "IOC"
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_MCX = "MCX"

    def __init__(self, enctoken):
        self.headers = {"Authorization": f"enctoken {enctoken}"}
        self.session = requests.session()
        self.root_url = "https://api.kite.trade"
        self.session.get((self.root_url), headers=(self.headers))

    def instruments(self, exchange=None):
        data = self.session.get(
            f"{self.root_url}/instruments", headers=(self.headers)
        ).text.split("\n")
        Exchange = []
        for i in data[1:-1]:
            row = i.split(",")
            if exchange is None or exchange == row[11]:
                Exchange.append(
                    {
                        "instrument_token": int(row[0]),
                        "exchange_token": row[1],
                        "tradingsymbol": row[2],
                        "name": row[3][1:-1],
                        "last_price": float(row[4]),
                        "expiry": dateutil.parser.parse(row[5]).date()
                        if row[5] != ""
                        else None,
                        "strike": float(row[6]),
                        "tick_size": float(row[7]),
                        "lot_size": int(row[8]),
                        "instrument_type": row[9],
                        "segment": row[10],
                        "exchange": row[11],
                    }
                )

        return Exchange

    def quote(self, instruments):
        data = self.session.get(
            f"{self.root_url}/quote", params={"i": instruments}, headers=(self.headers)
        ).json()["data"]
        return data

    def ltp(self, instruments):
        data = self.session.get(
            f"{self.root_url}/quote/ltp",
            params={"i": instruments},
            headers=(self.headers),
        ).json()["data"]
        return data

    def historical_data(
        self, instrument_token, from_date, to_date, interval, continuous=False, oi=False
    ):
        params = {
            "from": from_date,
            "to": to_date,
            "interval": interval,
            "continuous": 1 if continuous else 0,
            "oi": 1 if oi else 0,
        }
        lst = self.session.get(
            f"{self.root_url}/instruments/historical/{instrument_token}/{interval}",
            params=params,
            headers=(self.headers),
        ).json()["data"]["candles"]
        records = []
        for i in lst:
            record = {
                "date": dateutil.parser.parse(i[0]),
                "open": i[1],
                "high": i[2],
                "low": i[3],
                "close": i[4],
                "volume": i[5],
            }
            if len(i) == 7:
                record["oi"] = i[6]
            records.append(record)

        return records

    def profile(self):
        profile = self.session.get(
            f"{self.root_url}/user/profile", headers=self.headers
        ).json()["data"]
        return profile

    def margins(self):
        margins = self.session.get(
            f"{self.root_url}/user/margins", headers=(self.headers)
        ).json()["data"]
        return margins

    def orders(self):
        orders = self.session.get(
            f"{self.root_url}/orders", headers=(self.headers)
        ).json()["data"]
        return orders

    def positions(self):
        positions = self.session.get(
            f"{self.root_url}/portfolio/positions", headers=(self.headers)
        ).json()["data"]
        return positions

    def place_order(
        self,
        variety,
        exchange,
        tradingsymbol,
        transaction_type,
        quantity,
        product,
        order_type,
        price=None,
        validity=None,
        disclosed_quantity=None,
        trigger_price=None,
        squareoff=None,
        stoploss=None,
        trailing_stoploss=None,
        tag=None,
    ):
        params = locals()
        del params["self"]
        for k in list(params.keys()):
            if params[k] is None:
                del params[k]

        order_id = self.session.post(
            f"{self.root_url}/orders/{variety}", data=params, headers=(self.headers)
        ).json()["data"]["order_id"]
        return order_id

    def modify_order(
        self,
        variety,
        order_id,
        parent_order_id=None,
        quantity=None,
        price=None,
        order_type=None,
        trigger_price=None,
        validity=None,
        disclosed_quantity=None,
    ):
        params = locals()
        del params["self"]
        for k in list(params.keys()):
            if params[k] is None:
                del params[k]

        order_id = self.session.put(
            f"{self.root_url}/orders/{variety}/{order_id}",
            data=params,
            headers=(self.headers),
        ).json()["data"]["order_id"]
        return order_id

    def cancel_order(self, variety, order_id, parent_order_id=None):
        order_id = self.session.delete(
            f"{self.root_url}/orders/{variety}/{order_id}",
            data=({"parent_order_id": parent_order_id} if parent_order_id else {}),
            headers=(self.headers),
        ).json()["data"]["order_id"]
        return order_id


def get_enctoken(userid: str, password: str, twofa: str) -> str:
    session = requests.Session()
    response = session.post(
        "https://kite.zerodha.com/api/login",
        data={"user_id": userid, "password": password},
    )
    response = session.post(
        "https://kite.zerodha.com/api/twofa",
        data={
            "request_id": response.json()["data"]["request_id"],
            "twofa_value": twofa,
            "user_id": response.json()["data"]["user_id"],
        },
    )
    enctoken = response.cookies.get("enctoken")
    if enctoken:
        return enctoken
    raise Exception("Enter valid details !!!!")


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    import utils
    import kite_connect

    configuration_details: list[dict] = utils.get_config_from_yaml()

    def login_to_kite_web_using_playwright(credentials_from_config, context) -> tuple:
        username = credentials_from_config.get("username")
        password = credentials_from_config.get("password")
        t_otp = credentials_from_config.get("time_based_otp_key")
        page = context.new_page()
        page.goto("https://kite.zerodha.com/?next=%2Fdashboard")
        page.get_by_label("User ID").click()
        page.get_by_label("User ID").fill(username)
        page.get_by_placeholder("Password").click()
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()
        otp = utils.get_otp(t_otp)
        page.get_by_placeholder("••••••").fill(otp)
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="I understand").click()
        enc_token = [
            cookie["value"]
            for cookie in context.cookies()
            if cookie["name"] == "enctoken"
        ]
        enc_token = next(iter(enc_token), None)
        return enc_token

    configuration_details: list[dict] = utils.get_config_from_yaml()

    # Playwright operations
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()

    # Other operations
    enc_token = login_to_kite_web_using_playwright(
        configuration_details["credentials"], context
    )
    if not enc_token:
        print("enc_token is missing. Please check")
        SystemExit(-1)

    kite_client = kite_connect.KiteApp(enc_token)

    """
    NIFTY': {'underlying': 'NSE:NIFTY 50', 'expiry': '23OCT', 
    'lotsize': 25, 'stoploss': 10, 'segment': 'NFO-OPT', 'multiplier': 1}}"
    """
    args = dict(
        variety="regular",
        exchange="NSE",
        tradingsymbol="TRIDENT",
        transaction_type="BUY",
        quantity=1,
        product="MIS",
        order_type="MARKET",
        price=None,
        validity=None,
    )
    kite_client.place_order(**args)

