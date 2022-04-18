from datetime import datetime
import pathlib

__cur_logger_dir = None


def get_cur_logger_dir():

    # global is bad, I know!
    global __cur_logger_dir

    """
    This is to ensure that even if this function
    is called multiple times in a program.
    And the program operates at day boundaries.
    It'll always return the same one it started
    with!
    This is useful if the timezone is different
    from UTC (such as where telescopes are!)
    """
    if __cur_logger_dir is not None:
        return __cur_logger_dir

    logfile_dir = "data/{}".format(
        datetime.now().strftime("%Y%m%d"))

    # may raise error if cannot write directory
    pathlib.Path(logfile_dir).mkdir(parents=True, exist_ok=True)

    __cur_logger_dir = logfile_dir

    return logfile_dir
