from library.logging_pack import *
from datetime import date
from PyQt5.QtWidgets import *
from library import db_settings
from library import open_api
from collections import defaultdict

# def save_state(single_multi_data):
#

TR_REQ_TIME_INTERVAL = 0.2

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = open_api.open_api()

    # 잔고 data 가져오기

    balance_data = kiwoom.get_balance()


    #매수 주문
    # 03 시장가 매수
    # 4번째 인자: 1: 신규매수 / 2: 신규매도 / 3:매수취소 / 4:매도취소 / 5: 매수정정 / 6:매도정정
    kiwoom.send_order("send_order_req", "0101", kiwoom.account_number, 1, '012450', int(5), 0, "03", "")
    print("주문 접수")

    #매도 주문
    # 03 : 시장가 매도
    # 2 : 신규매도
    # 0 : price 인데 시장가니까 0으로
    # get_sell_num : 종목 보유 수량
    kiwoom.send_order("send_order_req", "0101", kiwoom.account_number, 2, '005930',
                             10, 0, "03", "")

    today = date.today().strftime("%Y%m%d")
    codes = ['005930', '066570', '012450', '035420', '035720']
    names = ['samsung_elec', 'lg_elec', 'hanwha_aero', 'naver', 'kakao']
    current_prices = [None, None, None, None, None]

    # save_state(balance_data)


    conns = db_settings.db_set(today)

    # opt10080 TR 요청 - 30초 단위 가격 가져오기(가장 최근으로)
    for code, name in zip(codes, names):
        i = 0
        data = defaultdict(list)
        ret = kiwoom.get_one_day_option_data(code, today)
        # for i in range(899, -1, -1): # for previous day
        current_prices[i] = (ret['close'][0])
        i += 1
        sql = f"insert into `{ret.index[0][:-6]}` \
         values ({ret.index[0]}, {ret['open'][0]}, {ret['high'][0]}, {ret['low'][0]}, {ret['close'][0]}, {ret['volume'][0]})"
        try:
            conns[name].cursor().execute(sql)
            conns[name].commit()
        except Exception as e:
            logger.warn(e)
        else:
            continue

    # 거래하기






    # while kiwoom.remained_data == True:
    #     time.sleep(TR_REQ_TIME_INTERVAL)
    #     kiwoom.set_input_value("종목코드", "039490")
    #     kiwoom.set_input_value("기준일자", "20170224")
    #     kiwoom.set_input_value("수정주가구분", 1)
    #     kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

