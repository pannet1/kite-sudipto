import pandas as pd
import utils
import utils_playwright
from playwright.sync_api import sync_playwright
import _kite_connect
import sys
import traceback

kite_chart_url = 'https://kite.zerodha.com/chart/web/ciq/NFO-OPT/{option_name}/{instrument_token}?theme=dark'


def underlying_from_config(symbol_details_from_config: list[dict]) -> list:
    """
        config file should return underlying
        underlying[0] = { 'keyword': 'NIFTY', 'symbol': 'NIFTY 50'}
        underlying[1] = { 'keyword': 'BANKNIFTY', 'symbol': 'BANKNIFTY'}
    """
    return [symbol_details["underlying"] for symbol_details in symbol_details_from_config.values()]


def ltp_for_underlying(lst_underlying: list, kite_client: _kite_connect.KiteApp) -> dict:
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
    print(output_dict)
    return output_dict


def get_instrument_token(option_name, df):
    tokens = df[df['tradingsymbol'] ==
                option_name]['instrument_token'].to_list()
    return tokens[0] if len(tokens) >= 1 else 0


def coin_option_names(symbol_details_from_config, instrument_details, dct_ltp):
    # delete first element common
    for symbol, details in symbol_details_from_config.items():
        print(details)
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

        val = atm + details['pe']
        option_name = symbol + details['expiry'] + str(val) + 'PE'
        instrument_token = get_instrument_token(
            option_name, instrument_details)

        details["pe_" + "url"] = kite_chart_url.format(
            option_name=option_name, instrument_token=instrument_token)
        details['put'] = option_name

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
        traceback.print_exc()
        
    with page3.expect_download() as download_info:
        page3.frame_locator(
            "#chart-iframe").get_by_role("button", name="Download").click()
        download1 = download_info.value
        df = pd.read_csv(f"{download1.path()}")
        # url.split("/")[-2]
        df["symbol"] = url.split("/")[-2]
    page3.close()
    return df


def generate_signal_fm_df(df_ce: pd.DataFrame, df_pe: pd.DataFrame) -> str:
    """
       if signal is generated it return the name of the option
       a dictionary can be built from the caller of this function.
       {"BANKNIFTY": {"signal": "BANKNIFTY23OCT42800CE"}}
    """
    # print(df_ce.head())
    # print(df_pe.head())
    # print(df_ce.columns)
    neg_3_ce_value = df_ce['Close'].iloc[-3]
    neg_2_ce_value = df_ce['Close'].iloc[-2]
    neg_3_pe_value = df_pe['Close'].iloc[-3]
    neg_2_pe_value = df_pe['Close'].iloc[-2]
    print(neg_3_ce_value, neg_2_ce_value, neg_3_pe_value, neg_2_pe_value)
    print(df_ce.iloc[-3, 4], df_ce.iloc[-2, 4], df_pe.iloc[-3, 4], df_pe.iloc[-2, 4], )
    if neg_3_ce_value < neg_3_pe_value and neg_2_ce_value > neg_2_pe_value:
        print(f"CE>PE(Crossing) is achieved")
        return df_ce
    elif neg_3_pe_value < neg_3_ce_value and neg_2_pe_value > neg_2_ce_value:
        print(f"PE>CE(Crossing) is achieved")
        return df_pe
    return pd.DataFrame()
    

def is_other_conditions(df):
    """
    [
        'Date',                                     # 0
        'Open',                                     # 1                
        'High',                                     # 2
        'Low',                                      # 3
        'Close',                                    # 4
        '% Change',                                 # 5
        '% Change vs Average',                      # 6
        'Volume',                                   # 7
        'Result ‌W Acc Dist‌ (n)',                    # 8
        'MA ‌ma‌ (57,Result ‌W Acc Dist‌ (n),ma,0)',    # 9
        'MACD ‌macd‌ (7,21,9)',                       # 10
        'Signal ‌macd‌ (7,21,9)',                     # 11
        '‌macd‌ (7,21,9)_hist',                       # 12 
        'OI',                                       # 13
        'MA ‌ma‌ (20,OI,ema,0)',                      # 14    
        'All Stops ‌ATR Trailing Stop‌ (8,2,points,n)',# 15
        'symbol'                                    # 16    
    ]
    """
    # df.reset_index(inplace=True)
    # macd fast is having short period >
    # macd slow is having long period with bigger number
    macd_fast_column_number = 10 # column number starts from 0
    macd_slow_column_number = 11 #
    acc_dist_column_number = 6
    ma_20_column_number = 7
    open_interest_column_number = 8
    sma_20_column_number = 9
    if( 
        df.iloc[-2, macd_fast_column_number] >= df.iloc[-2, macd_slow_column_number] and 
        # acc dist > 20 MA 
        df.iloc[-2, acc_dist_column_number] > df.iloc[-2, ma_20_column_number] and
        # open interest < 20 Sma 
        df.iloc[-2, open_interest_column_number] < df.iloc[-2, sma_20_column_number]
        ):
      return df
    return pd.DataFrame()


