import subprocess
from tkinter import *
from tkinter import messagebox
import os

switcher = None
BISDAC_cmd = ['python3','/path/to/script/BISDAC_Airtable_Interfacing.py']
Heartbeat_cmd = ['python3', '/path/to/script/Heartbeat_procedure.py']
Release_cmd = ['python3', '/path/to/script/Release_procedure.py']

def guiPump(user_Command, button_name):
    """
    Basic premise for the GUI is that the user will "Pump" the software. When the script reaches a point that requires
    user interaction to proceed (such as physically moving a probe into a solution), this function will be called in the
    script. The script won't be able to proceed until this function shuts itself down. In essence, this forces the user
    to manually step through the code at certain points, similar to a debugging tool.

    user_Command: a string passed into the function to tell the user what to do.
    button_name: Normally "Done", can be other things as needed.
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

        def createWidgets(self):
            """
            Main GUI stuff here. Create a label that gives the user a command based on input. Create a button that will
            ask for the user's confirmation before proceeding. Create help button.
            """
            Label(text=user_Command, font = ("Helvetica", 15)).pack()
            user_button = Button(text=button_name, command=self.comboFunc, bd=2, height=2, bg="light grey")
            user_button.configure(font=('Helvetica', 15))
            user_button.pack()

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
    root.title("Testing GUI")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def startScreen():
    """
    The first GUI screen for the BISDAC. Asks the user if they want to test a unit or quit. Either way, it asks for
    a confirmation and then proceeds with the script. In addition, it also contains quicklinks to the tutorial doc and
    Airtable required for the BISDAC.
    :return:
    """
    class Application(Frame):

        def confirmationStartBISDAC(self):
            # If the user accepts, then this shuts down the window and returns to the rest of the script.
            if messagebox.askyesno("Confirmation", "Confirm you want to start the BISDAC?"):
                global switcher
                switcher = 0
                self.quit()
            else:
                return

        def confirmationStartHeartbeat(self):
            if messagebox.askyesno("Confirmation", "Confirm you want to start the Heartbeat procedure?"):
                global switcher
                switcher = 1
                self.quit()
            else:
                return

        def confirmationStartRelease(self):
            if messagebox.askyesno("Confirmation", "Confirm you want to start the Release procedure?"):
                global switcher
                switcher = 2
                self.quit()
            else:
                return

        def confirmationQuit(self):
            # If the user accepts, then this shuts down the entire script and writes a sys.exit message on the console.
            if messagebox.askyesno("Confirmation", "Confirm you want to quit?"):
                global switcher
                switcher = 3
                self.quit()
            else:
                return

        def createWidgets(self):
            # The design of the start screen buttons. Make a red quit button and green start button, and then add a pair
            # of buttons that open the Google Docs help document or the QC-BISDAC airtable.
            top = Frame(root)
            bottom = Frame(root)
            top.pack(side = TOP)
            bottom.pack(side = BOTTOM, fill = BOTH, expand = True)

            Label(text="Welcome to the BISDAC", font=("Helvetica", 19)).pack(in_=top)

            start_BISDAC_button = Button(text="Start BISDAC", command=self.confirmationStartBISDAC, bd=2, height=2, width=25,
                                  bg="green",font=("Helvetica", 15))


            start_Heartbeat_button = Button(text="Start Heartbeat", command=self.confirmationStartHeartbeat, bd=2, height=2,
                                            width=25, bg="green",font=("Helvetica", 15))

            start_Production_button = Button(text="Production Setup", command=self.confirmationStartRelease, bd=2, height=2,
                                             width=25, bg="green",font=("Helvetica", 15))

            quit_button = Button(text="Quit System", command=self.confirmationQuit, bd=2, height=2, width=25, bg="red")
            quit_button.configure(font=("Helvetica", 15))

            start_BISDAC_button.pack(in_ = top)
            start_Heartbeat_button.pack(in_ = top)
            start_Production_button.pack(in_ = top)
            quit_button.pack(in_ = top)

        def __init__(self, master=None):
            Frame.__init__(self, master)
            self.pack()
            self.createWidgets()


    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            sys.exit("Window closed.")

    root = Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    app = Application(master=root)
    root.title("Unit Testing GUI")
    root.geometry('+%d+%d' % (100, 100))
    app.mainloop()
    root.destroy()


def BisdacLoop():
    subprocess.check_output(BISDAC_cmd)


def HeartbeatLoop():
    subprocess.check_output(Heartbeat_cmd)


def releaseLoop():
    subprocess.check_output(Release_cmd)


def main():
    while True:
        global switcher
        startScreen()
        if switcher == 0:
            try:
                BisdacLoop()
            except:
                guiPump("GUI closed unexpectedly, restarting.","Next")

        if switcher == 1:
            try:
                HeartbeatLoop()
            except:
                guiPump("GUI closed unexpectedly, restarting.", "Next")

        if switcher == 2:
            try:
                releaseLoop()
            except:
                guiPump("GUI closed unexpectedly, restarting.", "Next")

        if switcher == 3:
            break


if __name__ == "__main__":
    main()