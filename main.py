import time
import warnings
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from handler.recall_learning import RecallLearning
from handler.spelling_learning import SpellingLearning
from selenium.webdriver.chrome.options import Options

# 함수불러오기
from utility import (
    chd_wh,
    get_account,
    word_get,
    choice_set,
    choice_class,
    classcard_api_post,
    parse_set_url,
    get_sets_from_current_page,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)

account = get_account()  # 계정 가져오기

print("크롬 드라이브를 불러오고 있습니다 잠시만 기다려주세요!")

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--log-level=1')

# 드라이버 생성
driver = webdriver.Chrome(options=chrome_options)

# 로그인 시행
driver.get("https://www.classcard.net/Login")
wait = WebDriverWait(driver, 10)
id_element = wait.until(EC.visibility_of_element_located((By.NAME, "login_id")))
pw_element = wait.until(EC.visibility_of_element_located((By.NAME, "login_pwd")))
# 키보드 자동 입력은 사이트에서 차단하므로 값만 설정한다.
driver.execute_script(
    "arguments[0].value = arguments[1]; arguments[2].value = arguments[3];",
    id_element,
    account["id"],
    pw_element,
    account["pw"],
)
wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-login"))).click()
wait.until(EC.url_changes("https://www.classcard.net/Login"))

# 세트 및 클래스 정보 획득을 위한 루프
while True:
    os.system("cls" if os.name == "nt" else "clear")
    print("학습 모드를 선택해주세요.")
    print("Ctrl + C 를 눌러 종료")
    print("[1] 가입된 클래스에서 세트 선택하여 학습 (기존)")
    print("[2] 현재 브라우저 화면의 세트 중 선택하여 학습 (나의 폴더/세트 화면 등)")
    print("[3] 학습할 세트 URL 직접 입력")
    try:
        mode = int(input(">>> "))
        if mode not in [1, 2, 3]:
            raise ValueError
    except ValueError:
        print("올바른 번호를 입력해주세요.")
        time.sleep(1)
        continue
    except KeyboardInterrupt:
        quit()

    if mode == 1:
        # 클래스 선택
        class_dict = {}
        try:
            class_list_element = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".left-class-list"))
            )
            class_count = len(class_list_element.find_elements(By.TAG_NAME, "a"))
            for class_item, i in zip(
                class_list_element.find_elements(By.TAG_NAME, "a"),
                range(class_count),
            ):
                class_temp = {}
                class_temp["class_name"] = class_item.text
                class_temp["class_id"] = class_item.get_attribute("href").split("/")[-1]
                if class_temp["class_id"] == "joinClass":
                    break
                class_dict[i] = class_temp
        except Exception:
            pass

        if len(class_dict) == 0:
            print("가입된 클래스가 없습니다. 잠시 후 메뉴로 돌아갑니다.")
            time.sleep(2)
            continue
        elif len(class_dict) == 1:
            choice_class_val = 0
        else:
            choice_class_val = choice_class(class_dict=class_dict)  # 클래스 입력

        class_id = class_dict[choice_class_val].get("class_id")  # 클래스 아이디 가져오기
        driver.get(f"https://www.classcard.net/ClassMain/{class_id}")  # 클래스 페이지로 이동
        time.sleep(1)  # 로딩 대기

        # 세트 선택
        try:
            sets_div = driver.find_element(
                By.XPATH, "/html/body/div[1]/div[2]/div/div/div[2]/div[3]/div"
            )
            sets = sets_div.find_elements(By.CLASS_NAME, "set-items")
            sets_count = len(sets)
            sets_dict = {}
            for set_item, i in zip(sets, range(sets_count)):
                set_temp = {}
                set_temp["card_num"] = (
                    set_item.find_element(By.TAG_NAME, "a").find_element(By.TAG_NAME, "span").text
                )  # 카드 개수 가져오기 예) "10 카드"
                set_temp["title"] = set_item.find_element(By.TAG_NAME, "a").text.replace(
                    set_temp["card_num"], ""
                )  # 카드 개수 제거
                set_temp["set_id"] = set_item.find_element(By.TAG_NAME, "a").get_attribute(
                    "data-idx"
                )  # 세트 아이디 가져오기
                set_temp["class_id"] = class_id
                sets_dict[i] = set_temp
            
            if len(sets_dict) == 0:
                print("클래스 내에 학습할 세트가 없습니다.")
                time.sleep(2)
                continue

            set_choice = choice_set(sets_dict)  # 세트 입력
            set_id = sets_dict[set_choice]["set_id"]
            class_id = sets_dict[set_choice]["class_id"]
            set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
            break
        except Exception as e:
            print("세트 목록을 가져오는 데 실패했습니다.", e)
            time.sleep(2)
            continue

    elif mode == 2:
        print("\n브라우저에서 학습할 세트가 있는 페이지(나의 폴더, 나의 세트 등)로 이동한 후 엔터를 입력해주세요.")
        input("엔터를 누르면 페이지의 세트들을 읽어옵니다...")
        sets_dict = get_sets_from_current_page(driver)
        
        if len(sets_dict) == 0:
            print("현재 페이지에서 학습할 세트를 찾지 못했습니다. 다시 시도해 주세요.")
            time.sleep(2)
            continue
        
        set_choice = choice_set(sets_dict)
        set_id = sets_dict[set_choice]["set_id"]
        class_id = sets_dict[set_choice]["class_id"]
        set_site = f"https://www.classcard.net/set/{set_id}/{class_id}"
        break

    elif mode == 3:
        print("\n학습할 세트의 URL을 입력해주세요.")
        print("예) https://www.classcard.net/set/123456 또는 https://www.classcard.net/set/123456/7890")
        url_input = input(">>> ").strip()
        parsed_set_id, parsed_class_id = parse_set_url(url_input)
        if parsed_set_id:
            set_id = parsed_set_id
            class_id = parsed_class_id
            set_site = url_input
            break
        else:
            print("올바르지 않은 클래스카드 세트 URL 형식입니다. 다시 시도해주세요.")
            time.sleep(2)
            continue

