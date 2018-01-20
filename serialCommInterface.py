import threading
import time
import serial
#import Queue
import sys
import GLOBALs
import serial.tools.list_ports
import re
import BISDAC_Airtable_Interfacing

in_q_mutex = threading.Lock()
out_q_mutex = threading.Lock()

#################################################
##                   Methods                   ##
#################################################

def getBoardInfo():
    """
    Function:
     - Auto detect serial port to the current connected device
     - Take Particle ID if can
    Todo:
     - Right now, it can only detect the first device plugged in.

    # quick test:
    boardInfo = getBoardInfo()
    if boardInfo != None:
        print boardInfo
    else:
        print "No Particle Device Detected!!"
    """
    for port in list(serial.tools.list_ports.comports()):
        if port[1].startswith('P1'):
            #print(port[2])
            dev_info = port[2]
            id_pos = dev_info.find("SNR=")
            particle_id = dev_info[id_pos+4:]
            establish_serial_interface(port[0])
            return {'port':port[0],'particle_id':particle_id}
    return None



def getQueueIOStatus():
    """
    Return the logic status of both of the queues.
    0 = empty; 1 = not empty

    queue_GUI2FW    queue_FW2GUI    return val
        0               0               1
        0               1               2
        1               0               3
        1               1               4
    ret = 1: ready to call GUI_Producer()
    ret = 2: wait for GUI to process test results
    ret = 3: ready to push command to the FW
    ret = 4: Error(Write before Read)
    """
    if (GLOBALs.queue_GUI2FW.empty() and GLOBALs.queue_FW2GUI.empty()):
        return 1
    elif (GLOBALs.queue_GUI2FW.empty() and not GLOBALs.queue_FW2GUI.empty()):
        return 2
    elif (not GLOBALs.queue_GUI2FW.empty() and GLOBALs.queue_FW2GUI.empty()):
        return 3
    elif (not GLOBALs.queue_GUI2FW.empty() and not GLOBALs.queue_FW2GUI.empty()):
        return 4
    else:
        return 0



def GUI_Producer(cmd):
    """
    Function:
     - Put a test command into the outgoing queue.
     - called by GUI widgets' listeners @Robbie
    """
    GLOBALs.queue_GUI2FW.put(cmd)
    if(GLOBALs.queue_GUI2FW.full()):
        return True
    else:
        return False


def establish_serial_interface(pt):
    try:
        GLOBALs.curSerialComm = serial.Serial(
            #port='/dev/ttyACM0',
            #port='/dev/ttyACM1',
            #port='/dev/ttyUSB0',
            port = pt,
            baudrate = 9600,
            parity = serial.PARITY_ODD,
            stopbits = serial.STOPBITS_TWO,
            bytesize = serial.SEVENBITS
        )
        if GLOBALs.curSerialComm.isOpen():
            ret = True
        else:
            ret = False
    except serial.serialutil.SerialException:
        print ("Please plug in USB!")
        GLOBALs.detected_chip = False
        ret = False
        pass

    return ret


def kill_serial_interface():
    GLOBALs.curSerialComm.close()


#################################################
##               GUI to FW Thread              ##
#################################################



class BISDAC_GUI2FW_Thread (threading.Thread):
    """
    BISDAC_GUI2FW_Thread class is in charge of serial communication
    from GUI to the BISDAC Firmware.
    """
    def __init__(self, threadID, name, q_s2f):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q_s2f = q_s2f
    def run(self):
        # print (self.name + " is waiting for OUTGOING commands...")
        s2f_server(self.name,self.q_s2f)
        print ("Exiting " + self.name)

def s2f_server(threadName,q_s2f):
    while True: # the next line of "print Exiting..." is NOT a part of the while!!! 
        if GLOBALs.exitFlag:
            threadName.exit() # the next line of "print Exiting..." gets to execute at last!!!
        s2f_service(q_s2f)


def s2f_service(q):
    """
    This thread service also acts as the master of both of the I/O threads.
    That is to say, it has to monitor the status of both of the I/O queues.
    """
    if (getQueueIOStatus() == 1 or getQueueIOStatus() == 2):
        pass
    elif (getQueueIOStatus() == 3):
        push_cmd_to_fw(q.get())
    elif (getQueueIOStatus() == 4):
        reject_cmd_to_fw(q.get())


def push_cmd_to_fw(cmd):
    """
    Flush input and output, then push the command to the firmware
    """

    GLOBALs.curSerialComm.flushInput()
    GLOBALs.curSerialComm.flushOutput()
    cmd += "\r"
    print ("Command: " + cmd)
    # Self explanatory: send the "cmd" to the firmware
    GLOBALs.curSerialComm.write(cmd.encode())


def reject_cmd_to_fw(cmd):
    """
    Write to FW before Reading is finished.
    InternalError = 1

    GUI must sink this flag after dealing with it.
    """
    InternalError = 1

