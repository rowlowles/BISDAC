import queue


exitFlag = 0                    # one flag to exit both threads
queue_GUI2FW = queue.Queue(1)   # out_q : buffer of info from GUI to FW: size = 1, ie ONLY ONE CMD at a time
queue_FW2GUI = queue.Queue()    # in_q  : buffer of info from FW to GUI
detected_chip = False
curDevPort = ""
curDevParticleID = ""
curSerialComm = None
queue_result_comments = ""
results = None
finished_cal = None
multi_choice = None
switcher = None
guiCommandList = ""
guiUserMessage = ""
guiWaitTime = None
guiSwitcher = None              # 1 = Wait, 2 = multiChoice
guiClosed = False
threadsStarted = False

"""
1 = Write before read error
2 = no dfu device
"""
InternalError = 0
