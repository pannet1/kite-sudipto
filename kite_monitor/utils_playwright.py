import pandas as pd
import utils

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



# for url in url_list:
#     page3 = context.new_page()
#     page3.goto(url)
#     page3.wait_for_load_state("networkidle")
#     page3.frame_locator("#chart-iframe").locator(".ciq-DT > span").first.click()
#     page3.wait_for_load_state("networkidle")
#     with page3.expect_download() as download_info:
#         page3.frame_locator("#chart-iframe").get_by_role("button", name="Download").click()
#         download1 = download_info.value
#         print(pd.read_csv(f"{download1.path()}").head(1))
#     page3.close()