#################################################
##               FW to GUI Thread              ##
#################################################


class BISDAC_FW2GUI_Thread (threading.Thread):
    """
    BISDAC_FW2GUI_Thread class is in charge of serial communication
    from the BISDAC Firmware to the GUI.
    """
    def __init__(self, threadID, name, q_f2s):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q_f2s = q_f2s
    def run(self):
        # print (self.name + " is waiting for INCOMING feedbacks...")
        f2s_server(self.name,self.q_f2s)
        print ("Exiting " + self.name)

def f2s_server(threadName,q_f2s):
    while True: # the next line of "print Exiting..." is NOT a part of the while!!! 
        if GLOBALs.exitFlag:
            threadName.exit() # the next line of "print Exiting..." gets to execute at last!!!
        f2s_service(q_f2s)


def f2s_service(q):
    """
    This is the Producer to the GUI.
    It keeps reading data from the FW, no logic analysis included.
    """
    try:
        line = GLOBALs.curSerialComm.readline()
    except:
        # If we fail to pull data, that means the connection was interrupted. Let's see if we can fix the issue.
        chip_info = getBoardInfo()
        # Start a wait screen to see if the problem was temporary
        print ("Serious error! Trying to fix...")
        GLOBALs.guiWaitTime = 10
        GLOBALs.guiSwitcher = 1
        while not GLOBALs.guiClosed:  # Holds while guiClosed is false, other thread sets it to True
            pass
        GLOBALs.guiClosed = False
        GLOBALs.guiSwitcher = None
        try:
            connection = establish_serial_interface(chip_info[0])
        except:
            # Normally this would cause an Asynchronous error, but since we are shutting down the script immediately
            # afterwards, this is just fine.
            BISDAC_Airtable_Interfacing.guiPump("An unexpected error has occurred:\n"
                                            "Connection with Unit broken.\nShutting down the script.\nIf the error"
                                            " persists after restarting, contact a software engineer.", "Okay")
            sys.exit(1)
        else:
            line = GLOBALs.curSerialComm.readline()

    if(line == None):
        pass
    else:
        q.put(line)
        #print(q.get())


#################################################
##          Test Results Parsing Thread        ##
#################################################


class Results_Parse_Thread (threading.Thread):
    """
    Results_Parse_Thread is the consumer of the in coming testing results.
    """
    def __init__(self, threadID, name, q_f2s):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q_f2s = q_f2s
    def run(self):
        # print self.name + " is waiting for INCOMING feedbacks..."
        test_results_server(self.name,self.q_f2s)
        print ("Exiting " + self.name)

def test_results_server(threadName,q_f2s):
    while True: # the next line of "print Exiting..." is NOT a part of the while!!! 
        if GLOBALs.exitFlag:
            threadName.exit() # the next line of "print Exiting..." gets to execute at last!!!
        results_parser(q_f2s)

