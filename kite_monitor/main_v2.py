import pandas as pd
import utils
from playwright.sync_api import sync_playwright
import kite_connect
import sys

try:
    from tabulate import tabulate
except ImportError:
    # Module is not installed, attempt to install it
    import subprocess
    import sys

    # Replace 'your_module' with the actual module name you want to install
    module_name = "tabulate"

    # Use 'pip' to install the module
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
    except subprocess.CalledProcessError:
        print(f"Failed to install {module_name}. Please install it manually.")
    else:
        # Module installed successfully, now you can import it
        from tabulate import tabulate
kite_chart_url = 'https://kite.zerodha.com/chart/web/ciq/NFO-OPT/{option_name}/{instrument_token}?theme=dark'
rsi_14_column_number = 5
moving_average_10_column_number = 6
atr_14_column_number = 7
macd_7_20_1_column_number = 8
moving_average_20_triple_exponential_column_number = 11

def login_to_kite_web_using_playwright(credentials_from_config, context) -> tuple:
    username = credentials_from_config.get('username')
    password = credentials_from_config.get('password')
    t_otp = credentials_from_config.get('time_based_otp_key')
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
    enc_token = [cookie["value"] for cookie in context.cookies() if cookie["name"] == "enctoken"]
    enc_token = next(iter(enc_token), None)
    return enc_token


def underlying_from_config(symbol_details_from_config: list[dict]) -> list:
    """
        config file should return underlying
        underlying[0] = { 'keyword': 'NIFTY', 'symbol': 'NIFTY 50'}
        underlying[1] = { 'keyword': 'BANKNIFTY', 'symbol': 'BANKNIFTY'}
    """
    return [symbol_details["underlying"] for symbol_details in symbol_details_from_config.values()]


def ltp_for_underlying(lst_underlying: list, kite_client: kite_connect.KiteApp) -> dict:
    """
        kite api will return ltp if list is passed
        like ["NSE:NIFTY 50", "NSE:BANKNIFTY"]
        now we build a dict of form, from keyword
        {"BANKNIFTY": 43020, "NIFTY": 12021}
    """
    output_dict = {}
    for underlying in lst_underlying:
        # key = underlying.split(":")[-1].split()[0]
        tmp = kite_client.ltp(underlying).get(underlying)
        if tmp:
            output_dict[underlying] = tmp.get("last_price")
    # print(output_dict)
    return output_dict


def get_instrument_token(option_name, df):
    tokens = df[df['tradingsymbol'] ==
                option_name]['instrument_token'].to_list()
    return tokens[0] if len(tokens) >= 1 else 0


def coin_option_names(symbol_details_from_config, instrument_details, dct_ltp, kite_client):
    # delete first element common
    for symbol, details in symbol_details_from_config.items():
        # print(details)
        # symbol = list(details.keys())[0]  # Get the symbol from the dictionary
        # if symbol != "common":
        # details = details[symbol]  # Extract details for the symbol
        ltp = dct_ltp[details['underlying']]
        atm = utils.get_atm(details['diff'], ltp)

        val = atm + details['ce']
        option_name = symbol + details['expiry'] + str(val) + 'CE'
        instrument_token = get_instrument_token(
            option_name, instrument_details)

        details["ce_" + "url"] = kite_chart_url.format(
            option_name=option_name, instrument_token=instrument_token)
        details['call'] = option_name
        tmp = kite_client.quote("NFO:"+option_name).get("NFO:"+option_name)
        if tmp:
            details['call_ltp'] = tmp.get("last_price")
            details['call_oi'] = tmp.get("last_price")

        val = atm + details['pe']
        option_name = symbol + details['expiry'] + str(val) + 'PE'
        instrument_token = get_instrument_token(
            option_name, instrument_details)

        details["pe_" + "url"] = kite_chart_url.format(
            option_name=option_name, instrument_token=instrument_token)
        details['put'] = option_name
        tmp = kite_client.quote("NFO:"+option_name).get("NFO:"+option_name)
        if tmp:
            details['put_ltp'] = tmp.get("last_price")
            details['put_oi'] = tmp.get("last_price")
    return symbol_details_from_config


