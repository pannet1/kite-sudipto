from pandas import DataFrame
import utils
from pprint import pprint

kite_chart_url = 'https://kite.zerodha.com/chart/web/ciq/NFO-OPT/{option_name}/{instrument_token}?theme=dark'


def underlying_from_config() -> list:
    """
        config file should return underlying
        underlying[0] = { 'keyword': 'NIFTY', 'symbol': 'NIFTY 50'}
        underlying[1] = { 'keyword': 'BANKNIFTY', 'symbol': 'BANKNIFTY'}
    """
    configuration_details: list[dict] = utils.get_config_from_yaml()
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    symbol_details_from_config: list[dict] = configuration_details.get(
        'symbols')
    return symbol_details_from_config


def get_instrument_token(option_name, df):
    tokens = df[df['tradingsymbol'] ==
                option_name]['instrument_token'].to_list()
    return tokens[0] if len(tokens) >= 1 else 0


def coin_option_names(symbol_details_from_config, instrument_details):
    # delete first element common
    for details in symbol_details_from_config:
        symbol = list(details.keys())[0]  # Get the symbol from the dictionary
        if symbol != "common":
            details = details[symbol]  # Extract details for the symbol
            print(details)
            ltp = utils.get_ltp_from_redis(details['underlying'])
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
symbol_details_from_config = underlying_from_config()
instrument_details = utils.get_instrument_details()
position = False
while True:
    if not position:
        # need to get it through kiteweb, no redis
        symbol_details = coin_option_names(
            symbol_details_from_config, instrument_details)
        # TODO: this is mostly incorrect, adjust accordingly
        print(symbol_details)
        for symbol in symbol_details:
            pprint(symbol)
            for k, v in symbol.items():
                # we download df for call first
                df_ce = download_playwright(v["ce"])
                # then for put
                df_pe = download_playwright(v["pe"])
                # compare both and see if there is a signal
                str_symbol = generate_signal_fm_df(df_ce, df_pe)
                if str_symbol:
                    symbol["signal"] = str_symbol
                    break
        # if there is signal key in dct_options
        if "signal" in symbol_details:
            dct_params = update_order_params_fm_config(dct_signal)
            place_order(dct_params)
            position = True
    else:
        # since we know that the position is True
        # we have he dct_params, use it to
        df_exit = download_playwright(dct_params['signal'])
        # return False if we exited.
        postion = exit_trade(dct_exit)