def results_parser(q):
    """
    q is a queue object, where q.get moves to return the next element in the queue. q is filled with the values passed
    from the firmware, and this function parses the stream of data into something that is useful for the GUI.
    Refer to the BISDAC_Device_Comm_Standard.txt file for the command options, along with examples of the communication.
    :param q: a queue object. q.get() returns the next value in the queue
    :return: return a list, first element containing a boolean defining the status of the test, second with comments
    """
    if q.empty():
        pass
    else:
        #Grab the next element in the queue and cast as a string
        res = str(q.get())
        # Remove special character formatting
        res = res[2:res.__len__()-5]
        # Print out the results of res to the terminal so that we have a record if necessary.
        print(res)

        # The following statements should catch all the relevant results sent from Ryan's firmware. The catches we look
        # for are "WAIT", "FAIL", "XXX/YYY", "REQ:", "ERROR:", and "STATUS". The specific usage/use of each catch
        # is listed in the comments of the relevant catch.
        if "WAIT" in res:
        # If the firmware just wants to wait for a bit, this is called
            wait_string = re.search('[(][w][:][0-9]*[0-9][)]', res).group()
            wait_time = int(wait_string[3:-1])
            print ("Waiting for " + str(wait_time) + " seconds.")

            # Set the GUI flags
            GLOBALs.guiWaitTime = wait_time
            GLOBALs.guiSwitcher = 1
            while not GLOBALs.guiClosed: #Holds while guiClosed is false, other thread sets it to True
                pass
            GLOBALs.guiClosed = False
            GLOBALs.guiSwitcher = None
            # End GUI calling

        elif "FAIL" in res:
            # Given the following format for failure:
            #[TEST NAME]
            # FAIL
            #   [FAILURE DESCRIPTION]
            # We will be iterating through res until we hit "FAIL", at which point we will enter this if statement.
            # Then, it will grab the the next element in the queue, which should be the failure description. Add it to
            # the end of a global string (so that it isn't accidentally overwritten for some reason), and then continue.
            res = str(q.get())
            res = res[4:res.__len__() - 5]
            print("Failed test: " + res)
            GLOBALs.queue_result_comments += (res + ". ")

        elif re.search('[0-9]*[0-9][/][0-9]*[0-9]', res):
        # Given the format `XXX/YYY PASSED` in the queue, check is XXX == YYY
            print("Found result line: " + res)
            result = re.search('[0-9]*[0-9][/][0-9]*[0-9]', res).group()
            result = result.split("/")
            if int(result[0] == result[1]):

                # If XXX == YYY, then everything passed and all is good. Return pass and continue with the BISDAC
                # Return "Pass" to the autoTest/manualTest in BISDAC_Airtable_Interfacing
                print("Passed tests: " + res)
                GLOBALs.results = [True, ""]
            else:
                # If XXX != YYY, then some tests failed and GLOBALs.queue_results_comments should not == "".
                # Load the comments of the failed tests into a temp string, reset the global, and return the failure
                # flag along with the comments about the failed test.
                print ("Failed tests: " + res)
                temp_comment_storage = GLOBALs.queue_result_comments
                GLOBALs.queue_result_comments = ""
                GLOBALs.results = [False, temp_comment_storage]

        elif "REQ:" in res:
            # We've reached a test line!
            # Given format `REQ: Some Command [some/options](w:SomeInt)
            print("Request line: " + res)
            # Find the `(w:someInt)` section of the command, and take the int from there
            # if there is no wait, this is (w:0)
            wait_string = re.search('[(][w][:][0-9]*[0-9][)]',res).group()
            wait_time=int(wait_string[3:-1])

            #Find the options in the square brackets and break them into a list of commands
            option_string = re.search(r'\[(.*)\]',res).group()[1:-1]
            com_list = []
            for coms in option_string.split("/"):
                com_list.append(coms)

            #Takes the string between `REQ: ` and `[` and creates a string.
            command = re.search(r'REQ: (.*)',res).group(1)
            end_of_command = re.search('\[',command).start()
            user_command = command[:end_of_command]

            # Create a user window with the list of commands as buttons and the user_command as the message to the user
            # If wait is not zero, start a buffer
            if com_list == []:
                com_list = ["Next"]
            # Call GUI via flags
            GLOBALs.guiCommandList = com_list
            GLOBALs.guiUserMessage = user_command
            GLOBALs.guiSwitcher = 2
            GLOBALs.guiClosed = False
            while not GLOBALs.guiClosed:
                pass
            GLOBALs.guiClosed = False
            GLOBALs.guiSwitcher = None
            # End calling gui Multi Choice via flags
            if wait_time:
                # Set the GUI flags
                GLOBALs.guiWaitTime = wait_time
                GLOBALs.guiSwitcher = 1
                while not GLOBALs.guiClosed:  # Holds while guiClosed is false, other thread sets it to True
                    pass
                GLOBALs.guiClosed = False
                GLOBALs.guiSwitcher = None

            answer = str(GLOBALs.multi_choice).upper() +"\r"
            GLOBALs.multi_choice = None
            time.sleep(.1)
            push_cmd_to_fw(answer)

        elif "ERROR:" in res:
            # We got an error in the calibration process! Note: in this case, the error text is on the same line.
            res = res[6:]
            print ("Failed calibration: " + res)
            GLOBALs.queue_result_comments += (res+ ". ")

        elif "STATUS" in res:
            # STATUS: SUCCESS/ERROR is the return value for calibrations
            if "SUCCESS" in res:
                # Calibration was successful
                GLOBALs.results = [True,""]

            elif "ERROR" in res:
                # Calibration was unsuccessful
                temp_comment_storage = GLOBALs.queue_result_comments
                GLOBALs.queue_result_comments = ""
                GLOBALs.results = [False, temp_comment_storage]
            else:
                print("We got ourselves an error!")
                print(res)
        #Slip back to the beginning of the statement, read in the next line.

#################################################
# establish_serial_interface('/dev/ttyACM2')

# Create new threads
thread_BISDAC_GUI2FW = BISDAC_GUI2FW_Thread(1, "Thread-GUI2FW-OUTGOING", GLOBALs.queue_GUI2FW)
thread_BISDAC_FW2GUI = BISDAC_FW2GUI_Thread(2, "Thread-FW2GUI-INCOMING", GLOBALs.queue_FW2GUI)
thread_Results_Parser = Results_Parse_Thread(3, "Thread-Test-Results-Parser",GLOBALs.queue_FW2GUI)
# Start new Threads: call them after building up the GUI.
def start_Threads():
    thread_BISDAC_GUI2FW.start()
    thread_BISDAC_FW2GUI.start()
    thread_Results_Parser.start()