def download_playwright(url: str, context) -> pd.DataFrame:
    """
        if the option name is supplied this returns the
        dataframe. we want to reuse this later for exits
    """
    page3 = context.new_page()
    page3.goto(url)
    page3.wait_for_load_state("networkidle")
    page3.frame_locator(
        "#chart-iframe").locator(".ciq-DT > span").first.click()
    page3.wait_for_load_state("networkidle")
    try:
        page3.frame_locator("#chart-iframe").get_by_role("button", name="+ Additional columns").is_visible(timeout=100)
        page3.frame_locator("#chart-iframe").get_by_role("button", name="+ Additional columns").click()
    except:
        pass
        
    with page3.expect_download() as download_info:
        page3.frame_locator(
            "#chart-iframe").get_by_role("button", name="Download").click()
        download1 = download_info.value
        df = pd.read_csv(f"{download1.path()}")
        # url.split("/")[-2]
        df["symbol"] = url.split("/")[-2]
        for col in df.columns:
            if col == "Date":
                continue
            try:
                df[col] = df[col].str.replace(',', '').astype(float)
            except:
                pass
    page3.close()
    return df


def generate_signal_fm_df(df_ce: pd.DataFrame, df_pe: pd.DataFrame, details: dict) -> str:
    """
       if signal is generated it return the name of the option
       a dictionary can be built from the caller of this function.
       {"BANKNIFTY": {"signal": "BANKNIFTY23OCT42800CE"}}
    """
    call_oi = details.get("call_oi", 0)
    put_oi = details.get("put_oi", 0)
    
    print_data = [
        ["Time", "Symbol", "pe_oi", "ce_oi", "RSI(14)", "MA(10)", "ATR(14)", "MACD(7,20,1)", "MA(20, (TRIPLE EXPONENTIAL)) "],
        [df_ce['Date'].iloc[-2], df_ce['symbol'].iloc[-2], put_oi, call_oi, df_ce.iloc[-2, rsi_14_column_number], 
        df_ce.iloc[-2, moving_average_10_column_number], df_ce.iloc[-2, atr_14_column_number], df_ce.iloc[-2, macd_7_20_1_column_number],
        df_ce.iloc[-2, moving_average_20_triple_exponential_column_number]],
        [df_ce['Date'].iloc[-3], df_ce['symbol'].iloc[-3], put_oi, call_oi, df_ce.iloc[-3, rsi_14_column_number], 
        df_ce.iloc[-3, moving_average_10_column_number], df_ce.iloc[-3, atr_14_column_number], df_ce.iloc[-3, macd_7_20_1_column_number],
        df_ce.iloc[-3, moving_average_20_triple_exponential_column_number]],
    ]
    print("=====Call Side Check - Start=========")
    print(tabulate(print_data, headers="firstrow", tablefmt="fancy_grid"))
    print("=====Call Side Check - End===========")
    call_side_conditions = [
        call_oi != 0 and put_oi != 0,
        put_oi > call_oi,
        any([
            df_ce.iloc[-2, rsi_14_column_number] > df_ce.iloc[-2, moving_average_10_column_number], 
            df_ce.iloc[-3, rsi_14_column_number] > df_ce.iloc[-3, moving_average_10_column_number], 
            ]),
        any([
            df_ce.iloc[-2, atr_14_column_number] > df_ce.iloc[-2, moving_average_10_column_number],
            df_ce.iloc[-3, atr_14_column_number] > df_ce.iloc[-3, moving_average_10_column_number],
            ]),
        df_ce.iloc[-2, macd_7_20_1_column_number] > 0,
        any([
            df_ce.iloc[-2, macd_7_20_1_column_number] > df_ce.iloc[-2, moving_average_20_triple_exponential_column_number],
            df_ce.iloc[-3, macd_7_20_1_column_number] > df_ce.iloc[-3, moving_average_20_triple_exponential_column_number],
        ])
    ]
    if all(call_side_conditions):
        # call side - bullish
        return df_ce
    print_data = [
        ["Time", "Symbol", "pe_oi", "ce_oi", "RSI(14)", "MA(10)", "ATR(14)", "MACD(7,20,1)", "MA(20, (TRIPLE EXPONENTIAL))"],
        [df_pe['Date'].iloc[-2], df_pe['symbol'].iloc[-2], put_oi, call_oi, df_pe.iloc[-2, rsi_14_column_number], 
        df_pe.iloc[-2, moving_average_10_column_number], df_pe.iloc[-2, atr_14_column_number], df_pe.iloc[-2, macd_7_20_1_column_number],
        df_pe.iloc[-2, moving_average_20_triple_exponential_column_number]],
        [df_pe['Date'].iloc[-3], df_pe['symbol'].iloc[-3], put_oi, call_oi, df_pe.iloc[-3, rsi_14_column_number], 
        df_pe.iloc[-3, moving_average_10_column_number], df_pe.iloc[-3, atr_14_column_number], df_pe.iloc[-3, macd_7_20_1_column_number],
        df_pe.iloc[-3, moving_average_20_triple_exponential_column_number]],
    ]
    print("=====Put Side Check - Start=========")
    print(tabulate(print_data, headers="firstrow", tablefmt="fancy_grid"))
    print("=====Put Side Check - End===========")
    put_side_conditions = [
        call_oi != 0 and put_oi != 0,
        call_oi > put_oi,
        any([
            df_pe.iloc[-2, rsi_14_column_number] > df_pe.iloc[-2, moving_average_10_column_number],
            df_pe.iloc[-3, rsi_14_column_number] > df_pe.iloc[-3, moving_average_10_column_number],
        ]),
        any([
            df_pe.iloc[-2, atr_14_column_number] > df_pe.iloc[-2, moving_average_10_column_number],
            df_pe.iloc[-3, atr_14_column_number] > df_pe.iloc[-3, moving_average_10_column_number],
        ]),
        df_pe.iloc[-2, macd_7_20_1_column_number] > 0,
        any([
            df_pe.iloc[-2, macd_7_20_1_column_number] > df_pe.iloc[-2, moving_average_20_triple_exponential_column_number],
            df_pe.iloc[-3, macd_7_20_1_column_number] > df_pe.iloc[-3, moving_average_20_triple_exponential_column_number],
        ])
    ]
    if all(put_side_conditions):
        # put side - bearish
        return df_pe
    return pd.DataFrame()
    

