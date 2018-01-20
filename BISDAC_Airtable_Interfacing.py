########################################################################################################################
##                                                                                                                    ##
##                                             THIS IS BISDAC!                                                        ##
##                                                                                                                    ##
########################################################################################################################
# This is where the fun begins.
# This script interfaces with serialCommInterface.py, GLOBALs.py, and firmware loaded on the unit to perform the
# Built-In Self-Diagnostic And Calibration of the unit to check for errors and calibrate the unit.

from airtable import airtable
from tkinter import *
from tkinter import messagebox # Messagebox must be explicitly imported in order to be called
from random import randint
import GLOBALs
import serialCommInterface
import webbrowser
import subprocess
import time
import os
from datadog import initialize, api

# Note: base_id refers to the specific PRG-00002 QC Tracking Rev6 airtable board. If you change boards bases, update it.
# Find the base ID and API key from from this page (must be logged in): https://airtable.com/api
api_key = 'api_key'
qc_base_id = 'base_id'

# The name of the specific subtable in the base. Note, the names must be in all caps even if it is not written that way
# in Airtable. Example: QC-System (https://airtable.com/tbl8sRTs6d8Qsaw55/viw02CNq8CuFgZ7jL) vs 'QC-SYSTEM'
table_name_bisdac = 'BISDAC_RECORDS_TABLE_NAME'
table_name_rev_tests = 'TEST_TABLE_NAME'
table_name_rev_cals = 'CALIBRATION_TABLE_NAME'

# Datadog API initialization
options = {'api_key':'api_key_val', 'app_key':'app_key_val'}
initialize(**options)

# Create and authorize the API calls for the airtable
at = airtable.Airtable(qc_base_id, api_key)


