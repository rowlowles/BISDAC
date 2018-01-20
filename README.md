# README #

### What is the BISDAC and why does it exist? ###

BISDAC stands for **B**uilt-**I**n **S**elf-**D**iagnostic **A**nd **C**alibration and is a process all units will go through before they leave the production line. The BISDAC is intended to use the unit's firmware to test a unit for hardware errors (such as a disconnected sensor), and calibrate both the pH and EC sensors so that the unit is prepared for the customer.

The system was designed to be incredibly simple and uncomplicated to execute, so that a random person picked off the street could come onto the assembly line and be able to perform the BISDAC with no training. This meant no command line interfaces, simple instructions, and a GUI that was incredibly simple and difficult to get confused with. On the backend side, the BISDAC was coded to have an absolute minimum ammount of hardcoding so that adding tests or calibrations to the system requires as little work as possible.

In addition, the BISDAC creates a record of each unit that passes through it in the Airtable Database, including what tests failed, failure cause, etc.

### How does it work? ###

*(This is a short version, refer to the comments in **BISDAC_Airtable_Interfacing.py** for a more detailed walkthrough.)*

The BISDAC process is made of several components: the BISDAC scripts in this repo, a database in Airtable, and the firmware that is loaded onto each unit. The firmware on the unit is what actually performs the tests and calibrations but that firmware is controlled by commands the Python scripts send to it.

At the beginning of the BISDAC process, the user is directed to connect the unit to the computer running the BISDAC via a USB cable. The script will then flash the testing firmware to the unit with the user's help. The script will direct the user to scan in the barcodes located on the unit, which contain characters which identify what revision of hardware the unit is. Different revisions of hardware require different tests. The script will then search the Airtable Database for the list of tests and calibrations to perform.

Unfortunately, not all of the tests can be performed automatically. For example, calibrating the pH and EC sensors requires the pH and EC probe to be placed in control solutions of known pH/EC value. This can't be automated, so when the user's assistance is required a popup window directing the user to perform some action will be displayed.

Once the script has a list of tests and calibrations to perform it will send them to the firmware one at a time and parse the results of each. After the testing and calibration is completed, the script will create a record of the results in Airtable and guide the user to prepare the unit for either repairs (if the unit failed the BISDAC) or packaging (if the unit passed the bISDAC and is now ready to be shipped).

### Other Details ###

The BISDAC was intended to be very scalable and easy to modify. To add/remove a test to the BISDAC an operator only needs to check/uncheck a box in Airtable's web interface (assuming the firmware loaded onto the device is equipped to handle said test). No tests were hardcoded into the script, and nothing is assumed about the layout. A standardized format was developed for communication over the serial interface between the Python scripts and the Firmware so that instructions and results can be easily parsed via Regex.

serialCommInterface.py was mostly written by my coworker, however I did the entire results_parser(q) function, which is why the commenting format differs between those two files.

This repo also includes the skeletons for both the Heartbeat Procedure (an extended test to verify stability of a unit) and the Packaging Procedure (the process for preparing the unit for shipping). However, they were out of scope for the project and are only included here as an sign of things to come.