def place_orders(config_details: dict, symbol: str,  action="B") -> dict:
    """
    NIFTY': {'underlying': 'NSE:NIFTY 50', 'expiry': '23OCT', 
    'lotsize': 25, 'stoploss': 10, 'segment': 'NFO-OPT', 'multiplier': 1}}"
    """
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
        dct_ltp = ltp_for_underlying([details['underlying']], kite_client)
        if dct_ltp.values():
            ltp = next(iter(dct_ltp.values()))
            args['transaction_type'] = "SELL"
            args['order_type'] == "SL-M"
            args['trigger_price'] = ltp - details['stoploss']
            _ = kite_client.order_place(
                variety="regular", **args)
            return 
    
    # Buy order
    _ = kite_client.order_place(
        variety="regular", **args)

    return


def check_indicator_exit(df, symbol_details):
    """
      MACD opposite of buy condition 
      i.e MACD fast < MACD slow
      or ltp < ATR indicator
    """
    macd_fast_column_number = 0
    macd_slow_column_number = 1
    atr_indicator_column_number = 2
    symbol_name = df['symbol'].unique()[0]
    ltp = 999999999999
    for symbol, details in symbol_details.items():
        if symbol_name.startswith(symbol):
            dct_ltp = ltp_for_underlying([details['underlying']], kite_client)
            if dct_ltp.values():
                ltp = next(iter(dct_ltp.values()))
                break

    if (
        df.iloc[-2, macd_fast_column_number] < df.iloc[-2, macd_slow_column_number] or
        ltp < df.iloc[-2, atr_indicator_column_number]
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
browser = playwright.chromium.launch(headless=True)
context = browser.new_context()

# Other operations
enc_token = utils_playwright.login_to_kite_web_using_playwright(
    configuration_details["credentials"], context)
if not enc_token:
    print("enc_token is missing. Please check")
    sys.exit(-1)
kite_client = _kite_connect.KiteApp(enc_token)

symbol_details_with_common: list[dict] = configuration_details["symbols"]
symbol_details: dict = utils.merge_common_to_symbols(
    symbol_details_with_common)
print(symbol_details)
dct_underlying: list = underlying_from_config(symbol_details)
print(dct_underlying)
# position = False
order_placed_instrument = None
instrument_details = utils.get_instrument_details()
while True:
    # if not position:
    if not order_placed_instrument:
        dct_ltp = ltp_for_underlying(dct_underlying, kite_client)
        updated_configuration_details = coin_option_names(
            symbol_details, instrument_details, dct_ltp)
        print(updated_configuration_details)
        for symbol, details in updated_configuration_details.items():
            df_ce = download_playwright(details["ce_url"], context)
            df_pe = download_playwright(details["pe_url"], context)
            df: pd.DataFrame() = generate_signal_fm_df(df_ce, df_pe)
            if df.index.size > 0:
                df: pd.DataFrame()  = is_other_conditions(df)
                if df.index.size > 0:
                    # position = True
                    order_placed_instrument = df['symbol'].unique()[0]
                    for symbol, details in symbol_details.items():
                        if order_placed_instrument.startswith(symbol):
                            place_orders(details, order_placed_instrument, action="B")
                    # trigger buy order for inst_name
                    # if there is signal key in dct_options
                    break
    else:
        instrument_token = get_instrument_token(
            order_placed_instrument, instrument_details)
        url_to_download = kite_chart_url.format(
            option_name=order_placed_instrument, instrument_token=instrument_token)
        df = download_playwright(url_to_download, context)
        df = check_indicator_exit(df, symbol_details)
        if df.index.size > 0:
            # trigger a sell order for position
            # position = False
            order_placed_instrument = df['symbol'].unique()[0]
            for symbol, details in symbol_details.items():
                if order_placed_instrument.startswith(symbol):
                    place_orders(details, order_placed_instrument, action="S")
            order_placed_instrument = None
        


#         # since we know that the position is True
#         # we have he dct_params, use it to
#         df_exit = download_playwright(dct_params['signal'])
#         # return False if we exited.
#         postion = exit_trade(dct_exit)
context.close()
playwright.stop()
