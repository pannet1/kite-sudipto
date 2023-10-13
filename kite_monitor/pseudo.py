from pandas import DataFrame


def underlying_from_config() -> list:
    """
        config file should return underlying 
        underlying[0] = { 'keyword': 'NIFTY', 'symbol': 'NIFTY 50'}
        underlying[1] = { 'keyword': 'BANKNIFTY', 'symbol': 'BANKNIFTY'}
    """
    pass


def ltp_for_underlying(lst_underlying: list) -> dict:
    """
        kite api will return ltp if list is passed
        like ["NSE:NIFTY 50", "NSE:BANKNIFTY"]
        now we build a dict of form, from keyword 
        {"BANKNIFTY": 43020, "NIFTY": 12021}               
    """
    pass


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


def place_order(dct_signal: dict) -> dct:
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
dct_underlying = underlying_from_config()
position = False
while True:
    if not position:
        dct_ltp = ltp_for_underlying(dct_underlying)
        # need to get it through kiteweb, no redis
        dct_atm = atm_from_ltp(dct_ltp)
        # get the option symbols involved
        dct_options = options_from_ltp(dct_atm)
        # TODO: this is mostly incorrect, adjust accordingly
        for k, v in dct_options.items():
            # we download df for call first
            df_ce = download_playwright(v['symbol']["ce"])
            # then for put
            df_pe = download_playwright(v['symbol']["pe"])
            # compare both and see if there is a signal
            str_symbol = generate_signal_fm_df(df_ce, df_pe)
            if str_symbol:
                symbol["signal"] = str_symbol
                break
        # if there is signal key in dct_options
        if "signal" in dct_options:
            dct_params = update_order_params_fm_config(dct_signal)
            place_order(dct_params)
            position = True
    else:
        # since we know that the position is True
        # we have he dct_params, use it to
        df_exit = download_playwright(dct_params['signal'])
        # return False if we exited.
        postion = exit_trade(dct_exit)
