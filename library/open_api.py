from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from pandas import DataFrame
from collections import defaultdict
from library.logging_pack import *
from library import cf
import sys
import time
from library.logging_pack import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.mod_gubun = 1 # 모의 투자
        self.rq_count = 0


    def account_info(self):
        logger.debug("account_info 함수에 들어왔습니다!")
        account_number = self.get_login_info("ACCNO")
        self.account_number = account_number.split(';')[0]
        logger.debug("계좌번호 : " + self.account_number)

    def get_login_info(self, tag):
        try:
            ret = self.dynamicCall("GetLoginInfo(QString)", tag)
            # logger.debug(ret)
            return ret
        except Exception as e:
            logger.critical(e)

    def _set_signal_slots(self):
        try:
            # 주문체결 시점에서 키움증권 서버가 발생시키는 OnReceiveChejanData 이벤트를 처리하는 메서드
            self.OnReceiveChejanData.connect(self._receive_chejan_data)
            self.OnEventConnect.connect(self._event_connect)
            self.OnReceiveTrData.connect(self._receive_tr_data)
            self.OnReceiveMsg.connect(self._receive_msg)


        except Exception as e:
            is_64bits = sys.maxsize > 2**32
            if is_64bits:
                logger.critical('현재 Anaconda는 64bit 환경입니다. 32bit 환경으로 실행하여 주시기 바랍니다.')
            else:
                logger.critical(e)

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()

    def _receive_msg(self, sScrNo, sRQName, sTrCode, sMsg):
        logger.debug("_receive_msg 함수에 들어왔습니다!")
        # logger.debug("sScrNo!!!")
        # logger.debug(sScrNo)
        # logger.debug("sRQName!!!")
        # logger.debug(sRQName)
        # logger.debug("sTrCode!!!")
        # logger.debug(sTrCode)
        # logger.debug("sMsg!!!")
        logger.debug(sMsg)


    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def _get_comm_data(self, code, field_name, index, item_name):
        # logger.debug('calling GetCommData...')
        # self.exit_check()
        ret = self.dynamicCall("GetCommData(QString, QString, int, QString", code, field_name, index, item_name)
        return ret.strip()

    def set_input_value(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.dynamicCall("CommRqData(QString, QString, int, QString", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString", code,
                               real_type, field_name, index, item_name)
        return ret.strip()

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # print("screen_no, rqname, trcode", screen_no, rqname, trcode)
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False
        # print("self.py_gubun!!", self.py_gubun)
        if rqname == "opt10081_req" and self.py_gubun == "trader":
            # logger.debug("opt10081_req trader!!!")
            # logger.debug("Get an item info !!!!")
            self._opt10081(rqname, trcode)
        elif rqname == "opt10081_req" and self.py_gubun == "collector":
            # logger.debug("opt10081_req collector!!!")
            # logger.debug("Get an item info !!!!")
            self.collector_opt10081(rqname, trcode)
        elif rqname == "opw00001_req":
            # logger.debug("opw00001_req!!!")
            # logger.debug("Get an de_deposit!!!")
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            # logger.debug("opw00018_req!!!")
            # logger.debug("Get the possessed item !!!!")
            self._opw00018(rqname, trcode)
        elif rqname == "opt10074_req":
            # logger.debug("opt10074_req!!!")
            # logger.debug("Get the profit")
            self._opt10074(rqname, trcode)
        elif rqname == "opw00015_req":
            # logger.debug("opw00015_req!!!")
            # logger.debug("deal list!!!!")
            self._opw00015(rqname, trcode)
        elif rqname == "opt10076_req":
            # logger.debug("opt10076_req")
            # logger.debug("chegyul list!!!!")
            self._opt10076(rqname, trcode)
        elif rqname == "opt10073_req":
            # logger.debug("opt10073_req")
            # logger.debug("Get today profit !!!!")
            self._opt10073(rqname, trcode)
        elif rqname == "opt10080_req":
            # logger.debug("opt10080_req!!!")
            # logger.debug("Get an de_deposit!!!")
            self._opt10080(rqname, trcode)
        # except Exception as e:
        #     logger.critical(e)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10080(self, rqname, trcode):
        # data_cnt = self._get_repeat_cnt(trcode, rqname) # for previous day
        for i in range(2):
            date = self._get_comm_data(trcode, rqname, i, "체결시간")
            open = self._get_comm_data(trcode, rqname, i, "시가")
            high = self._get_comm_data(trcode, rqname, i, "고가")
            low = self._get_comm_data(trcode, rqname, i, "저가")
            close = self._get_comm_data(trcode, rqname, i, "현재가")
            volume = self._get_comm_data(trcode, rqname, i, "거래량")

            self.ohlcv['date'].append(date[:])
            self.ohlcv['open'].append(abs(int(open)))
            self.ohlcv['high'].append(abs(int(high)))
            self.ohlcv['low'].append(abs(int(low)))
            self.ohlcv['close'].append(abs(int(close)))
            self.ohlcv['volume'].append(int(volume))
            self.ohlcv['sum_volume'].append(int(0))


    # trader가 호출 할때는 collector_opt10081과 다르게 1회만 _get_comm_data 호출 하면 된다.
    def _opt10081(self, rqname, trcode):
        try:
            logger.debug("_opt10081!!!")
            date = self._get_comm_data(trcode, rqname, 0, "일자")
            open = self._get_comm_data(trcode, rqname, 0, "시가")
            high = self._get_comm_data(trcode, rqname, 0, "고가")
            low = self._get_comm_data(trcode, rqname, 0, "저가")
            close = self._get_comm_data(trcode, rqname, 0, "현재가")
            volume = self._get_comm_data(trcode, rqname, 0, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))
        except Exception as e:
            logger.critical(e)

    # 먼저 OnReceiveTrData 이벤트가 발생할 때 수신 데이터를 가져오는 함수인 _opw00001를 open_api 클래스에 추가합니다.
    def _opw00001(self, rqname, trcode):
        logger.debug("_opw00001!!!")
        try:
            self.d2_deposit_before_format = self._get_comm_data(trcode, rqname, 0, "d+2추정예수금")
            self.d2_deposit = self.change_format(self.d2_deposit_before_format)
            logger.debug("예수금!!!!")
            logger.debug(self.d2_deposit_before_format)
        except Exception as e:
            logger.critical(e)

    def _opw00018(self, rqname, trcode):
        # try:
        # 전역변수로 사용하기 위해서 총매입금액은 self로 선언
        # logger.debug(1)

        self.total_purchase_price = self._get_comm_data(trcode, rqname, 0, "총매입금액")
        # logger.debug(2)
        self.total_eval_price = self._get_comm_data(trcode, rqname, 0, "총평가금액")
        # logger.debug(3)
        self.total_eval_profit_loss_price = self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
        # logger.debug(4)
        self.total_earning_rate = self._get_comm_data(trcode, rqname, 0, "총수익률(%)")
        # logger.debug(5)
        self.estimated_deposit = self._get_comm_data(trcode, rqname, 0, "추정예탁자산")
        # logger.debug(6)
        self.change_total_purchase_price = self.change_format(self.total_purchase_price)
        self.change_total_eval_price = self.change_format(self.total_eval_price)
        self.change_total_eval_profit_loss_price = self.change_format(self.total_eval_profit_loss_price)
        self.change_total_earning_rate = self.change_format2(self.total_earning_rate)

        self.change_estimated_deposit = self.change_format(self.estimated_deposit)

        self.balance_data['single'].append(self.change_total_purchase_price)
        self.balance_data['single'].append(self.change_total_eval_price)
        self.balance_data['single'].append(self.change_total_eval_profit_loss_price)
        self.balance_data['single'].append(self.change_total_earning_rate)
        self.balance_data['single'].append(self.change_estimated_deposit)


        # 이번에는 멀티 데이터를 통해 보유 종목별로 평가 잔고 데이터를 얻어와 보겠습니다.
        # 다음 코드를 _opw00018에 추가합니다.
        # 멀티 데이터는 먼저 _get_repeat_cnt 메서드를 호출해 보유 종목의 개수를 얻어옵니다.
        # 그런 다음 해당 개수만큼 반복하면서 각 보유 종목에 대한 상세 데이터를
        # _get_comm_data를 통해 얻어옵니다.
        # 참고로 opw00018 TR을 사용하는 경우 한 번의 TR 요청으로
        # 최대 20개의 보유 종목에 대한 데이터를 얻을 수 있습니다.
        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)

        for i in range(rows):
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._get_comm_data(trcode, rqname, i, "보유수량")
            purchase_price = self._get_comm_data(trcode, rqname, i, "매입가")
            current_price = self._get_comm_data(trcode, rqname, i, "현재가")
            eval_profit_loss_price = self._get_comm_data(trcode, rqname, i, "평가손익")
            earning_rate = self._get_comm_data(trcode, rqname, i, "수익률(%)")
            item_total_purchase = self._get_comm_data(trcode, rqname, i, "매입금액")

            quantity = self.change_format(quantity)
            purchase_price = self.change_format(purchase_price)
            current_price = self.change_format(current_price)
            eval_profit_loss_price = self.change_format(eval_profit_loss_price)
            earning_rate = self.change_format2(earning_rate)
            item_total_purchase = self.change_format(item_total_purchase)

            self.balance_data['multi'].append(
                [name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate,
                 item_total_purchase])


    def change_format(self, data):
        try:
            strip_data = data.lstrip('0')
            if strip_data == '':
                strip_data = '0'

            # format_data = format(int(strip_data), ',d')

            # if data.startswith('-'):
            #     format_data = '-' + format_data
            return int(strip_data)
        except Exception as e:
            logger.critical(e)


    # 수익률에 대한 포맷 변경은 change_format2라는 정적 메서드를 사용합니다.
    #     @staticmethod
    def change_format2(self, data):
        try:
            # 앞에 0 제거
            strip_data = data.lstrip('-0')

            # 이렇게 추가해야 소수점으로 나온다.
            if strip_data == '':
                strip_data = '0'
            else:
                # 여기서 strip_data가 0이거나 " " 되니까 100 나눴을 때 갑자기 동작안함. 에러도 안뜸 그래서 원래는 if 위에 있었는데 else 아래로 내림
                strip_data = str(float(strip_data) / self.mod_gubun)
                if strip_data.startswith('.'):
                    strip_data = '0' + strip_data

                #     strip 하면 -도 사라지나보네 여기서 else 하면 안된다. 바로 위에 소수 읻네 음수 인 경우가 있기 때문
                if data.startswith('-'):
                    strip_data = '-' + strip_data

            return strip_data
        except Exception as e:
            logger.critical(e)

    def get_one_day_option_data(self, code, start):
        self.ohlcv = defaultdict(list)

        self.set_input_value("종목코드", code)

        self.set_input_value("기준일자", start)

        self.set_input_value("수정주가구분", 1)

        self.comm_rq_data("opt10080_req", "opt10080", 0, "0101")

        if self.ohlcv['date'] == '':
            return False

        df = DataFrame(self.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=self.ohlcv['date'])
        return df

    def get_balance(self):
        self.balance_data = {'single': [], 'multi': []}
        # comm_rq_data 호출하기 전에 반드시 set_input_value 해야한다.
        self.set_input_value("계좌번호", self.account_number)
        self.set_input_value("비밀번호입력매체구분", 00);
        # 조회구분 = 1:추정조회, 2: 일반조회
        self.set_input_value("조회구분", 1);

        self.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        self.set_input_value("계좌번호", self.account_number)

        self.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.remained_data:
            # # comm_rq_data 호출하기 전에 반드시 set_input_value 해야한다. 초기화 되기 때문
            self.set_input_value("계좌번호", self.account_number)

            self.comm_rq_data("opw00018_req", "opw00018", 2, "2000")
            # print("self.balance_data: ", self.balance_data)
        return self.balance_data

    def get_d2_deposit(self):
        logger.debug("get_d2_deposit 함수에 들어왔습니다!")
        # 이번에는 예수금 데이터를 얻기 위해 opw00001 TR을 요청하는 코드를 구현해 봅시다. opw00001 TR은 연속적으로 데이터를 요청할 필요가 없으므로 상당히 간단합니다.
        # 비밀번호 입력매체 구분, 조회구분 다 작성해야 된다. 안그러면 0 으로 출력됨
        self.set_input_value("계좌번호", self.account_number)
        # self.set_input_value("")
        self.set_input_value("비밀번호입력매체구분", 00)
        # 조회구분 = 1:추정조회, 2: 일반조회
        self.set_input_value("조회구분", 1)
        self.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        logger.debug("_receive_chejan_data 함수로 들어왔습니다!!!")
        logger.debug("gubun !!! :" + gubun)
        # 체결구분 접수와 체결
        if gubun == "0":
            logger.debug("in 체결 data!!!!!")
            # 주문 번호
            order_num = self.get_chejan_data(9203)
            # logger.debug(order_num)

            # logger.debug("종목명!!!")
            # 현재 체결 진행 중인 코드명을 키움증권으로 부터 가져온다
            # "삼성전자         %) 이런식으로 출력 돼서 아래 change_format3 함수로 부터 변환해줘야함
            code_name_temp = self.get_chejan_data(302)
            # logger.debug("code_name_temp!!!!!!")
            # logger.debug(code_name_temp)
            # 코드명
            code_name = self.change_format3(code_name_temp)
            # logger.debug("code_name!!!")
            # logger.debug(code_name)
            # 종목 코드
            code = self.codename_to_code(code_name)
            # logger.debug("종목명 변환한 코드!!!")
            # logger.debug(code)

            # logger.debug("주문수량!!!")
            # logger.debug(self.get_chejan_data(900))
            # logger.debug("주문가격!!!")
            # logger.debug(self.get_chejan_data(901))

            # logger.debug("미체결수량!!!")
            # 미체결 수량
            chegyul_fail_amount_temp = self.get_chejan_data(902)
            # logger.debug(chegyul_fail_amount_temp)
            # logger.debug("원주문번호!!!")
            # logger.debug(self.get_chejan_data(904))
            # logger.debug("주문구분!!!")
            # order_gubun -> "+매수" or "-매도"
            order_gubun = self.get_chejan_data(905)
            # logger.debug(order_gubun)
            # logger.debug("주문/체결시간!!!")
            # logger.debug(self.get_chejan_data(908))
            # logger.debug("체결번호!!!")
            # logger.debug(self.get_chejan_data(909))
            # logger.debug("체결가!!!")
            # purchase_price=self.get_chejan_data(910)
            # logger.debug(self.get_chejan_data(910))
            # logger.debug("체결량!!!")
            # logger.debug(self.get_chejan_data(911))
            # logger.debug("현재가, 체결가, 실시간종가")
            purchase_price = self.get_chejan_data(10)

            if code != False and code != "" and code != 0 and code != "0":
                # 미체결 수량이 ""가 아닌 경우
                if chegyul_fail_amount_temp != "":
                    logger.debug("일단 체결은 된 경우!")
                    if self.is_all_item_db_check(code) == False:
                        logger.debug("all_item_db에 매수한 종목이 없음 ! 즉 신규 매수하는 종목이다!!!!")
                        if chegyul_fail_amount_temp == "0":
                            logger.debug("완벽히 싹 다 체결됨!!!!!!!!!!!!!!!!!!!!!!!!!")
                            self.db_to_all_item(order_num, code, code_name, 0, purchase_price, 0)
                        else:
                            logger.debug("체결 되었지만 덜 체결 됨!!!!!!!!!!!!!!!!!!")
                            self.db_to_all_item(order_num, code, code_name, 1, purchase_price, 0)

                    elif order_gubun == "+매수":
                        if chegyul_fail_amount_temp != "0" and self.stock_chegyul_check(code) == True:
                            logger.debug("아직 미체결 수량이 남아있다. 매수 진행 중!")
                            pass
                        elif chegyul_fail_amount_temp == "0" and self.stock_chegyul_check(code) == True:
                            logger.debug("미체결 수량이 없다 / 즉, 매수 끝났다!!!!!!!")
                            self.end_invest_count_check(code)
                        elif self.stock_chegyul_check(code) == False:
                            logger.debug("현재 all_item_db에 존재하고 체결 체크가 0인 종목, 재매수 하는 경우!!!!!!!")
                            # self.reinvest_count_check(code)
                        else:
                            pass

                    elif order_gubun == "-매도":
                        if chegyul_fail_amount_temp == "0":
                            logger.debug("all db에 존재하고 전량 매도하는 경우!!!!!")
                            self.sell_final_check(code)
                        else:
                            logger.debug("all db에 존재하고 수량 남겨 놓고 매도하는 경우!!!!!")
                            self.sell_chegyul_fail_check(code)

                    else:
                        logger.debug("order_gubun!!!! " + str(order_gubun))
                        logger.debug("이건 어떤 상황이라고 생각해야함??????????????????????????????")
                else:
                    logger.debug("_receive_chejan_data 에서 code 가 불량은 아닌데 체결된놈이 빈공간이네????????????????????????")
            else:
                logger.debug("_receive_chejan_data 에서 code가 불량이다!!!!!!!!!")

        # 국내주식 잔고전달
        elif gubun == "1":
            logger.debug("잔고데이터!!!!!")
            # logger.debug("item_cnt!!!")
            # logger.debug(item_cnt)
            # logger.debug("fid_list!!!")
            # logger.debug(fid_list)
            # try:
            # logger.debug("주문번호!!!")
            # logger.debug(self.get_chejan_data(9203))
            # logger.debug("종목명!!!")
            # logger.debug(self.get_chejan_data(302))
            # logger.debug("주문수량!!!")
            # logger.debug(self.get_chejan_data(900))
            # logger.debug("주문가격!!!")
            # logger.debug(self.get_chejan_data(901))
            #
            # logger.debug("미체결수량!!!")
            chegyul_fail_amount_temp = self.get_chejan_data(902)
            logger.debug(chegyul_fail_amount_temp)
            # logger.debug("원주문번호!!!")
            # logger.debug(self.get_chejan_data(904))
            # logger.debug("주문구분!!!")
            # logger.debug(self.get_chejan_data(905))
            # logger.debug("주문/체결시간!!!")
            # logger.debug(self.get_chejan_data(908))
            # logger.debug("체결번호!!!")
            # logger.debug(self.get_chejan_data(909))
            # logger.debug("체결가!!!")
            # logger.debug(self.get_chejan_data(910))
            # logger.debug("체결량!!!")
            # logger.debug(self.get_chejan_data(911))
            # logger.debug("현재가, 체결가, 실시간종가")
            # logger.debug(self.get_chejan_data(10))
        else:
            logger.debug(
                "_receive_chejan_data 에서 아무것도 해당 되지않음!")

    #   미체결 정보
    def _opt10076(self, rqname, trcode):
        # try:
        logger.debug("func in !!! _opt10076!!!!!!!!! ")
        chegyul_fail_amount_temp = self._get_comm_data(trcode, rqname, 0, "미체결수량")
        logger.debug("_opt10076 미체결수량!!!")
        logger.debug(chegyul_fail_amount_temp)

        # chegyul_fail_amount_temp 비어있으면 int 변환 불가
        if chegyul_fail_amount_temp != "":
            self.chegyul_fail_amount = int(chegyul_fail_amount_temp)

        else:
            self.chegyul_fail_amount = -1

        if self.chegyul_fail_amount != "":
            self.chegyul_name = self._get_comm_data(trcode, rqname, 0, "종목명")
            logger.debug("_opt10076 종목명!!!")
            logger.debug(self.chegyul_name)

            self.chegyul_guboon = self._get_comm_data(trcode, rqname, 0, "주문구분")
            logger.debug("_opt10076 주문구분!!!")
            logger.debug(self.chegyul_guboon)

            self.chegyul_state = self._get_comm_data(trcode, rqname, 0, "주문상태")
            logger.debug("_opt10076 주문상태!!!")
            logger.debug(self.chegyul_state)


        else:
            logger.debug("오늘 산놈이 아닌데 chegyul_check 가 1이 된 종목이다!")


    # openapi 매수 요청
    def send_order(self, request_name, screen_no, account_no, order_type, code, qty, price, hoga_type, origin_order_no):
        """
        주식 주문 메서드

        send_order() 메소드 실행시,
        OnReceiveMsg, OnReceiveTrData, OnReceiveChejanData 이벤트가 발생한다.
        이 중, 주문에 대한 결과 데이터를 얻기 위해서는 OnReceiveChejanData 이벤트를 통해서 처리한다.
        OnReceiveTrData 이벤트를 통해서는 주문번호를 얻을 수 있는데, 주문후 이 이벤트에서 주문번호가 ''공백으로 전달되면,
        주문접수 실패를 의미한다.

        :param request_name: string - 주문 요청명(사용자 정의)
        :param screen_no: string - 화면번호(4자리)
        :param account_no: string - 계좌번호(10자리)
        :param order_type: int - 주문유형(1: 신규매수, 2: 신규매도, 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정)
        :param code: string - 종목코드
        :param qty: int - 주문수량
        :param price: int - 주문단가
        :param hoga_type: string - 거래구분(00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 그외에는 api 문서참조)
        :param origin_order_no: string - 원주문번호(신규주문에는 공백, 정정및 취소주문시 원주문번호르 입력합니다.)
        """
        if not (isinstance(request_name, str)
                and isinstance(screen_no, str)
                and isinstance(account_no, str)
                and isinstance(order_type, int)
                and isinstance(code, str)
                and isinstance(qty, int)
                and isinstance(price, int)
                and isinstance(hoga_type, str)
                and isinstance(origin_order_no, str)):
            raise ParameterTypeError()

        return_code = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                       [request_name, screen_no, account_no, order_type, code, qty, price, hoga_type,
                                        origin_order_no])

        if return_code != ReturnCode.OP_ERR_NONE:
            raise KiwoomProcessingError("send_order(): " + ReturnCode.CAUSE[return_code])

        self.OnReceiveChejanData.connect(self._receive_chejan_data)

    def GetChejanData(self, nFid):
        cmd = 'GetChejanData("%s")' % nFid
        ret = self.dynamicCall(cmd)
        return ret

    # # 체결 데이터를 가져오는 메서드인 GetChejanData를 사용하는
    # get_chejan_data 메서드
    def get_chejan_data(self, fid):
        # logger.debug("get_chejan_data!!!")
        try:
            self.exit_check()
            ret = self.dynamicCall("GetChejanData(int)", fid)
            return ret
        except Exception as e:
            logger.critical(e)


    def chegyul_check(self, code):
        logger.debug("chegyul_check code!!!")
        logger.debug(code)
        self.set_input_value("종목코드", code)
        # 	조회구분 = 0:전체, 1:종목
        self.set_input_value("조회구분", 1)
        # SetInputValue("조회구분"	,  "입력값 2");
        # 	계좌번호 = 전문 조회할 보유계좌번호
        self.set_input_value("계좌번호", self.account_number)
        # 	비밀번호 = 사용안함(공백)
        # 	SetInputValue("비밀번호"	,  "입력값 5");
        self.comm_rq_data("opt10076_req", "opt10076", 0, "0350")

        if self.chegyul_fail_amount == -2:
            # opt10076_req 로 comm rq data 가는 도중에 receive chejan 걸려서 chegyul_fail_amount를 못가져옴. 이럴 때는 다시 돌려
            # 만약 여기서 두번 돌려서 시간낭비가 심하다고 판단 되는 경우에는 그냥 pass로 해도 상관없을듯 로그찍어봐
            logger.debug(
                "opt10076_req 로 comm rq data 가는 도중에 receive chejan 걸려서 chegyul_fail_amount를 못가져옴. 이럴 때는 다시 돌려")

            self.chegyul_check()
        elif self.chegyul_fail_amount == -1:
            # logger.debug("!!!!!!!!!!!!!!!!!!!!!!!!!!logger.debug _receive_chejan_data 에서 code가 불량이다!!!!!!!!!")
            logger.debug(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!l이게 아마 어제 미체결 인놈들같은데 ! update 한번해줘보자 나중에 안되면 수정 , 이게 아마 이미 체결 된놈인듯 어제 체결 돼서 조회가 안되는거인듯")
            # self.engine_JB.commit()

        elif self.chegyul_fail_amount == 0:
            logger.debug("체결!!!!! 이건 오늘 산놈들에 대해서만 조회가 가능한듯 ")

            # 여기좀 간결하게 바꿔봐
            # 제일 최근 종목하나만 체결정보 업데이트하는거다
            # self.jackbot_db_con.commit()

        else:
            logger.debug("아직 매수 혹은 매도 중인 놈이다 미체결!!!!!!!!!!!!!!!!!!!!!!!!!")
            logger.debug("self.chegyul_fail_amount!!")
            logger.debug(self.chegyul_fail_amount)

    # openapi 조회 카운트를 체크 하고 cf.max_api_call 횟수 만큼 카운트 되면 봇이 꺼지게 하는 함수
    def exit_check(self):
        time.sleep(cf.TR_REQ_TIME_INTERVAL)
        self.rq_count += 1
        # openapi 조회 count 출력 (수정): 항상 출력이 아니라 45, 100으로 나눠질 때만
        if self.rq_count % 45 == 0:
            logger.debug(self.rq_count)
            time.sleep(cf.TR_REQ_TIME_INTERVAL_LONG)
        if self.rq_count % 100 == 0:
            logger.debug(self.rq_count)
            time.sleep(cf.TR_REQ_TIME_INTERVAL_LONG * 2)
        if self.rq_count == cf.max_api_call:
            sys.exit(1)


class ParameterTypeError(Exception):
    """ 파라미터 타입이 일치하지 않을 경우 발생하는 예외 """

    def __init__(self, msg="파라미터 타입이 일치하지 않습니다."):
        self.msg = msg

    def __str__(self):
        return self.msg

class ParameterTypeError(Exception):
    """ 파라미터 타입이 일치하지 않을 경우 발생하는 예외 """

    def __init__(self, msg="파라미터 타입이 일치하지 않습니다."):
        self.msg = msg

    def __str__(self):
        return self.msg


class ParameterValueError(Exception):
    """ 파라미터로 사용할 수 없는 값을 사용할 경우 발생하는 예외 """

    def __init__(self, msg="파라미터로 사용할 수 없는 값 입니다."):
        self.msg = msg

    def __str__(self):
        return self.msg


class KiwoomProcessingError(Exception):
    """ 키움에서 처리실패에 관련된 리턴코드를 받았을 경우 발생하는 예외 """

    def __init__(self, msg="처리 실패"):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg


class KiwoomConnectError(Exception):
    """ 키움서버에 로그인 상태가 아닐 경우 발생하는 예외 """

    def __init__(self, msg="로그인 여부를 확인하십시오"):
        self.msg = msg

    def __str__(self):
        return self.msg


class ReturnCode(object):
    """ 키움 OpenApi+ 함수들이 반환하는 값 """

    OP_ERR_NONE = 0  # 정상처리
    OP_ERR_FAIL = -10  # 실패
    OP_ERR_LOGIN = -100  # 사용자정보교환실패
    OP_ERR_CONNECT = -101  # 서버접속실패
    OP_ERR_VERSION = -102  # 버전처리실패
    OP_ERR_FIREWALL = -103  # 개인방화벽실패
    OP_ERR_MEMORY = -104  # 메모리보호실패
    OP_ERR_INPUT = -105  # 함수입력값오류
    OP_ERR_SOCKET_CLOSED = -106  # 통신연결종료
    OP_ERR_SISE_OVERFLOW = -200  # 시세조회과부하
    OP_ERR_RQ_STRUCT_FAIL = -201  # 전문작성초기화실패
    OP_ERR_RQ_STRING_FAIL = -202  # 전문작성입력값오류
    OP_ERR_NO_DATA = -203  # 데이터없음
    OP_ERR_OVER_MAX_DATA = -204  # 조회가능한종목수초과
    OP_ERR_DATA_RCV_FAIL = -205  # 데이터수신실패
    OP_ERR_OVER_MAX_FID = -206  # 조회가능한FID수초과
    OP_ERR_REAL_CANCEL = -207  # 실시간해제오류
    OP_ERR_ORD_WRONG_INPUT = -300  # 입력값오류
    OP_ERR_ORD_WRONG_ACCTNO = -301  # 계좌비밀번호없음
    OP_ERR_OTHER_ACC_USE = -302  # 타인계좌사용오류
    OP_ERR_MIS_2BILL_EXC = -303  # 주문가격이20억원을초과
    OP_ERR_MIS_5BILL_EXC = -304  # 주문가격이50억원을초과
    OP_ERR_MIS_1PER_EXC = -305  # 주문수량이총발행주수의1%초과오류
    OP_ERR_MIS_3PER_EXC = -306  # 주문수량이총발행주수의3%초과오류
    OP_ERR_SEND_FAIL = -307  # 주문전송실패
    OP_ERR_ORD_OVERFLOW = -308  # 주문전송과부하
    OP_ERR_MIS_300CNT_EXC = -309  # 주문수량300계약초과
    OP_ERR_MIS_500CNT_EXC = -310  # 주문수량500계약초과
    OP_ERR_ORD_WRONG_ACCTINFO = -340  # 계좌정보없음
    OP_ERR_ORD_SYMCODE_EMPTY = -500  # 종목코드없음

    CAUSE = {
        0: '정상처리',
        -10: '실패',
        -100: '사용자정보교환실패',
        -102: '버전처리실패',
        -103: '개인방화벽실패',
        -104: '메모리보호실패',
        -105: '함수입력값오류',
        -106: '통신연결종료',
        -200: '시세조회과부하',
        -201: '전문작성초기화실패',
        -202: '전문작성입력값오류',
        -203: '데이터없음',
        -204: '조회가능한종목수초과',
        -205: '데이터수신실패',
        -206: '조회가능한FID수초과',
        -207: '실시간해제오류',
        -300: '입력값오류',
        -301: '계좌비밀번호없음',
        -302: '타인계좌사용오류',
        -303: '주문가격이20억원을초과',
        -304: '주문가격이50억원을초과',
        -305: '주문수량이총발행주수의1%초과오류',
        -306: '주문수량이총발행주수의3%초과오류',
        -307: '주문전송실패',
        -308: '주문전송과부하',
        -309: '주문수량300계약초과',
        -310: '주문수량500계약초과',
        -340: '계좌정보없음',
        -500: '종목코드없음'
    }


class FidList(object):
    """ receiveChejanData() 이벤트 메서드로 전달되는 FID 목록 """

    CHEJAN = {
        9201: '계좌번호',
        9203: '주문번호',
        9205: '관리자사번',
        9001: '종목코드',
        912: '주문업무분류',
        913: '주문상태',
        302: '종목명',
        900: '주문수량',
        901: '주문가격',
        902: '미체결수량',
        903: '체결누계금액',
        904: '원주문번호',
        905: '주문구분',
        906: '매매구분',
        907: '매도수구분',
        908: '주문/체결시간',
        909: '체결번호',
        910: '체결가',
        911: '체결량',
        10: '현재가',
        27: '(최우선)매도호가',
        28: '(최우선)매수호가',
        914: '단위체결가',
        915: '단위체결량',
        938: '당일매매수수료',
        939: '당일매매세금',
        919: '거부사유',
        920: '화면번호',
        921: '921',
        922: '922',
        923: '923',
        949: '949',
        10010: '10010',
        917: '신용구분',
        916: '대출일',
        930: '보유수량',
        931: '매입단가',
        932: '총매입가',
        933: '주문가능수량',
        945: '당일순매수수량',
        946: '매도/매수구분',
        950: '당일총매도손일',
        951: '예수금',
        307: '기준가',
        8019: '손익율',
        957: '신용금액',
        958: '신용이자',
        959: '담보대출수량',
        924: '924',
        918: '만기일',
        990: '당일실현손익(유가)',
        991: '당일신현손익률(유가)',
        992: '당일실현손익(신용)',
        993: '당일실현손익률(신용)',
        397: '파생상품거래단위',
        305: '상한가',
        306: '하한가'
    }


class RealType(object):
    REALTYPE = {
        '주식시세': {
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '거일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            311: '시가총액(억)'
        },

        '주식체결': {
            20: '체결시간(HHMMSS)',
            10: '체결가',
            11: '전일대비',
            12: '등락율',
            27: '최우선매도호가',
            28: '최우선매수호가',
            15: '체결량',
            13: '누적체결량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비',
            29: '거래대금증감',
            30: '전일거래량대비',
            31: '거래회전율',
            32: '거래비용',
            228: '체결강도',
            311: '시가총액(억)',
            290: '장구분',
            691: 'KO접근도'
        },

        '주식호가잔량': {
            21: '호가시간',
            41: '매도호가1',
            61: '매도호가수량1',
            81: '매도호가직전대비1',
            51: '매수호가1',
            71: '매수호가수량1',
            91: '매수호가직전대비1',
            42: '매도호가2',
            62: '매도호가수량2',
            82: '매도호가직전대비2',
            52: '매수호가2',
            72: '매수호가수량2',
            92: '매수호가직전대비2',
            43: '매도호가3',
            63: '매도호가수량3',
            83: '매도호가직전대비3',
            53: '매수호가3',
            73: '매수호가수량3',
            93: '매수호가직전대비3',
            44: '매도호가4',
            64: '매도호가수량4',
            84: '매도호가직전대비4',
            54: '매수호가4',
            74: '매수호가수량4',
            94: '매수호가직전대비4',
            45: '매도호가5',
            65: '매도호가수량5',
            85: '매도호가직전대비5',
            55: '매수호가5',
            75: '매수호가수량5',
            95: '매수호가직전대비5',
            46: '매도호가6',
            66: '매도호가수량6',
            86: '매도호가직전대비6',
            56: '매수호가6',
            76: '매수호가수량6',
            96: '매수호가직전대비6',
            47: '매도호가7',
            67: '매도호가수량7',
            87: '매도호가직전대비7',
            57: '매수호가7',
            77: '매수호가수량7',
            97: '매수호가직전대비7',
            48: '매도호가8',
            68: '매도호가수량8',
            88: '매도호가직전대비8',
            58: '매수호가8',
            78: '매수호가수량8',
            98: '매수호가직전대비8',
            49: '매도호가9',
            69: '매도호가수량9',
            89: '매도호가직전대비9',
            59: '매수호가9',
            79: '매수호가수량9',
            99: '매수호가직전대비9',
            50: '매도호가10',
            70: '매도호가수량10',
            90: '매도호가직전대비10',
            60: '매수호가10',
            80: '매수호가수량10',
            100: '매수호가직전대비10',
            121: '매도호가총잔량',
            122: '매도호가총잔량직전대비',
            125: '매수호가총잔량',
            126: '매수호가총잔량직전대비',
            23: '예상체결가',
            24: '예상체결수량',
            128: '순매수잔량(총매수잔량-총매도잔량)',
            129: '매수비율',
            138: '순매도잔량(총매도잔량-총매수잔량)',
            139: '매도비율',
            200: '예상체결가전일종가대비',
            201: '예상체결가전일종가대비등락율',
            238: '예상체결가전일종가대비기호',
            291: '예상체결가',
            292: '예상체결량',
            293: '예상체결가전일대비기호',
            294: '예상체결가전일대비',
            295: '예상체결가전일대비등락율',
            13: '누적거래량',
            299: '전일거래량대비예상체결률',
            215: '장운영구분'
        },

        '장시작시간': {
            215: '장운영구분(0:장시작전, 2:장종료전, 3:장시작, 4,8:장종료, 9:장마감)',
            20: '시간(HHMMSS)',
            214: '장시작예상잔여시간'
        },

        '업종지수': {
            20: '체결시간',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            15: '거래량',
            13: '누적거래량',
            14: '누적거래대금',
            16: '시가',
            17: '고가',
            18: '저가',
            25: '전일대비기호',
            26: '전일거래량대비(계약,주)'
        },

        '업종등락': {
            20: '체결시간',
            252: '상승종목수',
            251: '상한종목수',
            253: '보합종목수',
            255: '하락종목수',
            254: '하한종목수',
            13: '누적거래량',
            14: '누적거래대금',
            10: '현재가',
            11: '전일대비',
            12: '등락율',
            256: '거래형성종목수',
            257: '거래형성비율',
            25: '전일대비기호'
        },

        '주문체결': {
            9201: '계좌번호',
            9203: '주문번호',
            9205: '관리자사번',
            9001: '종목코드',
            912: '주문분류(jj:주식주문)',
            913: '주문상태(10:원주문, 11:정정주문, 12:취소주문, 20:주문확인, 21:정정확인, 22:취소확인, 90,92:주문거부)',
            302: '종목명',
            900: '주문수량',
            901: '주문가격',
            902: '미체결수량',
            903: '체결누계금액',
            904: '원주문번호',
            905: '주문구분(+:현금매수, -:현금매도)',
            906: '매매구분(보통, 시장가등)',
            907: '매도수구분(1:매도, 2:매수)',
            908: '체결시간(HHMMSS)',
            909: '체결번호',
            910: '체결가',
            911: '체결량',
            10: '체결가',
            27: '최우선매도호가',
            28: '최우선매수호가',
            914: '단위체결가',
            915: '단위체결량',
            938: '당일매매수수료',
            939: '당일매매세금'
        },

        '잔고': {
            9201: '계좌번호',
            9001: '종목코드',
            302: '종목명',
            10: '현재가',
            930: '보유수량',
            931: '매입단가',
            932: '총매입가',
            933: '주문가능수량',
            945: '당일순매수량',
            946: '매도매수구분',
            950: '당일총매도손익',
            951: '예수금',
            27: '최우선매도호가',
            28: '최우선매수호가',
            307: '기준가',
            8019: '손익율'
        },

        '주식시간외호가': {
            21: '호가시간(HHMMSS)',
            131: '시간외매도호가총잔량',
            132: '시간외매도호가총잔량직전대비',
            135: '시간외매수호가총잔량',
            136: '시간외매수호가총잔량직전대비'
        }
    }
