import pymysql
from library import cf

def db_set(date):
    connections = db_conn()

    sql = f"create table if not exists `{date}`( \
            date char(14) NOT NULL, \
            open int, \
            high int, \
            low int, \
            close int, \
            volume int, \
            PRIMARY KEY (date) \
            );"

    for conn in connections.values():
        conn.cursor().execute(sql)

    return connections

def db_conn():
    connections = dict()
    connections['samsung_elec'] = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='samsung_elec',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    connections['lg_elec'] = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='lg_elec',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    connections['hanwha_aero'] = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='hanwha_aero',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    connections['naver'] = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='naver',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    connections['kakao'] = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='kakao',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    return connections
