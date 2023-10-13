
import utils
import re
import pprint
from playwright.sync_api import Playwright, sync_playwright
import pandas as pd

kite_chart_url = 'https://kite.zerodha.com/chart/web/ciq/{segment}/{option_name}/{instrument_token}?theme=dark'


def run(playwright: Playwright,  credentials, symbol_details):
    username = credentials.get('username')
    password = credentials.get('password')
    t_otp = credentials.get('time_based_otp_key')
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
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
    data_frame_details = {}
    for symbol, url in symbol_details.items():
        page3 = context.new_page()
        page3.goto(url)
        page3.wait_for_load_state("networkidle")
        page3.frame_locator("#chart-iframe").locator(".ciq-DT > span").first.click()
        page3.wait_for_load_state("networkidle")
        with page3.expect_download() as download_info:
            page3.frame_locator("#chart-iframe").get_by_role("button", name="Download").click()
            download1 = download_info.value
            # download1.save_as(download1.suggested_filename)
            # print(pd.read_csv(f"{download1.path()}").head(5))
            k = re.sub(r'(\d+)(?=CE|PE)', '', symbol)
            data_frame_details[k] = pd.read_csv(f"{download1.path()}")
        page3.close()
    context.close()
    browser.close()
    return data_frame_details

def get_instrument_token(option_name, df):
    tokens = df[df['tradingsymbol']== option_name ]['instrument_token'].to_list()
    return tokens[0] if len(tokens) >= 1 else 0 
    

def coin_option_names(symbol_details_from_config, instrument_details):
    symbol_details = utils.merge_common_to_symbols(symbol_details_from_config)
    output_symbol_details = {}
    for symbol, details in symbol_details.items():
        ltp = utils.get_ltp_from_redis(details['underlying'])
        atm = utils.get_atm(details['diff'], ltp)
        for i in ["ce", "pe"]:
            val = atm + details[i]
            option_name = symbol+details['expiry']+str(val)+i.upper()
            instrument_token = get_instrument_token(option_name, instrument_details)
            output_symbol_details[option_name] = kite_chart_url.format(segment=details['segment'], 
                                                   option_name=option_name, 
                                                   instrument_token=instrument_token)
    return output_symbol_details
    

if __name__ == "__main__":
    configuration_details: list[dict] = utils.get_config_from_yaml() 
    credentials: dict = configuration_details.get('credentials')
    username: str = credentials.get('username')
    password: str = credentials.get('password')
    t_otp: str = credentials.get('time_based_otp_key')
    symbol_details_from_config: list[dict] = configuration_details.get('symbols')
    instrument_details = utils.get_instrument_details()
    symbol_details = coin_option_names(symbol_details_from_config, instrument_details)
    
    pprint.pprint(symbol_details)
    with sync_playwright() as playwright:
        data_frame_details = run(playwright, credentials, symbol_details)
        # TODO: maheswaran.palaniselvan: Below lines can be put in a diff function
        checked_values = []
        for symbol, df in data_frame_details.items():
            if symbol in checked_values:
                continue
            checked_values.append(symbol)
            if "CE" in symbol:
                opposite_value = symbol.replace("CE", "PE")
                # CE[-3] < PE[-3] and CE[-2] > PE[-2]
                neg_3_ce_value = data_frame_details[symbol]['close'].iloc[-3]
                neg_2_ce_value = data_frame_details[symbol]['close'].iloc[-2]
                neg_3_pe_value = data_frame_details[opposite_value]['close'].iloc[-3]
                neg_2_pe_value = data_frame_details[opposite_value]['close'].iloc[-2]
                if neg_3_ce_value < neg_3_pe_value and neg_2_ce_value > neg_2_pe_value:
                    print(f"CE>PE(Crossing) is achieved")
                
            else:
                opposite_value = symbol.replace("PE", "CE")
                # PE[-3] < CE[-3] and PE[-2] > CE[-2]
                neg_3_pe_value = data_frame_details[symbol]['close'].iloc[-3]
                neg_2_pe_value = data_frame_details[symbol]['close'].iloc[-2]
                neg_3_ce_value = data_frame_details[opposite_value]['close'].iloc[-3]
                neg_2_ce_value = data_frame_details[opposite_value]['close'].iloc[-2]
                if neg_3_pe_value < neg_3_ce_value and neg_2_pe_value > neg_2_ce_value:
                    print(f"PE>CE(Crossing) is achieved")
            
            
            checked_values.append(opposite_value)
            
        


    # otp: str = utils.get_otp(t_otp)
    # print(otp)
    # enc_token = kite_connect.get_enctoken(username, password, otp)
    # kite_app = kite_connect.KiteApp(enc_token)
    # print(kite_app.profile())


