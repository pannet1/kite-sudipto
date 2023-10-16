import pandas as pd
import utils
import utils_playwright
from playwright.sync_api import sync_playwright
import _kite_connect
import sys

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


def options_from_ltp(dct_atm: dict) -> dict:
    """
        each symbol key from config now will have
        a pair of options. please note that we should
        not simply replace the option name like PE
        instead of CE
        {"BANKNIFTY": ["BANKNIFTY23OCT42800CE", "BANKNIFTY23OCT43200PE"], ..}
    """
    pass


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
    with page3.expect_download() as download_info:
        page3.frame_locator(
            "#chart-iframe").get_by_role("button", name="Download").click()
        download1 = download_info.value
        df = pd.read_csv(f"{download1.path()}")
    page3.close()
    return df


def generate_signal_fm_df(df_ce: pd.DataFrame, df_pe: pd.DataFrame) -> str:
    """
       if signal is generated it return the name of the option
       a dictionary can be built from the caller of this function.
       {"BANKNIFTY": {"signal": "BANKNIFTY23OCT42800CE"}}
    """
    print(df_ce.head())
    print(df_pe.head())
    print(df_ce.columns)
    neg_3_ce_value = df_ce['Close'].iloc[-3]
    neg_2_ce_value = df_ce['Close'].iloc[-2]
    neg_3_pe_value = df_pe['Close'].iloc[-3]
    neg_2_pe_value = df_pe['Close'].iloc[-2]
    if neg_3_ce_value < neg_3_pe_value and neg_2_ce_value > neg_2_pe_value:
        print(f"CE>PE(Crossing) is achieved")
    elif neg_3_pe_value < neg_3_ce_value and neg_2_pe_value > neg_2_ce_value:
        print(f"PE>CE(Crossing) is achieved")
    pass


def update_order_params_with_config(dct_signal: dict) -> dict:
    """
        using the base key, we need to update order update
        params from config file, so we can generate order
    """
    pass


def place_orders(signal: dict) -> dict:
    """
    NIFTY': {'underlying': 'NSE:NIFTY 50', 'expiry': '23OCT', 
    'lotsize': 25, 'stoploss': 10, 'segment': 'NFO-OPT', 'multiplier': 1}}"
    """
    args = dict(
        exchange="NFO",
        tradingsymbol=signal['tradingsymbol'],
        transaction_type="BUY",
        quantity=signal['lotsize'] * signal['multiplier'],
        product="MIS",
        order_type="MARKET",
        price=None,
        validity=None,
    )
    signal['entry_order_id'] = kite_client.order_place(
        variety="regular", **args)

    args['transaction_type'] = "SELL"
    args['order_type'] == "SL-M"
    args['trigger_price'] = 0  # ltp - signal['stoploss']
    signal['exit_order_id'] = kite_client.order_place(
        variety="regular", **args)


return signal


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
browser = playwright.chromium.launch()
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
position = False
instrument_details = utils.get_instrument_details()
while True:
    if not position:
        dct_ltp = ltp_for_underlying(dct_underlying, kite_client)
        updated_configuration_details = coin_option_names(
            symbol_details, instrument_details, dct_ltp)
        print(updated_configuration_details)
        for symbol, details in updated_configuration_details.items():
            df_ce = download_playwright(details["ce_url"], context)
            df_pe = download_playwright(details["pe_url"], context)
            str_symbol = generate_signal_fm_df(df_ce, df_pe)
        break
       # if there is signal key in dct_options
#         if "signal" in dct_options:
#             dct_params = update_order_params_fm_config(dct_signal)
#             dct_params = place_orders(dct_params)
#             ## we may not needs this if we use a single dictionary for
#             all purpose and hence could while loop with that
#             position = True
#     else:
#         # since we know that the position is True
#         # we have he dct_params, use it to
#         df_exit = download_playwright(dct_params['signal'])
#         # return False if we exited.
#         postion = exit_trade(dct_exit)
context.close()
playwright.stop()