def guiPump(user_Command, button_name):
    """
    Basic premise for the GUI is that the user will "Pump" the software. When the script reaches a point that requires
    user interaction to proceed (such as holding down some buttons on the board), this function will be called in the
    script. The script won't be able to proceed until this function shuts itself down. In essence, this forces the user
    to manually step through the code at certain points, similar to a debugging tool.

    user_Command: a string passed into the function to tell the user what to do.
    button_name: Normally "Next", can be other things as needed.
    :return: Returns and shuts the GUI down until user is needed again
    """

    class Application(Frame):
        def comboFunc(self):
            """
            Open up a confirmation window. The user will now have to confirm they are ready to proceed to the next step
            before the code continues. If the user confirms they are ready to proceed, this shuts down and the script
            resumes. If they are not ready, return to the GUI loop.
            :return:
            """
            if messagebox.askyesno("Confirmation", "Confirm selection?"):
                self.quit()
            else:
                return

        def glossaryBrowser(self):
            # Open the help/tutorial doc to the glossary of parts
            webbrowser.open("URL for glossary doc")

        def helpBrowser(self):
            # Open the help/tutorial doc
            webbrowser.open("URL for help doc")

        def createWidgets(self):
            """
            Main GUI stuff here. Create a label that gives the user a command based on input. Create a button that will
            ask for the user's confirmation before proceeding. Create help button.
            """
            Label(text=user_Command, font = ("Helvetica", 15)).pack()
            user_button = Button(text=button_name, command=self.comboFunc, bd=2, height=2, width = 15, bg="light grey")
            user_button.configure(font=('Helvetica', 15))
            user_button.focus_set()
            user_button.pack()

            help_button = Button(text = "Help", command = self.helpBrowser, bg = "light grey", bd = 2, width = 14)
            help_button.configure(font = ('Helvetica',12))

            help_button.pack()
            glossary_button = Button(text="Glossary of Parts", command=self.glossaryBrowser, bg="light grey", bd=2,
                                     width=14)
            glossary_button.configure(font=('Helvetica', 12))
            glossary_button.pack()


        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.pack()
            self.createWidgets()

    def on_closing():
        # Double check that the user wants to quit the BISDAC. Don't want them to accidentally click X and shut down
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            os._exit(0)

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = Application(master=root)
    root.title("BISDAC")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def guiPumpResults(result_List, unit_name):
    """
    Similar to the other GUI functions, this one was made for the specific case of displaying the results of the test.
    Creates a list of N buttons, where N is the number of failed tests, and when you click on the button a popup
    explaining the cause of the test's failure shows up.
    :param result_List: List of list of results. ex: [["test 1", "Failure reason"], ["test 2", "Failure reason 2"],...]
    :param unit_name: The unit's PRG designator as a string in format "PRG2-00W-XYZ",
    :return:
    """
    class Application(Frame):
        def multiComb(self, name):
            # Display the cause of the failure
            messagebox.showinfo("Cause of " + name[0] + " Failure:", name[1])
            return

        def comboFunc(self):
            if messagebox.askyesno("Confirmation", "Confirm selection?"):
                self.quit()
            else:
                return

        def airtableBrowser(self):
                # Open the airtable of results.
                webbrowser.open("Link to BISDAC Airtable")

        def createWidgets(self):
            """
            Main stuff happens here. Iteratively create buttons using lambda, create "Continue" and "Airtable" buttons
            """

            Label(text=unit_name + " failed the following tests.\nClick on a button to see results.\nResults are also "
                                   "stored online, in Airtable.\nClick \"Close Results\" to proceed.",
                  font=("Helvetica", 15)).pack()
            for test, result in result_List:
                # Create N buttons, one for each N items in list, and create functions for each
                Button(text=test, command=lambda x=[test, result]: self.multiComb(x), bd=2, height=2, font=
                ('Helvetica, 15'), width=20).pack()

            user_button = Button(text="Close Results", command=self.comboFunc, bd=2, height=2, bg="light grey")
            user_button.configure(font=('Helvetica', 15))
            user_button.pack()

            airtable_button = Button(text="Airtable", command=self.airtableBrowser, bg="light grey", bd=2,
                                     width=14)
            airtable_button.configure(font=('Helvetica', 12))
            airtable_button.pack()

        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.pack()
            self.createWidgets()

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            os._exit(0)

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = Application(master=root)
    root.title("BISDAC")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def guiPumpChoice(user_Command, comm_List):
    """
    Similar to guiPump(), but rather than giving the user single response, it iteratively creates a list of N buttons
    where each button returns a different value. This is used to communicate between the GUI and the firmware, because
    the firmware is expecting specific return values. Because those returns are determined by comm_List, there is no
    need to hardcode any return values in this function.

    user_Command: A string telling the user what to do
    comm_List: A list of strings that are used to create buttons for the user to click. Default size is 1. Whatever
    option the user clicks is then sent back to the Firmware via the GLOBALs file.
    """

    class Application(Frame):

        def multiComb(self, name):
            # Set the GLOBALs variable that the serialCommInterface script will then send back to the firmware.
            if messagebox.askyesno("Confirmation", "Confirm \"" + name + "\" selection?"):
                GLOBALs.multi_choice = name
                self.quit()
            else:
                return

        def helpBrowser(self):
            # Open the help/tutorial doc
            webbrowser.open("Link to help doc")

        def glossaryBrowser(self):
            # Open the help/tutorial doc to the glossary of parts
            webbrowser.open("Link to glossary doc")

        def createWidgets(self):
            """
            Main GUI stuff here. Iteratively create a list of buttons that can be used to send back results to the
            firmware. Also creates links to help and glossary documents.
            """
            Label(text=user_Command, font=("Helvetica", 15)).pack()

            for item in comm_List:
                # Create N buttons, one for each N items in list, and create functions for each
                Button(text=item, command=lambda x=item: self.multiComb(x), bd=2, height=2, font=
                ('Helvetica, 15'), width=20).pack()

            help_button = Button(text="BISDAC Help", command=self.helpBrowser, bg="light grey", bd=2, width=14)
            help_button.configure(font=('Helvetica', 12))
            help_button.pack()

            glossary_button = Button(text="Glossary of Parts", command=self.glossaryBrowser, bg="light grey", bd=2,
                                     width=14)
            glossary_button.configure(font=('Helvetica', 12))
            glossary_button.pack()


        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.pack()
            self.createWidgets()

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            os._exit(1)

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = Application(master=root)
    root.title("BISDAC")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def barcodeScanner(user_command):
    """
    Opens up a window that waits for an input from the user. Barcode sanitization occurs elsewhere, to keep this GUI
    function minimal. The barcode scanner is just a USB device that reads in a value wherever the cursor is focused.
    :param user_command: A string telling the user to scan either PCB or Chassis barcode. May be expanded to more
    barcodes later.
    :return:
    """
    class Application(Frame):
        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.pack()
            self.createWidgets()

        def createWidgets(self):
            label = Label(text = user_command,font = ("Helvetica", 15))
            entry = Entry(textvariable = user_var,font = ("Helvetica", 15), bd = 2)
            entry.focus_set()
            # When barcode is scanned close the GUI and return the value
            entry.bind("<Return>", lambda event: root.destroy())
            instruction = Label(text = "Scan the barcode with the scanner.", font = ("Helvetica", 10))
            label.pack()
            entry.pack()
            instruction.pack()

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            os._exit(0)

    root = Tk()
    user_var = StringVar()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.title("BISDAC")
    app = Application(master=root)
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    value_return = user_var.get()
    return value_return


