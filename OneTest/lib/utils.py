from datetime import datetime


def format_timestamp(timestamp, date_format='%Y-%m-%d %H:%M:%S'):
    return datetime.fromtimestamp(timestamp).strftime(date_format) if timestamp else None
