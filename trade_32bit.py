from library.logging_pack import *
from datetime import date
from datetime import datetime
from PyQt5.QtWidgets import *
from library import db_settings
from library import open_api
from collections import defaultdict

def load_previous_day_data(kiwoom, date):
    kiwoom.data_collect = True
    conns = db_settings.db_conns()
    codes = ['005930', '066570', '012450', '035420', '035720']
    names = ['samsung_elec', 'lg_elec', 'hanwha_aero', 'naver', 'kakao']
    for code, name in zip(codes, names):
        data = defaultdict(list)
        ret = kiwoom.get_one_day_option_data(code, date)
        # for i in range(899, -1, -1): # for previous day
        for i in range(899, -1, -1):
            sql = f"insert into `{ret.index[i][:-6]}` \
                   values ({ret.index[i]}, {ret['open'][i]}, {ret['high'][i]}, {ret['low'][i]}, {ret['close'][i]}, {ret['volume'][i]})"
            try:
                conns[name].cursor().execute(sql)
                conns[name].commit()
            except Exception as e:
                logger.warn(e)
            else:
                continue

TR_REQ_TIME_INTERVAL = 0.2

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = open_api.Kiwoom()
    kiwoom.comm_connect()
    kiwoom.account_info()


    today = date.today().strftime("%Y%m%d")
    codes = ['005930', '066570', '012450', '035420', '035720']
    names = ['samsung_elec', 'lg_elec', 'hanwha_aero', 'naver', 'kakao']
    current_prices = [None, None, None, None, None]


    conns = db_settings.db_set(today)
    # day data collecting
    # load_previous_day_data(kiwoom, today)
    action_conn = db_settings.db_connect('rl_actions')
    prev_action = False

    while(datetime.now().strftime("%H:%M:%S") <= "15:30:00"):
        # opt10080 TR 요청 - 30초 단위 가격 가져오기(가장 최근으로)
        i = 0 # fill up current_prices
        for code, name in zip(codes, names):
            data = defaultdict(list)
            ret = kiwoom.get_one_day_option_data(code, today)
            if ret.empty:
                break
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

        # 잔고 data 가져오기
        balance_data = kiwoom.get_balance()
        stocks_owned = [0, 0, 0, 0, 0]
        for stock in balance_data['multi']:
            if stock[0] == '삼성전자':
                stocks_owned[0] = stock[1]
            elif stock[0] == 'LG전자':
                stocks_owned[1] = stock[1]
            elif stock[0] == '한화에어로스페이스':
                stocks_owned[2] = stock[1]
            elif stock[0] == 'NAVER':
                stocks_owned[3] = stock[1]
            elif stock[0] == '카카오':
                stocks_owned[4] = stock[1]

        # state 생성
        stocks_owned.extend(current_prices)
        stocks_owned.append(kiwoom.d2_deposit)
        db_settings.save_state(stocks_owned)

        # action 불러오기
        action = db_settings.load_action(action_conn)
        if action == prev_action:
            continue
        else:
            prev_action = action
            actions = list(action.values())[1:]
            buy_count = sum(1 for x in actions if x == 1)
            j = 0 # for indexing current_price
            for code, action in zip(codes, actions):
                # 전량 매도
                if action == 0:
                    # 매도 주문
                    # 03 : 시장가 매도
                    # 2 : 신규매도
                    # 0 : price 인데 시장가니까 0으로
                    # get_sell_num : 종목 보유 수량
                    kiwoom.send_order("send_order_req", "0101", kiwoom.account_number, 2, code,
                                      stocks_owned[j], 0, "03", "")
                    logger.debug(f"sell {names[j]} : {stocks_owned[j]}")
                # n분의 1 구매
                elif action == 2:
                    budget = kiwoom.d2_deposit // buy_count
                    buy_amount = budget // current_prices[j]
                    # 매수 주문
                    # 03 시장가 매수
                    # 4번째 인자: 1: 신규매수 / 2: 신규매도 / 3:매수취소 / 4:매도취소 / 5: 매수정정 / 6:매도정정
                    kiwoom.send_order("send_order_req", "0101", kiwoom.account_number, 1, code, buy_amount, 0, "03", "")
                    logger.debug(f"buy {names[j]} : {buy_amount}")
                else:
                    logger.debug(f"hold {names[j]}")
                j += 1










    # while kiwoom.remained_data == True:
    #     time.sleep(TR_REQ_TIME_INTERVAL)
    #     kiwoom.set_input_value("종목코드", "039490")
    #     kiwoom.set_input_value("기준일자", "20170224")
    #     kiwoom.set_input_value("수정주가구분", 1)
    #     kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