def waitScreen(message, count):
    """
    At some points, the user will need to wait while "stuff" outside the scripts happen. As an example, the pH probe
    should sit in a solution for ~60 seconds in order to get a mostly accurate reading. When these cases come up, this
    will create a simple loading screen to show the user that something is actually happening and the script is working.

    message: A string that tells the user what is happening. Normally it is just "Processing..."
    count: An integer that tells the script how long it should wait for.
    :return:
    """
    class ExampleApp(Frame):

        def __init__(self, master=None):
            Frame.__init__(self, master)
            GLOBALs.waiting = True
            self.pack()
            self.createWidgets()


        def createWidgets(self):
            Label(self, text=message,font = ("Helvetica", 15)).pack()
            self.label = Label(self, text="", width=68)
            self.label.pack()
            self.remaining = 0
            self.countdown(count)

        def countdown(self, remaining = None):
            #Create a "progress bar" that recursively counts down to 0
            if remaining is not None:
                self.remaining = remaining
            if self.remaining <= 0:
                self.quit()
            else:
                blocks = (count-self.remaining)*"█"
                self.label.configure(text=blocks)
                self.remaining = self.remaining - 1
                self.after(1000, self.countdown)

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            os._exit(1)


    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = ExampleApp(master = root)
    root.title("Testing GUI")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def flash_BISDAC_FW(firmware_Version):
    """
    Call this function to flash firmware to the unit via the USB connection. If the flash fails for some reason (ie,
    is unplugged or user doesn't follow the steps to press the button), then it tries to flash again.

    firmware_Version: int that determines what version of firmware we want to flash to the unit.
    """
    # Refer to DFU Mode from this link: https://docs.particle.io/guide/getting-started/modes/photon/
    bisdac_flashed = False

    # BISDAC.bin is the firmware for the BISDAC, firmware_Heartbeat.bin is for QC-System/heartbeat, firmware_Release is
    # for units going out of the door
    user_facing_names = ["BISDAC", "QC/Heartbeat", "Release"]
    user_facing_colours = ["Solid Orange", "Solid Pink", "Solid Green"]
    firmware = ["/path/to/bisdac/firmware/BISDAC.bin", "/path/to/bisdac/firmware/firmware_Heartbeat.bin",
                "/path/to/bisdac/firmware/firmware_Release.bin"]

    guiPump(user_facing_names[firmware_Version]+" Setup:\nHold down both SETUP and RESET buttons on the motherboard.\n"
            "Release RESET, and keep holding SETUP until the motherboard LED\nstarts flashing yellow. Then release "
                                                "SETUP.", "Next")
    guiPump("Click \"Next\" to upload the " + user_facing_names[firmware_Version] + " firmware to the unit.\n"
            "This may take a few seconds.","Next")


    print ("Beginning process to flash " + user_facing_names[firmware_Version] + " firmware to unit.")

    cmd = ["particle", "flash","--usb",firmware[firmware_Version]]
    while not bisdac_flashed:
        try:
            # flash the firmware via cmd line process. If it fails, triggers except statement
            subprocess.check_output(cmd)
            bisdac_flashed = True
            guiPump("Wait until the motherboard LED is " + user_facing_colours[firmware_Version] + ", then "
                    "click \"Next\".", "Next")
            # Need to wait for the chip to finish rebooting after flash.
            waitScreen("Processing...",15)
            guiPump("Unit has been programmed with\n"+user_facing_names[firmware_Version]+" firmware successfully!",
                    "Next")
        except subprocess.CalledProcessError:
            guiPump("Firmware flash failed!\nHold down both SETUP and RESET buttons.\nRelease RESET, and keep holding "
                    "SETUP until LED\nstarts flashing yellow.", "Next")


