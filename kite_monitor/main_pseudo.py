from pandas import DataFrame
import utils
import utils_playwright
from playwright.sync_api import sync_playwright
import _kite_connect
import sys

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
        key = underlying.split(":")[-1].split()[0]
        tmp = kite_client.ltp(underlying).get(underlying)
        if tmp:
            output_dict[key] = tmp.get("last_price")
    print(output_dict)
    return output_dict


def atm_from_ltp(dct_underlying: dict) -> dict:
    """
       returns dict of form 
        {"BANKNIFTY": 43000, "NSE:NIFTY 50": 12000}               
    """
    pass


def options_from_ltp(dct_atm: dict) -> dict:
    """
        each symbol key from config now will have 
        a pair of options. please note that we should 
        not simply replace the option name like PE 
        instead of CE
        {"BANKNIFTY": ["BANKNIFTY23OCT42800CE", "BANKNIFTY23OCT43200PE"], ..}
    """
    pass


def download_playwright(dct_option: dict) -> DataFrame:
    """
        if the option name is supplied this returns the 
        dataframe. we want to reuse this later for exits
    """
    pass


def generate_signal_fm_df(df_ce: DataFrame, df_pe: DataFrame) -> str:
    """
       if signal is generated it return the name of the option
       a dictionary can be built from the caller of this function.
       {"BANKNIFTY": {"signal": "BANKNIFTY23OCT42800CE"}}
    """
    pass


def update_order_params_with_config(dct_signal: dict) -> dict:
    """
        using the base key, we need to update order update 
        params from config file, so we can generate order
    """
    pass


def place_order(dct_signal: dict) -> dict:
    """

    """
    pass


def exit_trade(dct_signal: dict):
    """

    """
    pass


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
enc_token = utils_playwright.login_to_kite_web_using_playwright(configuration_details["credentials"], context)
if not enc_token:
    print("enc_token is missing. Please check")
    sys.exit(-1)
kite_client = _kite_connect.KiteApp(enc_token)

symbol_details_with_common: list[dict] = configuration_details["symbols"]
symbol_details: dict = utils.merge_common_to_symbols(symbol_details_with_common)
dct_underlying: list = underlying_from_config(symbol_details)
print(dct_underlying)
position = False

while True:
    if not position:
        dct_ltp = ltp_for_underlying(dct_underlying, kite_client)
        break
#         # need to get it through kiteweb, no redis
#         dct_atm = atm_from_ltp(dct_ltp)
#         # get the option symbols involved
#         dct_options = options_from_ltp(dct_atm)
#         # TODO: this is mostly incorrect, adjust accordingly
#         for k, v in dct_options.items():
#             # we download df for call first
#             df_ce = download_playwright(v['symbol']["ce"])
#             # then for put
#             df_pe = download_playwright(v['symbol']["pe"])
#             # compare both and see if there is a signal
#             str_symbol = generate_signal_fm_df(df_ce, df_pe)
#             if str_symbol:
#                 symbol["signal"] = str_symbol
#                 break
#         # if there is signal key in dct_options
#         if "signal" in dct_options:
#             dct_params = update_order_params_fm_config(dct_signal)
#             place_order(dct_params)
#             position = True
#     else:
#         # since we know that the position is True
#         # we have he dct_params, use it to
#         df_exit = download_playwright(dct_params['signal'])
#         # return False if we exited.
#         postion = exit_trade(dct_exit)
context.close()
playwright.stop()