must_exit = False
exit_reason = ""

def panic(reason):
    global must_exit
    global exit_reason
    must_exit = True
    exit_reason = reason