def checkConnection(firmware_version):
    """
    Check to see if the particle chip is connected to the computer via USB. Return the particle ID. If the chip is not
    connected, force the user to connect it by locking them in this loop until there is some chip info.

    After confirming that we have a chip connected, this function will also flash the BISDAC testing firmware to the
    unit so that it will be able to run the various tests.

    :return: {'port':port[0],'particle_id':particle_id}
    """
    guiPump("NOTE: You MUST wear gloves when touching the motherboard.\nGloves should be provided at the "
            "station.","Next")
    guiPump("Connect the unit to the computer via the Micro-USB cable.","Next")
    chip_info = serialCommInterface.getBoardInfo()
    while chip_info == None:
        guiPump("No unit detected.\nDouble check the USB connection.", "Next")
        chip_info = serialCommInterface.getBoardInfo()

    # Flash test firmware to the particle chip

    flash_BISDAC_FW(firmware_version)
    waitScreen("Beginning interface setup...", 15)
    chip_info = serialCommInterface.getBoardInfo()

    if not GLOBALs.threadsStarted:
        serialCommInterface.start_Threads()

    return chip_info


def barcodeSanitization(barcode, barcode_type):
    """
    Take in a barcode string, and perform some checks to make sure the user scanned the right barcode. These checks have
    been chosen with the intent that they wont need to be changed in the event that the barcode data is changed (ie, no
    looking for 00 at the beginning of Chassis barcode).

    barcode: String
    type: Int, can be either 1 or 2 (We want to add more barcodes to assembly process, which is why this is not a bool)
    :return: True if barcode is valid, false if not
    """

    if barcode_type == 1:
        # Chassis error checking
        if "POP" in barcode and len(barcode) == 19:
            guiPump("Error detected with Chassis Barcode:\nIncorrect Barcode scanned.\nReturning to previous step. "
                "Please scan Barcode again.", "Next")
            return False

        elif len(barcode) != 25:
            # Chassis barcodes should be 25 characters long
            guiPump("Error detected with Chassis Barcode:\nIncorrect Barcode scanned.\nReturning to previous step. "
                    "Please scan Barcode again.","Next")
            return False

        elif re.search('[a-zA-Z]', barcode):
            # Chassis barcodes should not contain any letter characters
            guiPump("Error detected with Chassis Barcode:\nIncorrect Barcode scanned.\nReturning to previous step. "
                    "Please scan the Barcode again.","Next")
            return False
        #Additional sanitation can be added to here, but that might end up being more dependant on formatting of codes
        return True

    if barcode_type == 2:
        # PCB Error checking
        if len(barcode) != 19:
            # PCB barcodes should be 17 characters long
            guiPump("Error detected with PCB Barcode:\nIncorrect Barcode scanned.\nReturning to previous step. "
                    "Please scan the Barcode again.","Next")
            return False
        elif re.search('[a-zA-NQ-Z]',barcode):
            # PCB Barcode should only contain letters P and O in uppercase
            guiPump("Error detected with PCB Barcode:\nIncorrect Barcode scanned.\nReturning to previous step. "
                    "Please scan the Barcode again.","Next")
            return False
        elif "POP" not in barcode:
            # PCB barcodes should contain POP
            guiPump("Error detected with PCB Barcode:\nIncorrect Barcode scanned.\nReturning to previous"
                    "step. Please scan the Barcode again.", "Next")
            return False
        #We checked the big things off here, so we should be good to return true
        return True


def barcodeValueParser(chip_info):
    """
    The unit has two barcodes: a PCB and Chassis code. These codes contain important info such as the revision number.
    This function has the user scan the barcodes and parse out that relevant data using the knowledge of how the
    barcodes are formatted.
    In addition, this function also creates and populates a row in the Airtable database with the info we found. This
    row will later be filled with the results of the BISDAC when it is completed.

    chip_info: {'port': "Not Important", 'particle_id': "important"}
    :return: A list in format [revision_number, unit_number, prg_number, chassis_serial, pcb_serial, id_number]
    """

    # the id_number is used to update the relevant row in Airtable with the results. An id_number is generated when we
    # create a new row in Airtable's BISDAC table.
    id_number = at.create(table_name_bisdac,{})['id']
    chassis_serial = None
    pcb_serial = None
    # If the values don't exist in the airtable, then hold in this loop until the barcodes are scanned.
    while chassis_serial == None:
        # Prompt the user to scan in the chassis barcodes, then sanitize them to make sure they got the right codes.
        chassis_serial = barcodeScanner("Please scan the chassis barcode.")
        if not barcodeSanitization(chassis_serial,1):
            chassis_serial = None

    while pcb_serial == None:
        # Prompt the user to scan in the pcb barcodes, then sanitize them to make sure they got the right codes.
        pcb_serial = barcodeScanner("Please scan the PCB barcode.")
        if not barcodeSanitization(pcb_serial,2):
            pcb_serial = None

    # Grab the unit number (last 6 digits, with a random int in the middle). Convert to string to remove leading zeroes
    # Unfortunately there isn't a clean regex way of doing this, because of randomized numbers and the lack of
    # any fixed characters (such as "-" or letters) that can be used to determine the position of the string
    unit_number = int(chassis_serial[-6:-4] +chassis_serial[-3:])

    # Get the PRG2 number which determines what the unit name in our system will be
    prg_number = int(chassis_serial[7:10])

    # Grab the pcb revision number and convert to int. This will be used to determine what tests we run.
    revision_number = int(re.search('[\-][0-9]{3,3}[\-]',pcb_serial).group()[1:-1])

    #Update the Airtable using the id_number we generated. Data must be passed to Airtable as a dictionary.
    print("Updating airtable...")
    at.update(table_name_bisdac, id_number, {"Particle I.D.":str(chip_info['particle_id']), "Chassis Serial":
        str(chassis_serial), "PCB Serial": str(pcb_serial)})

    # Return the numbers we generated here in a list
    return [revision_number, unit_number, prg_number, chassis_serial, pcb_serial, id_number]


