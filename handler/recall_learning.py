import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class RecallLearning:
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver  # webdriver

    def run(self, num_d: int, word_d: list) -> None:  # 핸들러 실행
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        da_e, da_k, _ = word_d
        # 원래 윈도우 핸들 저장
        original_window = driver.current_window_handle
        
        # 리콜학습 진입 버튼 찾기 (CSS Selector 사용)
        wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "a.btn-recall")
            )
        ).click()  # 리콜학습 진입 버튼

        # 클래스 외부 학습 시 경고 모달 처리 (안전하게 대기 시간 5초로 설정)
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
        time.sleep(3)
        print("=== 디버깅: 현재 윈도우 목록 ===")
        for idx, handle in enumerate(driver.window_handles):
            try:
                driver.switch_to.window(handle)
                print(f"Tab {idx} URL: {driver.current_url}")
            except Exception as e:
                print(f"Tab {idx} Error: {e}")
        
        # 원래 윈도우로 일단 복구
        try:
            driver.switch_to.window(original_window)
        except Exception:
            pass

        if len(driver.window_handles) > 1:
            print("새로운 학습 창이 감지되었습니다. 탭 포커스를 전환합니다.")
            for handle in driver.window_handles:
                if handle != original_window:
                    driver.switch_to.window(handle)
                    break

        # 리콜학습 페이지로의 전환 대기
        WebDriverWait(driver, 10).until(
            EC.url_contains("/Recall")
        )

        wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#wrapper-learn .btn-opt-start"))
        ).click()  # 리콜학습 시작 버튼

        for _ in range(1, num_d):  # 단어 수 만큼 반복
            current_card = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#wrapper-learn .CardItem.current.showing")
                )
            )
            cash_d = current_card.find_element(
                By.CSS_SELECTOR, ".card-top .normal-body"
            ).text  # 메인 단어 추출
            choices = current_card.find_elements(
                By.CSS_SELECTOR, ".cc-table.middle.fill-parent-w"
            )
            # 정답 매칭 알고리즘 개선
            import re
            
            def clean(t):
                # 원문자 및 품사 태그 제거
                t = re.sub(r'[①-⑩]', '', t)
                t = re.sub(r'\[[가-힣\s]+\]', '', t)
                # 공백 및 특수문자 정리 후 소문자화
                return "".join(t.split()).lower()

            cash_d_clean = clean(cash_d)
            click_count = 0

            for choice_item in choices:
                choice_text = choice_item.find_element(
                    By.CSS_SELECTOR, ".cc-ellipsis"
                ).text
                choice_text_clean = clean(choice_text)

                # 수집된 단어 데이터를 순회하며 정답 비교
                for i in range(1, num_d):
                    # 한글 뜻 비교
                    if choice_text_clean in clean(da_k[i]) or clean(da_k[i]) in choice_text_clean:
                        if cash_d_clean == clean(da_e[i]):
                            choice_item.click()
                            click_count += 1
                            break
                    # 영어 단어 비교 (문제와 보기의 관계가 반대인 경우 대비)
                    elif choice_text_clean == clean(da_e[i]):
                        if cash_d_clean in clean(da_k[i]) or clean(da_k[i]) in cash_d_clean:
                            choice_item.click()
                            click_count += 1
                            break
            
            if click_count == 0:
                print("모르는 단어 감지됨")
                random.choice(choices).click()
            time.sleep(3)
