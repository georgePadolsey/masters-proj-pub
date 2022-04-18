
def should_start_on_boot():

    try:
        with open("start_on_boot.txt", "r") as f:
            return f.readlines()[0].lower().index("t") != -1
    except:
        return False

def toggle_start_on_boot():

    orig = should_start_on_boot()

    with open("start_on_boot.txt", "w+") as f:
        f.write(str(not orig))
