# 바로답 계산기 블로그 글 카탈로그

바로답(https://u-jeverse.com) 계산기 소개 글의 작성 순서와 상태를 관리한다.
상태: 대기, 원고, 임시저장, 발행. 글을 쓰면 상태와 파일명을 갱신한다.

## 순위를 정한 기준 (2026-09-25)

실제 네이버 월간 검색수 없이 추정한 순위다. 검색광고 API 키가 생기면 검색수로 다시 정렬한다.
1. 관심도: 대표 검색어의 대중 검색 수요 (최상, 상, 중)
2. 네이버 자체 계산기: 검색 결과에 네이버 계산기가 먼저 뜨는 검색어는 계산만 필요한 사람이 블로그까지 오지 않는다. 조건, 신청, 표처럼 설명이 필요한 주제를 앞에 둔다.
3. 시즌: 신청 기한이나 계절이 있는 계산기는 시즌 2~4주 전에 발행한다. 시즌 표가 순위보다 우선한다.
4. 블로그 궁합: 육아, 배편 독자와 겹치면 기존 글에서 서로 연결할 수 있다.

## 유입 우선순위

| 순위 | 계산기 | 경로 | 대표 검색어 | 관심도 | 네이버 자체 계산기 | 시즌 | 글 각도 | 상태 |
|---|---|---|---|---|---|---|---|---|
| 1 | 연봉 실수령액 계산기 | /tax/net-salary | 연봉 실수령액, 연봉 4000 실수령액 | 최상 | 있음 | 연중 | 연봉별 실수령액 표로 롱테일 검색어를 한 번에 잡기 | 임시저장 baroanswer/20260925-net-salary-calculator.md |
| 2 | 실업급여 계산기 | /work/unemployment-benefit | 실업급여 계산, 실업급여 조건 | 최상 | 없음 | 연중 | 조건과 신청 절차가 주인공, 계산기는 도구 | 임시저장 baroanswer/20260925-unemployment-benefit-calculator.md |
| 3 | 퇴직금 계산기 | /work/severance | 퇴직금 계산기, 퇴직금 계산 | 최상 | 없음 | 연중 | 근속·평균임금 예시, 퇴직소득세까지 연결 | 임시저장 baroanswer/20260925-severance-calculator.md |
| 4 | 근로장려금·자녀장려금 계산기 | /tax/eitc | 근로장려금 자녀장려금 | 최상 | 없음 | 5월, 9월, 기한 후 11월 | 육아 독자와 겹침, 신청 기한 강조 | 원고 (사이트 수정 커밋 e70cd72, 배포 후 임시저장) baroanswer/20260925-eitc-calculator.md |
| 5 | 연말정산 환급금 계산기 | /tax/year-end | 연말정산 환급금 계산 | 최상 | 없음 | 10월 말~2월 | 11월 미리보기 서비스 시기에 맞춰 발행 | 원고 (사이트 수정 커밋 e70cd72, 배포 후 임시저장) baroanswer/20260925-year-end-tax-calculator.md |
| 6 | 주휴수당 계산기 | /work/weekly-holiday-pay | 주휴수당 계산 | 상 | 없음 | 연중 | 아르바이트 대상, 조건 15시간 기준 | 대기 |
| 7 | 연차 발생일수 계산기 | /date/annual-leave | 연차 계산, 연차 발생 | 상 | 없음 | 연중 | 입사 1년 미만과 이후 구분 | 대기 |
| 8 | 연차수당 계산기 | /work/annual-leave-pay | 연차수당 계산 | 상 | 없음 | 연말 | 퇴사·연말 미사용 연차 | 대기 |
| 9 | 국민연금 예상수령액 계산기 | /pension/national | 국민연금 예상수령액 | 상 | 없음 | 연중 | 중장년 홈판 반응 좋음 | 대기 |
| 10 | 부동산 중개보수 계산기 | /estate/brokerage-fee | 부동산 복비 계산, 중개수수료 | 상 | 없음 | 이사철 3월 9월 | 이사 시즌 발행 | 대기 |
| 11 | 주택청약 가점 계산기 | /estate/subscription-score | 청약 가점 계산 | 상 | 없음 | 분양 시즌 | 가점표 항목별 설명 | 대기 |
| 12 | 해외직구 관세·부가세 계산기 | /tax/customs | 해외직구 관세 계산 | 상 | 없음 | 11월 블랙프라이데이 | 면세 한도 150달러 200달러 구분 | 대기 |
| 13 | 자동차세 계산기 | /auto/car-tax | 자동차세 연납 할인 | 상 | 없음 | 12월 말~1월 | 연납 할인율과 신청 기간 | 대기 |
| 14 | 출산 예정일 계산기 | /health/due-date | 출산 예정일 계산 | 상 | 있음 | 연중 | 육아 독자와 겹침, 임신 주수표 | 대기 |
| 15 | 배란일·가임기 계산기 | /health/ovulation | 배란일 계산기 | 상 | 있음 | 연중 | 임신 준비, 건강 정보라 공식 근거 필수 | 대기 |
| 16 | 아기 개월수·백일·돌 계산기 | /date/baby-days | 아기 개월수 계산, 백일 계산 | 상 | 없음 | 연중 | 육아 독자와 겹침, 백일 돌 준비 | 대기 |
| 17 | 육아휴직급여 계산기 | /work/parental-leave | 육아휴직급여 계산 | 상 | 없음 | 연중 | 완료 | 임시저장 |
| 18 | 종합소득세 계산기 | /tax/income-tax | 종합소득세 계산 | 상 | 없음 | 5월 | 4월 말 발행 | 대기 |
| 19 | 시급·월급 변환기 | /work/wage | 시급 월급 계산, 최저임금 월급 | 상 | 있음 | 8월 최저임금 결정 후 | 2027 최저임금 월급 환산 | 대기 |
| 20 | 4대보험 계산기 | /tax/insurance | 4대보험 계산 | 상 | 없음 | 연중 | 근로자 부담분과 회사 부담분 | 대기 |
| 21 | 전기요금 계산기 | /life/electricity-bill | 전기요금 계산, 누진세 | 상 | 없음 | 7~8월, 12~1월 | 누진 구간표 | 대기 |
| 22 | 취득세 계산기 | /estate/acquisition-tax | 취득세 계산 | 상 | 없음 | 연중 | 생애최초 감면 | 대기 |
| 23 | 전월세 전환율 계산기 | /estate/rent-convert | 전월세 전환율 계산 | 중 | 없음 | 이사철 | 전세에서 월세 전환 예시 | 대기 |
| 24 | DSR·DTI·LTV 계산기 | /estate/dsr-ltv-dti | DSR 계산기 | 중 | 없음 | 규제 바뀔 때 | 대출 규제 뉴스 직후 발행 | 대기 |
| 25 | 증여세 계산기 | /tax/gift-tax | 증여세 계산, 결혼 증여 | 중 | 없음 | 연중 | 혼인 출산 증여공제 1억 | 대기 |
| 26 | 부동산 양도소득세 계산기 | /tax/real-estate-capital-gains-tax | 양도소득세 계산 | 중 | 없음 | 연중 | 1주택 비과세 조건 | 대기 |
| 27 | 로또 당첨금 세금 계산기 | /tax/lottery | 로또 당첨금 세금 | 중 | 없음 | 연중 | 홈판용, 1등 실수령액 | 대기 |
| 28 | 내 연봉은 상위 몇 %? | /rank/salary | 내 연봉 상위 몇 퍼센트 | 중 | 없음 | 연중 | 홈판용 궁금증형 | 대기 |
| 29 | 내 순자산은 상위 몇 %? | /rank/net-worth | 순자산 상위 몇 퍼센트 | 중 | 없음 | 연중 | 홈판용 궁금증형 | 대기 |
| 30 | 주식 평단가 계산기 | /stock/average-price | 주식 평단가 계산 | 중 | 없음 | 연중 | 물타기 계산기와 묶어서 | 대기 |
| 31 | 고속도로 통행료·유류비 계산기 | /auto/toll | 고속도로 통행료 유류비 | 중 | 없음 | 명절 휴가철 | 배편 글과 서로 연결 | 대기 |
| 32 | 통상임금·평균임금 계산기 | /work/ordinary-wage | 통상임금 계산 | 중 | 없음 | 연중 | 육아휴직 퇴직금 글과 연결 | 대기 |
| 33 | 출산전후휴가급여 계산기 | /work/maternity-leave | 출산휴가급여 | 중 | 없음 | 연중 | 미숙아 선택지 추가 후 작성 | 대기 |
| 34 | 분유량 계산기 | /health/baby-feeding | 분유량 계산 | 중 | 없음 | 연중 | 육아 독자와 겹침, 건강 근거 필수 | 대기 |
| 35 | 애드포스트 수익 계산기 | /blog/adpost | 애드포스트 수익 | 중 | 없음 | 연중 | 완료 | 임시저장 |

## 발행 달력 (시즌이 순위보다 우선)

| 발행 시점 | 계산기 | 이유 |
|---|---|---|
| 10월 초 | 퇴직금, 실업급여 | 연중 수요 최상, 시즌 공백기에 먼저 |
| 10월 중순 | 연말정산 환급금 | 11월 국세청 미리보기 전에 검색 선점 |
| 10월 말~11월 초 | 해외직구 관세 | 11월 블랙프라이데이 |
| 11월 | 근로장려금 기한 후 신청, 연차수당 | 기한 후 신청과 연말 미사용 연차 |
| 12월 초 | 전기요금, 자동차세 연납 | 난방철, 1월 연납 신청 |
| 2월 말~3월 | 복비, 전월세 전환율 | 봄 이사철 |
| 4월 말 | 종합소득세, 근로장려금 | 5월 신고와 정기 신청 |
| 6월 말~7월 | 전기요금(냉방) | 여름 누진 |
| 8월 | 시급 월급(새 최저임금) | 이듬해 최저임금 결정 직후 |
| 명절 2주 전 | 고속도로 통행료 유류비 | 배편 글과 함께 |

## 나머지 (순위 외)

| 계산기 | 경로 | 상태 |
|---|---|---|
| 온라인 수익 비교 계산기 | /blog/compare | 대기 |
| 애드센스 수익 계산기 | /blog/adsense | 대기 |
| 유튜브 수익 계산기 | /blog/youtube | 대기 |
| 틱톡·릴스 수익 계산기 | /blog/shorts | 대기 |
| 쿠팡 파트너스 수익 계산기 | /blog/coupang | 대기 |
| 스마트스토어 수수료·마진 계산기 | /blog/smartstore | 대기 |
| 전자책 수익 계산기 | /blog/ebook | 대기 |
| 원고료·체험단 단가 계산기 | /blog/rate | 대기 |
| 프리랜서 3.3% 계산기 | /blog/freelancer | 대기 |
| 블로그 수익 통합 계산기 | /blog/total | 대기 |
| 인스타그램·스레드 협찬 단가 계산기 | /blog/instagram | 대기 |
| 배달 라이더 수익 계산기 | /blog/delivery | 대기 |
| 광고 ROAS·ROI 계산기 | /blog/roas | 대기 |
| 금값 계산기 | /invest/gold | 대기 |
| 복리 계산기 | /invest/compound | 대기 |
| 예금·적금 이자 계산기 | /invest/deposit | 대기 |
| 환율·환전수수료 계산기 | /invest/exchange | 대기 |
| 코인 평단가 계산기 | /invest/coin-average | 대기 |
| 코인 물타기 계산기 | /invest/coin-average-down | 대기 |
| 코인 수익률 계산기 | /invest/coin-profit | 대기 |
| CAGR 연평균 수익률 계산기 | /invest/cagr | 대기 |
| 개인 간 단리 이자 계산기 | /invest/simple-interest | 대기 |
| 김치프리미엄 계산기 | /invest/kimchi-premium | 대기 |
| 적금 중도해지 이자 계산기 | /invest/early-termination | 대기 |
| ETF·펀드 총보수 비교 계산기 | /invest/etf-cost | 대기 |
| 주식 수익률 계산기 | /stock/profit | 대기 |
| 주식 물타기 계산기 | /stock/average-down | 대기 |
| 목표 평단가 계산기 | /stock/target-average | 대기 |
| 주식 손익분기점 계산기 | /stock/break-even | 대기 |
| 주식 수수료·세금 계산기 | /stock/fee-tax | 대기 |
| 주식 신용거래 계산기 | /stock/credit-trading | 대기 |
| 주식 미수거래 계산기 | /stock/unsettled-trading | 대기 |
| 손절·익절가 계산기 | /stock/stop-take-profit | 대기 |
| 상한가·하한가 계산기 | /stock/limit-up-down | 대기 |
| 해외주식 환율 수익률 계산기 | /stock/overseas-return | 대기 |
| 해외주식 양도소득세 계산기 | /stock/foreign-capital-gains-tax | 대기 |
| 배당수익률·배당금 계산기 | /stock/dividend-yield | 대기 |
| 적정주가 계산기 | /stock/fair-price | 대기 |
| 공모주 청약 계산기 | /stock/ipo | 대기 |
| 유상·무상증자 권리락 계산기 | /stock/rights-offering | 대기 |
| 내 또래 월급 순위 | /rank/peer-salary | 대기 |
| 우리 집 소득은 상위 몇 %? | /rank/household-income | 대기 |
| 금융자산·저축액 순위 | /rank/financial-assets | 대기 |
| 내 부채는 평균보다 많을까? | /rank/debt | 대기 |
| 우리 집 생활비 비교 | /rank/living-cost | 대기 |
| 내 저축률은 상위 몇 %? | /rank/saving-rate | 대기 |
| 내 키는 100명 중 몇 번째? | /rank/height | 대기 |
| 내 수면시간은 충분할까? | /rank/sleep | 대기 |
| 부가세 계산기 | /tax/vat | 대기 |
| 재산세 계산기 | /tax/property-tax | 대기 |
| 상속세 계산기 | /tax/inheritance-tax | 대기 |
| 퇴직소득세 계산기 | /tax/retirement-income-tax | 대기 |
| 근로소득 원천징수 계산기 | /tax/payroll-withholding | 대기 |
| 종합부동산세 계산기 | /tax/comprehensive-property-tax | 대기 |
| 금융소득종합과세 계산기 | /tax/financial-income-tax | 대기 |
| 월세 세액공제 계산기 | /tax/rent-tax-credit | 대기 |
| 주택청약종합저축 소득공제 계산기 | /tax/housing-subscription | 대기 |
| 기타소득 원천징수 계산기 | /tax/other-income | 대기 |
| 이자·배당소득세 계산기 | /tax/interest-income | 대기 |
| 인지세 계산기 | /tax/stamp-duty | 대기 |
| 간이과세자 부가세 계산기 | /business/simplified-vat | 대기 |
| 마진율·판매가 계산기 | /business/margin-price | 대기 |
| 손익분기점 계산기 | /business/break-even | 대기 |
| 카드수수료 계산기 | /business/card-fee | 대기 |
| 인건비 총비용 계산기 | /business/labor-cost | 대기 |
| 배달앱·오픈마켓 수수료 비교 | /business/platform-fee | 대기 |
| 감가상각비 계산기 | /business/depreciation | 대기 |
| 대출 상환 계산기 | /estate/loan | 대기 |
| 평수·평당가 계산기 | /estate/area | 대기 |
| 중도상환수수료 계산기 | /estate/prepayment-fee | 대기 |
| 전세가율·깡통전세 위험 계산기 | /estate/jeonse-ratio | 대기 |
| 임대수익률·갭투자 계산기 | /estate/rental-yield | 대기 |
| 등기비용·법무사 보수 계산기 | /estate/registration-cost | 대기 |
| 임대료 인상 상한 계산기 | /estate/rent-increase | 대기 |
| 건폐율·용적률 계산기 | /estate/floor-area-ratio | 대기 |
| 대환대출 손익 계산기 | /estate/loan-refinance | 대기 |
| 주택 구매력 계산기 | /estate/housing-affordability | 대기 |
| 연장·야간·휴일수당 계산기 | /work/overtime | 대기 |
| 최저임금 위반 판정 계산기 | /work/minimum-wage | 대기 |
| 군인 월급 계산기 | /work/military-pay | 대기 |
| 연봉 인상률 계산기 | /work/raise-rate | 대기 |
| 휴업수당 계산기 | /work/suspension-pay | 대기 |
| 국민연금 조기·연기수령 계산기 | /pension/timing | 대기 |
| 국민연금 추납·임의가입 계산기 | /pension/catch-up | 대기 |
| 국민연금 임의계속가입 계산기 | /pension/voluntary-continue | 대기 |
| 절세계좌 납입 우선순위 계산기 | /pension/account-order | 대기 |
| 부부 합산 연금 계산기 | /pension/couple | 대기 |
| 연금 인출 순서 계산기 | /pension/withdrawal-order | 대기 |
| 연금저축·IRP 세액공제 계산기 | /pension/tax-credit | 대기 |
| 연금소득세 계산기 | /pension/income-tax | 대기 |
| 은퇴 후 건강보험료 계산기 | /pension/health-insurance | 대기 |
| 노후자금 계산기 | /pension/retire-plan | 대기 |
| 은퇴자산 인출 시뮬레이션 | /pension/withdrawal | 대기 |
| 연금 공백기 계산기 | /pension/gap | 대기 |
| 유족연금·장애연금 계산기 | /pension/survivor | 대기 |
| 기초연금 계산기 | /pension/basic | 대기 |
| DC형 퇴직연금·IRP 적립금 계산기 | /pension/dc-irp | 대기 |
| 퍼센트 계산기 | /life/percent | 대기 |
| 단위 변환기 | /life/unit | 대기 |
| 음력·양력 변환기 | /life/lunar | 대기 |
| 에어컨 전기세 계산기 | /life/aircon | 대기 |
| 도시가스 요금 계산기 | /life/gas-bill | 대기 |
| 수도요금 계산기 | /life/water-bill | 대기 |
| 더치페이 계산기 | /life/dutch-pay | 대기 |
| 강아지·고양이 나이 계산기 | /life/pet-age | 대기 |
| 로또 당첨 확률 계산기 | /life/lotto-odds | 대기 |
| 금연 절약금 계산기 | /life/quit-smoking | 대기 |
| 신발 사이즈 변환기 | /life/shoe-size | 대기 |
| 의류 사이즈 변환기 | /life/clothing-size | 대기 |
| 불쾌지수·체감온도 계산기 | /life/weather-index | 대기 |
| 계량 변환·레시피 배율 계산기 | /life/recipe-scale | 대기 |
| 비밀번호 생성기 | /life/password | 대기 |
| 리볼빙 이자 계산기 | /life/revolving | 대기 |
| BMI·정상체중 계산기 | /health/bmi | 대기 |
| 기초대사량 계산기 | /health/bmr | 대기 |
| 하루 칼로리(TDEE) 계산기 | /health/tdee | 대기 |
| 체지방률 계산기 | /health/body-fat | 대기 |
| 수면 시간 계산기 | /health/sleep-cycle | 대기 |
| 달리기 페이스 계산기 | /health/pace | 대기 |
| 운동 칼로리 소모 계산기 | /health/exercise-calorie | 대기 |
| 혈중알코올농도 계산기 | /health/alcohol | 대기 |
| 단백질·물 섭취량 계산기 | /health/nutrient-intake | 대기 |
| 표준체중 계산기 | /health/ideal-weight | 대기 |
| 허리-키 비율 계산기 | /health/waist-height | 대기 |
| 목표 심박수 계산기 | /health/heart-rate | 대기 |
| 만 나이·세는나이 계산기 | /date/age | 대기 |
| 날짜 차이·며칠째 계산기 | /date/date-difference | 대기 |
| 디데이 계산기 | /date/d-day | 대기 |
| 근무일수 계산기 | /date/workdays | 대기 |
| 전역일 계산기 | /date/military-discharge | 대기 |
| 생일·환갑·칠순 계산기 | /date/milestone-birthday | 대기 |
| 시간 더하기·빼기 계산기 | /date/time-calculator | 대기 |
| 근무시간 계산기 | /date/work-hours | 대기 |
| 세계 시각·시차 계산기 | /date/timezone | 대기 |
| 몇 주차 계산기 | /date/week-number | 대기 |
| 택시요금 계산기 | /auto/taxi | 대기 |
| 자동차 취등록세·구매비용 계산기 | /auto/purchase-cost | 대기 |
| 자동차 할부·총구매비용 계산기 | /auto/installment | 대기 |
| 연비·유류비 계산기 | /auto/fuel-cost | 대기 |
| 리스·할부 비교 계산기 | /auto/lease-compare | 대기 |
| 전기차 충전요금 계산기 | /auto/ev-charging | 대기 |
| 과태료·범칙금 계산기 | /auto/fine | 대기 |
| 타이어 사이즈 계산기 | /auto/tire-size | 대기 |
