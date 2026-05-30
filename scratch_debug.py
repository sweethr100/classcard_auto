import time
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from utility import get_account, parse_set_url, get_sets_from_current_page, word_get
from handler.recall_learning import RecallLearning

account = get_account()

chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--log-level=1')

# 브라우저 실행
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://www.classcard.net/Login")

wait = WebDriverWait(driver, 10)
id_element = wait.until(EC.visibility_of_element_located((By.NAME, "login_id")))
pw_element = wait.until(EC.visibility_of_element_located((By.NAME, "login_pwd")))
driver.execute_script(
    "arguments[0].value = arguments[1]; arguments[2].value = arguments[3];",
    id_element,
    account["id"],
    pw_element,
    account["pw"],
)
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-login"))).click()
wait.until(EC.url_changes("https://www.classcard.net/Login"))

print("로그인 완료!")
time.sleep(3)

# 첫 번째 세트로 이동
sets_dict = get_sets_from_current_page(driver)
if len(sets_dict) > 0:
    first_set = sets_dict[0]
    print(f"발견한 첫 번째 세트: {first_set['title']} (ID: {first_set['set_id']})")
    set_site = f"https://www.classcard.net/set/{first_set['set_id']}/{first_set['class_id']}"
else:
    print("기본 세트로 이동합니다.")
    set_site = "https://www.classcard.net/set/1460"

driver.get(set_site)
time.sleep(2)

# 학습구간 전체로 변경
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
).click()
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
).click()

html = BeautifulSoup(driver.page_source, "html.parser")
cards_ele = html.find("div", class_="flip-body")
num_d = len(cards_ele.find_all("div", class_="flip-card")) + 1
time.sleep(0.5)

print(f"단어 정보를 파싱하는 중... 총 단어 수: {num_d - 1}")
word_d = word_get(driver, num_d)
print("단어 파싱 완료! 리콜 학습을 시작합니다.")

controler = RecallLearning(driver=driver)
controler.run(num_d=num_d, word_d=word_d)

print("리콜 학습 매크로 작동 테스트 성공적으로 완료!")
driver.quit()