def sendTest(test_name):
    """
    Send a test to Ryan's firmware, then grab the results from the results_parser. The first element in the list results
    is either True or False. If True, the test passed. Otherwise, something went wrong. Return a list with the test
    results.
    :param test_name: a string for the test currently happening (example: "DHT", "pH Calibration", "UB")
    :return: an array in format [Bool, comment string]. If bool == true, test passed.
    """
    # Push command to firmware. Commands must be in all caps with a new line character at the end.
    concat_cmd = "RUN " + str.upper(test_name)+"\r"
    GLOBALs.queue_GUI2FW.put(concat_cmd)
    # Read in results. results_parser() shouldn't return a value until it completes a test suite, so there shouldn't be
    # any threading issues where `return results` is reached before it is actually completed.
    results = None
    while results == None:
        if GLOBALs.results:
            results = GLOBALs.results
            break
        # These two if statements catch flags set by the serialCommInterface.py script and use them to activate the GUI
        # elements in this thread. If a different thread tries to call a GUI function in this thread, it can cause an
        # asynchronous threading error.
        elif GLOBALs.guiSwitcher == 1:
            # Wait screen flag set/reset block
            waitScreen("Processing...", GLOBALs.guiWaitTime)
            GLOBALs.guiSwitcher = None
            GLOBALs.guiWaitTime = None
            GLOBALs.guiClosed = True
        elif GLOBALs.guiSwitcher == 2:
            # Multi choice GUI flags set/reset block
            guiPumpChoice(GLOBALs.guiUserMessage, GLOBALs.guiCommandList)
            GLOBALs.guiSwitcher = None
            GLOBALs.guiUserMessage = None
            GLOBALs.guiCommandList = None
            GLOBALs.guiClosed = True

    # Set the global results flag back to None so that the next test will be stuck in the above While loop.
    GLOBALs.results = None

    print("\n" + str(results) + "\n")
    return results


def sendCalibration(calibration):
    """
    This is just like the above sendTest function, the only difference being that it sends a different command to the
    firmware. The results are parsed in the same function, and it waits for flags in the same way. This is separate
    because it is easier for this script to deal with the test/calibration difference than it is for the firmware.
    :param calibration: What calibration we are running.
    :return: [Bool, comment string]
    """
    concat_cmd = "SET " + str.upper(calibration) + "\r"
    GLOBALs.queue_GUI2FW.put(concat_cmd)

    results = None
    while results == None:
        if GLOBALs.results:
            results = GLOBALs.results
            break
        # GUI elements should be called from this thread to avoid other threads closing them and throwing an error
        if GLOBALs.guiSwitcher == 1:
            waitScreen("Processing...", GLOBALs.guiWaitTime)
            GLOBALs.guiSwitcher = None
            GLOBALs.guiWaitTime = None
            GLOBALs.guiClosed = True
        elif GLOBALs.guiSwitcher == 2:
            guiPumpChoice(GLOBALs.guiUserMessage,GLOBALs.guiCommandList)
            GLOBALs.guiSwitcher = None
            GLOBALs.guiUserMessage = None
            GLOBALs.guiCommandList = None
            GLOBALs.guiClosed = True

    # Set the global results flag back to None so that the next calibration will be stuck in the above While loop.
    GLOBALs.results = None

    print("\n"+ str(results) + "\n")
    return results


