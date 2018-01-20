import webbrowser
from tkinter import *
from tkinter import messagebox
import os

#TODO: For someone to fill with the appropriate Release code
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
    root.title("Unit Testing GUI")
    app.mainloop()
    root.destroy()


def ReleaseLoop():
    guiPump("The Release section has yet to be completed.\nOpening online Heartbeat tutorial instead.", "Okay")
    webbrowser.open("url_to_instructions")


if __name__ == "__main__":
    ReleaseLoop()