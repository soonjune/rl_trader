import pymysql
from library import cf
from library.logging_pack import *


def db_set(date):
    connections = db_conns()

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

def db_conns():
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

def save_state(state):
    conn = pymysql.connect(host=cf.db_ip,
                           port=int(cf.db_port),
                           user=cf.db_id,
                           password=cf.db_passwd,
                           db='saved_states',
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    sql = "insert into states values(NULL,{})".format(','.join(str(v) for v in state))
    try:
        conn.cursor().execute(sql)
        conn.commit()
    except Exception as e:
        logger.warn(e)

def db_connect(db_name):
    conn = pymysql.connect(host=cf.db_ip,
                    port=int(cf.db_port),
                    user=cf.db_id,
                    password=cf.db_passwd,
                    db=db_name,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor)
    return conn

def load_action(conn):
    sql = 'select * from actions ORDER BY id DESC LIMIT 1'
    with conn.cursor() as cursor:
        cursor.execute(sql)
        action = cursor.fetchone()
    return action