def performBISDAC(test_fields, calibration_list):
    """
    Take in an array of calibrations determined by BISD-Rev-Calibrations table, and send them to FW one by one. When
    the calibrations are complete, test the calibration. Return the results.
    Take in an array of tests determined by the BISD-Rev-Tests table. Each test is then sent to the sendTest, which
    returns the results of the test. Once all tests are done, the function returns the results for all tests.
    :param test_fields: List of tests as strings
    :param calibration_list: List of calibrations as strings
    :return:
    """

    guiPump("Start the calibration of the unit?","Next" )
    print ("BISDAC has begun...")

    # Create a 2D list, one column for test name, the other for the test results
    test_results = [[0] * 2 for i in range(len(test_fields))]
    calibration_results = [[0]*2 for j in range(len(calibration_list)*2)]
    cal_offset = len(calibration_list)

    for calibration in range(len(calibration_list)):
        # Send each calibration to the BISDAC one at a time
        print(calibration_list[calibration] + " has been started.")
        calibration_results[calibration][0] = calibration_list[calibration]
        calibration_results[calibration][1] = sendCalibration(calibration_list[calibration])
        print(calibration_list[calibration] + " has been completed.")
        time.sleep(.2)

        # Strip off the _CAL from the end of the calibration and send what remains as a test so that we can verify
        # the calibration was successful. ie, pH_Cal becomes pH and we then send the command `RUN PH` to the
        # unit to perform pH testing. All calibrations must be written in the format `[calName]_CAL`
        calibration_results[calibration+cal_offset][0] = \
            (calibration_list[calibration][:re.search('[_][cC][aA][lL]',calibration_list[calibration]).start()])
        calibration_results[calibration+cal_offset][1] = sendTest\
            ((calibration_list[calibration][:re.search('[_][cC][aA][lL]',calibration_list[calibration]).start()]))
        time.sleep(.2)

    guiPump("Calibrations complete.\nStart the automatic testing of the unit?", "Next")

    for test in range(len(test_fields)):
        # Send each test to the BISDAC one at a time and get the results back
        print (test_fields[test] + " has been started.")
        test_results[test][0] = test_fields[test]
        test_results[test][1] = sendTest(test_fields[test])
        print (test_fields[test] + " has been completed.")
        time.sleep(.2)

    # The format of test_results is [["Test Name",[Pass/fail,"Comments"]], ["Test Name",[Pass/Fail,"Comments"]],...]
    print ("\n\nTesting completed. Begin result compilation...")
    test_results.extend(calibration_results)

    return test_results


def createTestData(unit_name_ID, test_results):
    """
    Uses the values provided above to assemble a dictionary of the BISDAC test results to be passed to the Airtable API
    fields: The list of fields that have been tested will be associated with a result according to the test result
    test_results is an array w/ format [[testName,[True/False, "Comment"]],...] By default, the comment should be ""
    unit_name: The string with the relevant unit_ID
    test_results: results of the BISDAC tests
    return: A dictionary of the results, to be passed to the Airtable API
    """
    print ("Creating test data package for database...")
    comment_Output = ""
    result_Dictionary = {}
    failed_test_list = []

    for numTest in range(len(test_results)):
        # Add the parameters to the dictionary
        # Take the test name from the test_results array and set the value to True/False
        result_Dictionary[(test_results[numTest][0])] = test_results[numTest][1][0]
        # If the comments are present, append it to the comment_Output
        if test_results[numTest][1][1] != "":
            comment_Output = comment_Output + " " + test_results[numTest][1][1]
            temp_item = [[str(test_results[numTest][0]),str(test_results[numTest][1][1])]]
            failed_test_list.extend(temp_item)

    # Add the comments to the dictionary, if there are any.
    result_Dictionary["Issues/Notes"] = unit_name_ID + ": " + comment_Output
    return [result_Dictionary, failed_test_list]


def getUnitID(unit_Name):
    """
    Create the unit name based on the chassis revision number and unit identifier.
    Input: list containing revision number and unit number
    Output: string of unit name
    """

    num_leading_zeroes = 3 - len(str(unit_Name[2]))
    unit_Name = "PRG2-" + "0" * num_leading_zeroes + str(unit_Name[2]) + "-" + str(unit_Name[1])

    return unit_Name


