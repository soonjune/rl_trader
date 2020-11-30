import sys
import logging
from datetime import date
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from library import db_settings

from collections import defaultdict
from pandas import DataFrame
from library.logging_pack import logger

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

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

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10080(self, rqname, trcode):
        # data_cnt = self._get_repeat_cnt(trcode, rqname)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    today = date.today().strftime("%Y%m%d")
    codes = ['005930', '066570', '012450', '035420', '035720']
    names = ['samsung_elec', 'lg_elec', 'hanwha_aero', 'naver', 'kakao']

    conns = db_settings.db_set(today)

    # opt10080 TR 요청 - 30초 단위 가격 가져오기(가장 최근으로)
    for code, name in zip(codes, names):
        data = defaultdict(list)
        ret = kiwoom.get_one_day_option_data(code, today)
        sql = f"insert into `{ret.index[0][:-6]}` \
         values ({ret.index[0]}, {ret['open'][0]}, {ret['high'][0]}, {ret['low'][0]}, {ret['close'][0]}, {ret['volume'][0]})"
        try:
            conns[name].cursor().execute(sql)
            conns[name].commit()
        except Exception:
            logging(f"something wrong with data of {name}")
        else:
            continue

    # 거래하기






    # while kiwoom.remained_data == True:
    #     time.sleep(TR_REQ_TIME_INTERVAL)
    #     kiwoom.set_input_value("종목코드", "039490")
    #     kiwoom.set_input_value("기준일자", "20170224")
    #     kiwoom.set_input_value("수정주가구분", 1)
    #     kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