driver.get(set_site)  # 세트 페이지로 이동
time.sleep(1)  # 로딩 대기

user_id = int(driver.execute_script("return c_u;"))  # API 요청을 위해 유저 아이디 가져오기

# 단어 저장
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown > a",
).click()  # 학습구간 선택
driver.find_element(
    By.CSS_SELECTOR,
    "body > div.test > div.p-b-sm > div.set-body.m-t-25.m-b-lg > div.m-b-md.pos-relative > div.dropdown.open > ul > li:nth-child(1) > a",
).click()  # 학습구간 전체로 변경
html = BeautifulSoup(driver.page_source, "html.parser")  # 페이지 소스를 html로 파싱
cards_ele = html.find("div", class_="flip-body")  # 카드들을 찾음
num_d = len(cards_ele.find_all("div", class_="flip-card")) + 1  # 카드의 개수를 구함
time.sleep(0.5)  # 로딩 대기
word_d = word_get(driver, num_d)  # 단어를 가져옴
da_e, da_k, da_kyn = word_d

ch_d = chd_wh()  # 학습유형 입력
while 1:
    if ch_d == 1:
        print("암기학습은 지원하지 않습니다.")
    elif ch_d == 2:
        print("리콜학습을 시작합니다.")
        controler = RecallLearning(driver=driver)  # 암기 학습 클래스 생성
        controler.run(num_d=num_d, word_d=word_d)  # 학습 시작
    elif ch_d == 3:
        print("스펠학습을 시작합니다.")
        controler = SpellingLearning(driver=driver)  # 스펠 학습 클래스 생성
        controler.run(num_d=num_d, word_d=word_d)  # 학습 시작
    elif ch_d == 4:
        print("테스트학습은 지원하지 않습니다.")

    elif ch_d == 5:
        print("암기학습 API 요청을 시작합니다.")
        classcard_api_post(
            user_id=user_id,
            set_id=set_id,
            class_id=class_id,
            view_cnt=num_d,
            activity=1,
        )
    elif ch_d == 6:
        print("리콜학습 API 요청을 시작합니다.")
        classcard_api_post(
            user_id=user_id,
            set_id=set_id,
            class_id=class_id,
            view_cnt=num_d,
            activity=2,
        )
    elif ch_d == 7:
        print("스펠학습 API 요청을 시작합니다.")
        classcard_api_post(
            user_id=user_id,
            set_id=set_id,
            class_id=class_id,
            view_cnt=num_d,
            activity=3,
        )
    print("학습이 종료되었습니다.")
    driver.get(set_site)  # 다시 세트페이지로 이동
    time.sleep(1)