def createTestFields(rev_number):
    """
    In the BISD-Rev-Tests airtable there are several rows which detail what tests are to be performed on each revision
    of the unit. To add a test to the BISDAC, the user would edit that airtable with a new column. To add a new
    revision of tests, the user would add a new row and check off what tests that are to be done on that revision.
    This function grabs the table and looks to match the rev_number with the appropriate test row which will contain
    the tests to be performed on the unit.

    The benefits of storing the tests this way is that it avoids hardcoding any test values in this script. That way,
    when a new revision is made, all that needs to be done is to add a new row in Airtable. No changes to the code will
    be required, which saves time from having someone edit this and add tests then bugfix those tests, etc.

    :return: a list of tests to be performed in string format
    """
    print("Compiling list of tests to perform...")
    testOptions = at.get(table_name_rev_tests)['records']
    for index in range(len(testOptions)):
        # Match the rev_number to the test row.
        if testOptions[index]['fields']['Rev Name'] == str(rev_number):
            # This creates the list of tests
            key_list = list(testOptions[index]['fields'].keys())
            # Remove the two "non-test" elements from the list.
            non_tests = ['Rev Name', 'Notes']
            for nil in non_tests:
                key_list.remove(nil)
            print("List of tests created!")
            return key_list

    # If we get here then that means the test line is missing from airtable or the rev_number is wrong. If the former
    # is wrong, then an engineer must update the airtable. If the latter is wrong that means either the barcode was
    # somehow entered incorrectly, or the barcode format changed (which means barcodeValueParser needs to be changed)
    # Give the user a popup, then quit out of the BISDAC. This is a big issue.
    guiPump("Serious error: Test row not found in Airtable.\nCheck to make sure barcode is correct,\nand there is a "
            "test line in Airtable.\nContact an engineer to fix this issue.", "Shut Down BISDAC")

    os._exit(1)


def createCalibrationFields(rev_number):
    """
    Similar to the createTestFields function above, this grabs a list of calibrations to perform for the PCB.
    The purpose of this is so that it will take some work off the backend (because it is easier to deal with separating
    tests from calibrations in Python) and to ensure that calibrations occur before testing. Implementation is the same
    for this function as createTestFields.
    :param rev_number:
    :return:
    """

    fullList = at.get(table_name_rev_cals)
    libraryOptions = fullList['records']
    for index in range(len(libraryOptions)):
        if libraryOptions[index]['fields']['Rev Name'] == str(rev_number):
            key_list = list(libraryOptions[index]['fields'].keys())
            # Remove the two "non-test" elements from the list.
            non_tests = ['Rev Name', 'Notes']
            key_list.remove(non_tests[0])
            key_list.remove(non_tests[1])
            return key_list

    guiPump("Serious error: Calibration row not found in Airtable.\nCheck to ensure barcode is correct,and\nthere's a "
            "calibration line in Airtable.\nContact an engineer to fix this issue.", "Shut Down BISDAC")

    os._exit(1)