def place_orders(config_details: dict, symbol: str, ltp, action="B") -> dict:
    """
    NIFTY': {'underlying': 'NSE:NIFTY 50', 'expiry': '23OCT', 
    'lotsize': 25, 'stoploss': 10, 'segment': 'NFO-OPT', 'multiplier': 1}}"
    """
    mode = config_details["live"]
    print(f"{action} order placement triggered, on {'paper' if mode==0 else 'live'} mode")
    if mode == 0:
        return
    args = dict(
        exchange="NFO",
        tradingsymbol=symbol,
        transaction_type="BUY",
        quantity=config_details['lotsize'] * config_details['multiplier'],
        product="MIS",
        order_type="MARKET",
        price=None,
        validity=None,
    )
    
    # Sell order
    if action == "S":
        
        args['transaction_type'] = "SELL"
        args['order_type'] == "SL-M"
        args['trigger_price'] = ltp - config_details['stoploss']
        _ = kite_client.place_order(
            variety="regular", **args)
        return 
    
    # Buy order
    _ = kite_client.place_order(
        variety="regular", **args)

    return


def check_indicator_exit(df, sl):
    """
      IF MACD(7,20,1) < MOVING AVERAGE (20, (TRIPPLE EXPONNENTIAL)) PREFERABLY CROSSING FROM ABOVE.
    """
    symbol_name = df['symbol'].unique()[0]
    ltp = 999999999999
    for symbol, details in symbol_details.items():
        if symbol_name.startswith(symbol):
            dct_ltp = ltp_for_underlying([details['underlying']], kite_client)
            if dct_ltp.values():
                ltp = next(iter(dct_ltp.values()))
                break
    print_data = [
        ["Time", "Symbol", "MACD(7,20,1)", "MOVING AVERAGE (20, (TRIPPLE EXPONNENTIAL))", "LTP", "SL"],
        [df['Date'].iloc[-2], df['symbol'].iloc[-2], df.iloc[-2, macd_7_20_1_column_number], df.iloc[-2, moving_average_20_triple_exponential_column_number], ltp, sl],
        [df['Date'].iloc[-3], df['symbol'].iloc[-3], df.iloc[-3, macd_7_20_1_column_number], df.iloc[-3, moving_average_20_triple_exponential_column_number], ltp, sl]
    ]
    print("==============")
    print(tabulate(print_data, headers="firstrow", tablefmt="fancy_grid"))
    print("==============")

    if (
        df.iloc[-2, macd_7_20_1_column_number] < df.iloc[-2, moving_average_20_triple_exponential_column_number] or
        df.iloc[-3, macd_7_20_1_column_number] < df.iloc[-3, moving_average_20_triple_exponential_column_number] or
        ltp < sl
    ):
        return df
    return pd.DataFrame()


