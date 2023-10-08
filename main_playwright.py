from playwright.sync_api import Playwright, sync_playwright, expect
import pandas as pd
import pyotp
import time
import yaml
username = "CP4842"


def get_config_from_yaml(input_file: str) -> dict:
    with open(input_file, "r") as yamlfile:
        config_data =  yaml.safe_load(yamlfile)
        return config_data[0]
    
url_list = [
    'https://kite.zerodha.com/chart/web/ciq/NFO-OPT/NIFTY23OCT17750CE/17210626?theme=dark',
    'https://kite.zerodha.com/chart/web/ciq/NSE/RELIANCE/738561?theme=dark',
    'https://kite.zerodha.com/chart/web/ciq/NSE/NIFTYBEES/2707457?theme=dark',
    'https://kite.zerodha.com/chart/web/ciq/NSE/ICICIBANK/1270529?theme=dark',
    'https://kite.zerodha.com/chart/web/ciq/MCX-FUT/CRUDEOIL23OCTFUT/65611015?theme=dark',
]

def run(playwright: Playwright) -> None:
    config_file = "config.yaml" 
    configuration_details = get_config_from_yaml(config_file) 
    username = configuration_details.get('creds').get('username')
    password = configuration_details.get('creds').get('password')
    t_otp = configuration_details.get('creds').get('totp')
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://kite.zerodha.com/?next=%2Fdashboard")
    page.get_by_label("User ID").click()
    page.get_by_label("User ID").fill(username)
    page.get_by_placeholder("Password").click()
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Login").click()
    otp = pyotp.TOTP(t_otp).now()
    page.get_by_placeholder("••••••").fill(otp)
    #  Commented to improve TAT
    # page.wait_for_load_state("networkidle")
    # page.get_by_role("button", name="I understand").click()
    for url in url_list:
        page3 = context.new_page()
        page3.goto(url)
        page3.wait_for_load_state("networkidle")
        page3.frame_locator("#chart-iframe").locator(".ciq-DT > span").first.click()
        page3.wait_for_load_state("networkidle")
        with page3.expect_download() as download_info:
            page3.frame_locator("#chart-iframe").get_by_role("button", name="Download").click()
            download1 = download_info.value
            print(pd.read_csv(f"{download1.path()}").head(1))
        page3.close()


    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        print(time.time())
        run(playwright)
        print(time.time())

    # 1696667769.3045878
    # 1696667736.0103898