def bisdacPassFail(test_data, serial_numbers, failed_tests, unit_id_string):
    """
    Takes in the various results from the various functions and check to see if the BISDAC succeeded or failed.
    If the BISDAC passed, it will update a line in the QC-BISDAC table detailing that is passed all steps.

    :param test_data: A dictionary containing all the test results and comments. This will be passed to the API.
    :param serial_numbers: The chassis serial number, the pcb serial number, and the row ID string.
    :param failed_tests: A list containing the tests that failed and why they failed.
    :param unit_id_string: A string containing the unit name
    :return: No returns, this doesn't pass anything back. The work is done here.
    """
    # Flag to check if all Bisdac tests passed
    pass_Fail = True

    if failed_tests:
        pass_Fail = False

    # if pass_Fail is true at this point, the Bisdac passed!
    print (test_data)
    print("\n\n\n")

    try:
        print("Starting update airtable...")
        at.update(table_name_bisdac, serial_numbers[2], test_data)
        print("Updated Airtable")
    except:
        for key, value in test_data.items():
            try:
                at.update(table_name_bisdac, serial_numbers[2], {key: value})
            except:
                guiPump("Error writing " + str(key) + " = " + str(value) + " to the\ndatabase. Note this error and "
                            "contact a software engineer.\nThe rest of the BISDAC will proceed as normal.", "Okay")
    # At this point, the BISDAC essentially is completed. From here on, it is just cleaning up the system and preparing
    # it for the next station in the assembly line
    if pass_Fail:
        # Set the BISD value to true.
        at.update(table_name_bisdac,serial_numbers[2],{"BISD":True})
        # Check if we want to randomly select this unit for a full QC-system test
        qc_sys_rand = randint(1,100)
        # Currently, only 5% of units will be given the full parrot, this value is adjustable
        if qc_sys_rand <=5:
            # Post to Datadog
            api.Event.create(title="Unit Selected for QC-System", text=unit_id_string + " passed the BISDAC and has "
                            "been randomly selected for QC-System.", alert_type="success")
            # BISDAC was randomly selected to go through a QC System test
            guiPump("unit passed BISDAC and was randomly selected to perform the Heartbeat test.\nThe system will "
                    "now prepare the unit for the Heartbeat test.", "Next")
            # Flash QC-System firmware to unit
            guiPump("The system will now begin the process of\n loading the Heartbeat firmware.", "Next")
            flash_BISDAC_FW(1) # Flash Heartbeat firmware
            guiPump("System completed.\nNotify a Quality Technician of the random heartbeat test.\nSend"
                    " the unit to the Heartbeat station for testing.", "Next")

        else:
            # Post to Datadog
            api.Event.create(title="Unit Passed BISDAC", text=unit_id_string + " has passed the BISDAC",
                             alert_type="success")
            # Flash Release firmware to unit because BISDAC passed successfully
            guiPump("unit passed BISDAC!\nThe system will now prepare the unit to be shipped.","Next")
            guiPump("The system will now begin the process of\nloading the Release firmware.", "Next")
            flash_BISDAC_FW(2) # Flash Release firmware to the unit
            guiPump("System completed.\nSend the unit to Packaging.", "Next")

    else:
        # BISDAC failed
        # Post to Datadog
        error_message = unit_id_string + " has failed the BISDAC. Failure points: " + test_data["Issues/Notes"]
        api.Event.create(title="Unit Failed BISDAC", text=error_message, alert_type = "error")
        guiPumpResults(failed_tests,unit_id_string)
        guiPump("unit failed BISDAC.\nThe system will now prepare the unit to be repaired.","Next")
        guiPump("The system will now begin the process of\nloading the QC-Repair firmware.", "Next")
        flash_BISDAC_FW(1) # Flash the QC firmware to unit (same as Heartbeat firmware, does both functions)
        guiPump("System completed.\n Notify a Quality Technician of the failure.\nSend the unit to the "
                "QC-Repair station for repairs.", "Next")

    return


def BISDACLoop():
    """
    This is the BISDACLoop, where almost all the other functions are called. The first thing we do is check to see if
    a unit is actually connected, and if it is, flash the unit with the firmware needed to perform the tests.
    """
    chip_info = checkConnection(0)

    # Second, the user should scan the barcodes on the boards and chassis so that it can grab the unique identifiers
    # for the unit. These include what the unit is, what revision of hardware is used by it, etc. Check the function
    # for more descriptions of what these numbers are.
    # Barcode output = [revision_number, unit_number, prg_number, chassis_serial, pcb_serial, id_number]
    barcode_output = barcodeValueParser(chip_info)

    #Split the barcode output into two subgroups for ease of data handling. This is purely for ease on our side.
    rev_unit_numbers = [barcode_output[0], barcode_output[1],barcode_output[2]]
    chassis_pcb_serial_numbers = [barcode_output[3], barcode_output[4], barcode_output[5]]

    # To make sure the code is not susceptible to errors caused by someone changing something in Airtable without
    # updating this script, the list of tests is created each time the code runs. The list will contain all the tests
    # to be run by the BISDAC for the specific revision number passed in via rev_unit_numbers[0]
    test_list = createTestFields(rev_unit_numbers[0])
    calibration_list = createCalibrationFields(rev_unit_numbers[0])

    # Add the unit to the Unit List table and grab the identifier string that is needed to perform some operation on it.
    unit_ID_String = getUnitID(rev_unit_numbers)

    # Perform the BISDAC using the list of dictionary fields grabbed from above
    bisdac_test_results = performBISDAC(test_list, calibration_list)

    # Create a dictionary of results so that it can be used to update the Airtable
    output = createTestData(unit_ID_String, bisdac_test_results)
    test_data = output[0]
    failed_tests = output[1]

    # Determine whether the BISDAC passed/failed and update the relevant Airtables
    bisdacPassFail(test_data, chassis_pcb_serial_numbers,failed_tests, unit_ID_String)
    # End the threads now that the unit is finished being used
    guiPump("The BISDAC process is now finished!\nSelect the next unit to be tested.\nShutting down BISDAC.",
            "Done")
    # Exit the BISDAC and return to the BISDAC_Launcher loop.
    os._exit(0)


if __name__ == "__main__":
    BISDACLoop()


