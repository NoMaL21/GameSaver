import datetime

def get_timestamp():
    """현재 시간을 YYMMDD_HHMMSS 형식으로 반환"""
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")
