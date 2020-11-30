from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from pandas import DataFrame
from collections import defaultdict
from library.logging_pack import *
from library import cf
import sys

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.mod_gubun = 1 # 모의 투자

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
            self.OnEventConnect.connect(self._event_connect)
            self.OnReceiveTrData.connect(self._receive_tr_data)
            self.OnReceiveMsg.connect(self._receive_msg)
            # 주문체결 시점에서 키움증권 서버가 발생시키는 OnReceiveChejanData 이벤트를 처리하는 메서드
            self.OnReceiveChejanData.connect(self._receive_chejan_data)


        except Exception as e:
            is_64bits = sys.maxsize > 2**32
            if is_64bits:
                logger.critical('현재 Anaconda는 64bit 환경입니다. 32bit 환경으로 실행하여 주시기 바랍니다.')
            else:
                logger.critical(e)

    def _create_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)

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
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opt10080_req":
            self._opt10080(rqname, trcode)
        elif rqname == "opw00001_req":
            # logger.debug("opw00001_req!!!")
            # logger.debug("Get deposit!!!")
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            # logger.debug("opw00018_req!!!")
            # logger.debug("Get the possessed item !!!!")
            self._opw00018(rqname, trcode)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10080(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
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

    # openapi 매수 요청
    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        logger.debug("send_order!!!")
        try:
            self.exit_check()
            self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                             [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        except Exception as e:
            logger.critical(e)

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