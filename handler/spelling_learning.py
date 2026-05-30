import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SpellingLearning:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver  # webdriver

    def run(self, num_d: int, word_d: list) -> None:  # 핸들러 실행
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        da_e, da_k, _ = word_d

        def find_visible(parent, selector):
            return wait.until(
                lambda _: next(
                    (
                        element
                        for element in parent.find_elements(By.CSS_SELECTOR, selector)
                        if element.is_displayed()
                    ),
                    False,
                )
            )

        # 원래 윈도우 핸들 저장
        original_window = driver.current_window_handle

        # 스펠학습 진입 버튼 찾기 (CSS Selector 사용)
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.btn-spell")
            )
        ).click()  # 스펠학습 진입 버튼

        # 클래스 외부 학습 시 경고 모달 처리
        try:
            alert_modal = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, "alertModal"))
            )
            print("클래스 외부 학습 경고 모달 감지됨. 확인 버튼을 클릭합니다.")
            ok_btn = WebDriverWait(alert_modal, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-primary.btn-ok"))
            )
            ok_btn.click()
            print("경고 모달 승인 완료.")
        except Exception as e:
            print("경고 모달 대기 통과 (감지 안 됨 또는 무시됨):", e)
            pass

        # 새 창(탭)이 열릴 시간을 대기한 뒤 탭 전환
        time.sleep(2)
        if len(driver.window_handles) > 1:
            print("새로운 학습 창이 감지되었습니다. 탭 포커스를 전환합니다.")
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    break

        # 스펠학습 페이지로의 전환 대기
        WebDriverWait(driver, 10).until(
            EC.url_contains("/Spell")
        )

        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#wrapper-learn .btn-opt-start"))
        ).click()  # 스펠학습 시작 버튼
        try:
            for _ in range(1, num_d):
                current_card = wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "#wrapper-learn .CardItem.current.showing")
                    )
                )
                cash_d = find_visible(current_card, ".spell-content").text.split("\n")[0]
                # 스펠학습 정답 찾기 로직 개선 (텍스트 정제 사용)
                import re
                
                def clean(t):
                    # 원문자 및 품사 태그 제거
                    t = re.sub(r'[①-⑩]', '', t)
                    t = re.sub(r'\[[가-힣\s]+\]', '', t)
                    # 공백 및 기호 정리 후 소문자화
                    return "".join(t.split()).lower()

                cash_d_clean = clean(cash_d)
                text = None
                
                for i in range(1, num_d):
                    # 영어/한글 매칭
                    if cash_d_clean == clean(da_e[i]) or cash_d_clean == clean(da_k[i]) or cash_d_clean in clean(da_k[i]) or clean(da_k[i]) in cash_d_clean:
                        if cash_d_clean == clean(da_e[i]):
                            text = da_k[i]
                        else:
                            text = da_e[i]
                        break
                
                if not text:
                    text = "모름"
                    print("모르는 단어 감지됨")
                in_tag = find_visible(current_card, ".spell-input input")
                in_tag.click()
                in_tag.send_keys(text)
                driver.find_element(
                    By.CSS_SELECTOR, "#wrapper-learn .study-bottom .btn-confirm"
                ).click()
                time.sleep(1.5)
                time.sleep(0.5)
        except NoSuchElementException:
            pass
