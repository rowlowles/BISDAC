from tkinter import *
import tkinter as tk
from tkinter import messagebox
from airtable import airtable
import GLOBALs
import webbrowser
from datetime import datetime, timedelta
import time
import os
from datadog import statsd, initialize, api



# The name of the specific subtable in the base. Note, the names must be in all caps even if it is not written that way
# in Airtable. Example: QC-System vs 'QC-SYSTEM'
table_name_qc_syst = 'QC-SYSTEM'
table_name_bisdac = 'QC-BISDAC'
table_name_RTP = 'RTP'
table_name_rev_tests = 'BISD-REV-TESTS'
table_name_unit_list = 'UNIT LIST'

# Create and authorize the API calls for the airtable
at = airtable.Airtable(qc_base_id, api_key)

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
                webbrowser.open("https://airtable.com/tbl8J4EfvCz8Ppdtp/viw0jPydx1VXDeOH5")

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


if __name__ == "__main__":
    tests = [['pH','This is an example error message'],['EC', 'This is another']]
    guiPumpResults(tests, 'PRG2-001-001')
    unit_id_string = "PRG2-000-000"
    e_title = "Test Message"
    e_string = unit_id_string + "  is being tested"
    #api.Event.create(title=e_title, text=e_string, alert_type = 'error')
    for i in range (0,20):
        statsd.increment('bisdac.runs',1)
        #time.sleep(3)

