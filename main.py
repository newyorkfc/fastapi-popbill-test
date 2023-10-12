import os
from datetime import datetime
from typing import Annotated, Any

from _decimal import Decimal
from fastapi import FastAPI, Form
from fastapi.templating import Jinja2Templates
from popbill import PopbillException, Taxinvoice
from pytz import timezone
from starlette.requests import Request

from config import SERVER_URL, taxinvoiceService, ISSUE_TYPE, CHARGE_DIRECTION, INVOICER_CORP_NAME, \
    INVOICER_CEO_NAME, INVOICER_CORP_NUM, MGT_KEY_TYPE, TAX_TYPE, PURPOSE_TYPE, INVOICEE_TYPE

# TODO: 공급자, 피공급자 정보 추가 (업태, 업종, 주소, 이메일 등)


app = FastAPI()

templates = Jinja2Templates(directory="templates/")


def get_supply_cost(total_amount: Annotated[Any, lambda x: x.isdecimal()]) -> str:
    return str(round(Decimal(str(total_amount)) * Decimal("0.909")))


def get_tax(total_amount: Annotated[Any, lambda x: x.isdecimal()]) -> str:
    return str(round(Decimal(total_amount) * Decimal("0.091")))


@app.get("/")
async def _(request: Request):
    return templates.TemplateResponse(
        name="root.html",
        context=dict(
            request=request,
            SERVER_URL=SERVER_URL,
        )
    )