"""
    We want to keep track of the events
    with the keyword throughout the lifecycle
    of the program. for example "BANKNIFTY"
    and continue to populate it with needed
    values while dropping the unnecessary
"""
configuration_details: list[dict] = utils.get_config_from_yaml()

# Playwright operations
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)
context = browser.new_context()

# Other operations
enc_token = login_to_kite_web_using_playwright(
    configuration_details["credentials"], context)
if not enc_token:
    print("enc_token is missing. Please check")
    sys.exit(-1)
kite_client = kite_connect.KiteApp(enc_token)

symbol_details_with_common: list[dict] = configuration_details["symbols"]
symbol_details: dict = utils.merge_common_to_symbols(
    symbol_details_with_common)
print(symbol_details)
dct_underlying: list = underlying_from_config(symbol_details)
# print(dct_underlying)
# position = False
order_placed_instrument = None
order_placed_ltp = None
instrument_details = utils.get_instrument_details()
while True:
    # if not position:
    if not order_placed_instrument:
        dct_ltp = ltp_for_underlying(dct_underlying, kite_client)
        updated_configuration_details = coin_option_names(
            symbol_details, instrument_details, dct_ltp, kite_client)
        # print(updated_configuration_details)
        for symbol, details in updated_configuration_details.items():
            df_ce = download_playwright(details["ce_url"], context)
            df_pe = download_playwright(details["pe_url"], context)
            df: pd.DataFrame() = generate_signal_fm_df(df_ce, df_pe, details)
            if df.index.size > 0:
                # position = True
                order_placed_instrument = df['symbol'].unique()[0]
                for symbol, details in symbol_details.items():
                    if order_placed_instrument.startswith(symbol):
                        dct_ltp = ltp_for_underlying([details['underlying']], kite_client)
                        if dct_ltp.values():
                            order_placed_ltp = next(iter(dct_ltp.values()))
                            place_orders(details, order_placed_instrument, order_placed_ltp, action="B")
                # trigger buy order for inst_name
                # if there is signal key in dct_options
                break
    else:
        instrument_token = get_instrument_token(
            order_placed_instrument, instrument_details)
        url_to_download = kite_chart_url.format(
            option_name=order_placed_instrument, instrument_token=instrument_token)
        df = download_playwright(url_to_download, context)
        sl = list(updated_configuration_details.values())[0]["stoploss"]
        df = check_indicator_exit(df, order_placed_ltp - sl)
        if df.index.size > 0:
            # trigger a sell order for position
            # position = False
            order_placed_instrument = df['symbol'].unique()[0]
            for symbol, details in symbol_details.items():
                if order_placed_instrument.startswith(symbol):
                    place_orders(details, order_placed_instrument, action="S")
            order_placed_instrument = None
        
context.close()
playwright.stop()
