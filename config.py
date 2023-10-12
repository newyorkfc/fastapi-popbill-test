import os

from dotenv import load_dotenv
from popbill import TaxinvoiceService

load_dotenv()
SERVER_IP = os.getenv("SERVER_IP")
SERVER_URL = os.getenv("SERVER_URL")

''' 기본 세팅값 설정 '''
POPBILL_LINK_ID = os.getenv("POPBILL_LINK_ID")  # 링크아이디
POPBILL_SECRET_KEY = os.getenv("POPBILL_SECRET_KEY")  # 발급받은 비밀키, 유출에 주의하시기 바랍니다.
POPBILL_IS_TEST = True  # 연동환경 설정값, 개발용(True), 상업용(False)
POPBILL_IP_RESTRICT_ON_OFF = True  # 인증토큰 IP제한기능 사용여부, 권장(True)
POPBILL_USE_STATIC_IP = False  # 팝빌 API 고정 IP 사용여부, True-사용 False-미사용, 기본값(false)
POPBILL_USE_LOCAL_TIME_YN = True  # 로컬시스템 시간 사용여부, 권장(True)

# settings.py 작성한 LinkID, SecretKey를 이용해 TaxinvoiceService 객체 생성
taxinvoiceService = TaxinvoiceService(LinkID=POPBILL_LINK_ID, SecretKey=POPBILL_SECRET_KEY)
taxinvoiceService.IsTest = POPBILL_IS_TEST  # 연동환경 설정값, 개발용(True), 상업용(False)
taxinvoiceService.IPRestrictOnOff = POPBILL_IP_RESTRICT_ON_OFF  # 인증토큰 IP제한기능 사용여부, 권장(True)
taxinvoiceService.UseStaticIP = POPBILL_USE_STATIC_IP  # 팝빌 API 서비스 고정 IP 사용여부, true-사용, false-미사용, 기본값(false)
taxinvoiceService.UseLocalTimeYN = POPBILL_USE_LOCAL_TIME_YN  # 로컬시스템 시간 사용여부, 권장(True)

''' 추가 세팅값 설정 '''
POPBILL_CORP_NUM = os.getenv("POPBILL_CORP_NUM")  # 팝빌회원 사업자번호
POPBILL_USER_ID = os.getenv("POPBILL_USER_ID")  # 팝빌회원 아이디

ISSUE_TYPE = "정발행"
TAX_TYPE = "과세"
PURPOSE_TYPE = "영수"
CHARGE_DIRECTION = "정과금"
INVOICER_CORP_NUM = POPBILL_CORP_NUM
INVOICER_CORP_NAME = "공급자상호"
INVOICER_CEO_NAME = "공급자대표자성명"
INVOICEE_TYPE = "사업자"
MGT_KEY_TYPE = "SELL"