@app.post("/registIssue")
async def _(request: Request,
            totalAmount: str = Form(...),
            invoiceeCorpNum: str = Form(...),
            invoiceeCorpName: str = Form(...),
            invoiceeCEOName: str = Form(...), ):
    try:
        issue_type = ISSUE_TYPE
        tax_type = TAX_TYPE
        charge_direction = CHARGE_DIRECTION
        write_date = datetime.now(timezone('Asia/Seoul')).strftime("%Y%m%d")
        purpose_type = PURPOSE_TYPE
        supply_cost_total = get_supply_cost(total_amount=totalAmount)
        tax_total = get_tax(total_amount=totalAmount)
        total_amount = totalAmount
        invoicer_mgt_key = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d-%H-%M-%S")
        invoicer_corp_num = INVOICER_CORP_NUM
        invoicer_corp_name = INVOICER_CORP_NAME
        invoicer_ceo_name = INVOICER_CEO_NAME
        invoicee_type = INVOICEE_TYPE
        invoicee_corp_num = invoiceeCorpNum
        invoicee_corp_name = invoiceeCorpName
        invoicee_ceo_name = invoiceeCEOName

        # 세금계산서 정보
        taxinvoice = Taxinvoice(
            issueType=issue_type,  # [필수] 발행형태, [정발행, 역발행, 위수탁] 중 기재
            taxType=tax_type,  # [필수] 과세형태, [과세, 영세, 면세] 중 기재
            chargeDirection=charge_direction,  # [필수] 과금방향, [정과금(공급자), 역과금(공급받는자)]중 기재, 역과금의 경우 역발행세금계산서 발행시에만 사용가능
            writeDate=write_date,  # [필수] 작성일자, 날짜형식(yyyyMMdd)
            purposeType=purpose_type,  # [필수] [영수, 청구, 없음] 중 기재
            supplyCostTotal=supply_cost_total,  # [필수] 공급가액 합계
            taxTotal=tax_total,  # [필수] 세액 합계
            totalAmount=total_amount,  # [필수] 합계금액, 공급가액 합계 + 세액 합계
            invoicerMgtKey=invoicer_mgt_key,  # [필수] 공급자 문서번호, 1~24자리, (영문, 숫자, '-', '_') 조합으로 사업자별로 중복되지 않도록 구성
            invoicerCorpNum=invoicer_corp_num,  # [필수] 공급자 사업자번호 , '-' 없이 10자리 기재.
            invoicerCorpName=invoicer_corp_name,  # [필수] 공급자 상호
            invoicerCEOName=invoicer_ceo_name,  # [필수] 공급자 대표자 성명
            invoiceeType=invoicee_type,  # [필수] 공급받는자 구분, [사업자, 개인, 외국인] 중 기재
            invoiceeCorpNum=invoicee_corp_num,  # [필수] 공급받는자 사업자번호, '-' 제외 10자리, "개인" 인 경우, 주민등록번호 (하이픈 ('-') 제외 13자리)
            invoiceeCorpName=invoicee_corp_name,  # [필수] 공급받는자 상호
            invoiceeCEOName=invoicee_ceo_name,  # [필수] 공급받는자 대표자 성명
        )

        response = taxinvoiceService.registIssue(
            CorpNum=INVOICER_CORP_NUM,
            taxinvoice=taxinvoice,
        )

        return templates.TemplateResponse(
            name="regist_issue.html",
            context=dict(
                request=request,
                code=response.code,
                message=response.message,
                ntsConfirmNum=response.ntsConfirmNum,

                SERVER_URL=SERVER_URL,
                invoicerMgtKey=invoicer_mgt_key,
            )
        )
    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getInfo")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getInfo(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )

        return templates.TemplateResponse(
            name="get_info.html",
            context=dict(
                request=request,
                itemKey=response.itemKey,
                taxType=response.taxType,
                writeDate=response.writeDate,
                regDT=response.regDT,
                issueType=response.issueType,
                supplyCostTotal=response.supplyCostTotal,
                taxTotal=response.taxTotal,
                purposeType=response.purposeType,
                issueDT=response.issueDT,
                lateIssueYN=response.lateIssueYN,
                preIssueDT=response.preIssueDT,
                openYN=response.openYN,
                openDT=response.openDT,
                stateMemo=response.stateMemo,
                stateCode=response.stateCode,
                stateDT=response.stateDT,
                ntsconfirmNum=response.ntsconfirmNum,
                ntsresult=response.ntsresult,
                ntssendDT=response.ntssendDT,
                ntsresultDT=response.ntsresultDT,
                ntssendErrCode=response.ntssendErrCode,
                modifyCode=response.modifyCode,
                interOPYN=response.interOPYN,
                invoicerCorpName=response.invoicerCorpName,
                invoicerCorpNum=response.invoicerCorpNum,
                invoicerMgtKey=response.invoicerMgtKey,
                invoicerPrintYN=response.invoicerPrintYN,
                invoiceeCorpName=response.invoiceeCorpName,
                invoiceeMgtKey=response.invoiceeMgtKey,
                invoiceePrintYN=response.invoiceePrintYN,
                closeDownState=response.closeDownState,
                closeDownStateDate=response.closeDownStateDate,
                trusteeCorpName=response.trusteeCorpName,
                trusteeCorpNum=response.trusteeCorpNum,
                trusteeMgtKey=response.trusteeMgtKey,
                trusteePrintYN=response.trusteePrintYN,
            )
        )
    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getPopUpURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getPopUpURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getViewURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getViewURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getPrintURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getPrintURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getOldPrintURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getOldPrintURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getEPrintURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getEPrintURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getMailURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getMailURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


@app.post("/getPDFURL")
async def _(request: Request,
            MgtKey: str = Form(...), ):
    try:
        corp_num = INVOICER_CORP_NUM
        mgt_key_type = MGT_KEY_TYPE
        mgt_key = MgtKey

        response = taxinvoiceService.getPDFURL(
            CorpNum=corp_num,  # 팝빌회원 사업자번호 (하이픈 '-' 제외 10자리)
            MgtKeyType=mgt_key_type,  # 세금계산서 유형 : "SELL" / "BUY" / "TRUSTEE" 중 택 1 (SELL : 매출  BUY : 매입, TRUSTEE = 위수탁)
            MgtKey=mgt_key,  # 파트너가 할당한 문서번호
        )
        return templates.TemplateResponse(
            name="popup.html",
            context=dict(
                request=request,
                popup_url=response,
            )
        )

    except PopbillException as PE:
        return templates.TemplateResponse(
            name="exception.html",
            context=dict(
                request=request,
                code=PE.code,
                message=PE.message
            )
        )


if __name__ == '__main__':
    os.system("uvicorn main:app --reload")
