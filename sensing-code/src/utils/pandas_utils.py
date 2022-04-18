import pandas as pd
def is_time_delta(x):
    try:
        pd.Timedelta(x)
        return True
    except:
        return False