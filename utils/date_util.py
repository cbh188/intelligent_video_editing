from datetime import datetime

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise ValueError(f"Invalid time string format: {time_str}. Expected format: yyyy-MM-dd HH:mm:ss") from e
