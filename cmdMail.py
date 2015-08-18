#! /usr/bin/python3

# Reads new emails and performs tasks if certain commands are found

import poplib
import smtplib
import ssl
from urllib.request import urlopen
import time
from datetime import datetime
from subprocess import call
import threading
import traceback

# Constants and Settings
FROM_NAME = "Raspi Notification" # A name for the from email account
PI_NAME = "Raspi:" # A name for the server, this preceeds the subject in every email
USER_NAME = "" # user@gmail.com
PASSWORD = "" # account password
SEND_TO = "" # reciever email
RIP_SCRIPTS = {"Trance": "/home/pi/ripTrance.sh", "Dubbase.FM": "/home/pi/ripDub.sh"} # Genres and script locations for streamripper

# A dictionary that keeps track if a rip is already in progress for that genre
is_rip_locked = {}


# Read new emails from an account for commands
def read_emails():
    done = False
    messages = ""
    while not done:
        try:
            # Connect to gmail and send credentials
            pop_conn = poplib.POP3_SSL("pop.gmail.com")
            pop_conn.user(USER_NAME)
            pop_conn.pass_(PASSWORD)

            # Connect to server and get new emails
            messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]

            # Close server connection and exit the while loop
            pop_conn.quit()
            done = True
        except Exception as e:
        	# In case of errors, wait a minute then try again
            error_message = "No arguments found with exception."
            if e.args[0]:
                error_message = e.args[0]
            log("Read Email Error: " + str(error_message))
            time.sleep(60)
    # End Read Loop

    # Turn the emails into a lower case string
    messages = str(messages).lower()

    # Look for key phrases in the emails
    # Uses multi-threading for tasks to keep things moving asyncronously during long tasks.

    # Reboots the computer
    if "reboot" in messages:
        reboot_pi()

    # Exits cmdMail.py
    if "stop listening" in messages:
        log("No longer listening.")

        # Build and send an email
        sub = PI_NAME + " Not listening"
        msg = "I am no longer listening."
        send_email(sub, msg)

        # Exit the program
        exit(0)

    # Returns the global IP address
    if "home ip" in messages:
        t = threading.Thread(target=send_ip_email)
        t.start()

    # Wakes a computer over LAN using external program wakeonlan, 
    # copy this section and use a different name to allow multiple computers
    if "wake liten" in messages:
        t = threading.Thread(target=wake_on_lan, args=("Liten",))
        t.start()

    # Rips an internet radio stream using external streamripper program
    if "rip trance" in messages:
        genre = "Trance"
        t = threading.Thread(target=rip, args=(genre,))
        t.start()

    # Rips an internet radio stream using external streamripper progam
    if "rip dub" in messages:
        # sleep for 5 seconds to prevent thread overlap with email and log functions when started simultaneously
        time.sleep(5)
        genre = "Dubbase.FM"
        t = threading.Thread(target=rip, args=(genre,))
        t.start()


# Send an email on script start to notify about a reboot
def send_boot_mail():
    # 2 minute delay to allow drivers and internet connection to get going
    time.sleep(120)

    log("Booting up.", True)

    # Build and send the email
    sub = PI_NAME + " Startup complete"
    msg = "I have successfully booted up.\n" + get_home_ip() + "."
    send_email(sub, msg)


# Send an email with the global IP address in it
def send_ip_email():
    log("IP requested.")

    # Build and send the email
    sub = PI_NAME + " Home IP"
    msg = get_home_ip() + "."
    send_email(sub, msg)

# Returns a string with the home global IP
def get_home_ip():
    return "Home IP address: " + str(urlopen("http://ipecho.net/plain").read().decode("utf-8"))

# Wakes a computer up over LAN network
def wake_on_lan(hostname):
    log("Waking Liten.")

    # Try waking Liten 4 times
    for x in range(4):
        call(["wakeonlan", ""])
        print()

    # Build and send the email
    sub = PI_NAME + " WOL " + str(hostname)
    msg = "I have woken " + str(hostname) + "."
    send_email(sub, msg)

    # Try waking Liten another 4 times
    for x in range(4):
        call(["wakeonlan", ""])
        print()


# Starts a new streamripper of dubstep music, the script will send an email when it is done
def rip(genre):
    global is_rip_locked

    # If there is already a stream being downloaded, it will have a true value in this dictionary
    # A new stream will delete and corrupt the current one.
    if is_rip_locked[genre]:
        log(genre + " is locked, aborting rip.")

        # Build and send and email, then exit this function
        sub = PI_NAME + " " + genre + " ripper stream locked"
        msg = "Another process is ripping " + genre + ". So I won't start a new rip."
        send_email(sub, msg)
    else:
    	# The value returned false and so a streamrip can be started
        log("Ripping " + genre + ".")

        # Build and send the email confirming the command
        sub = PI_NAME + " " + genre + " Streamripper started"
        msg = "I have started the " + genre + " stream rip."
        send_email(sub, msg)

        # Lock the genre from being ripped multiple times
        is_rip_locked[genre] = True

        # Start the ripper, the thread will wait here until the rip is finished
        call([RIP_SCRIPTS[genre]])

        # Unlock the genre so it can be ripped again
        is_rip_locked[genre] = False

        log("Finished Ripping " + genre + ".")

        # Build and send the email when the rip is done
        sub = PI_NAME + " " + genre + " Streamripper done"
        msg = "I just wanted to let you know that your " + genre + " stream is saved."
        send_email(sub, msg)


# Reboot the device
def reboot_pi():
    log("Rebooting now.")

    # Build and send the email confirming the command
    sub = PI_NAME + " Rebooting"
    msg = "cmdMail has requested a reboot. I will be back online in a few... hopefully."
    send_email(sub, msg)

    # Wait 15 seconds for the mail to finish sending
    time.sleep(15)
    call(["sudo reboot"])


# Send an email
def send_email(subject, message=" "):
	# Construct the email in single-string format
    eml = "\r\n".join(["From: %s" % FROM_NAME, "To: %s" % SEND_TO, "Subject: %s" % subject, "", message])

    # Keep trying until the email is successfully sent
    sent = False
    while not sent:
        try:
            # Log in and send, magic.
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(USER_NAME, PASSWORD)
            server.sendmail(FROM_NAME, [SEND_TO], eml)
            server.quit()
            # Sent ends the loop
            sent = True
        except smtplib.SMTPException as e:
        	# In case of errors, wait a minute and then resend
        	# Subject can help identify what function tried to send the email
            log("Send Email Error: " + subject + ", " + str(e.strerror) + ".")
            time.sleep(60)
    # End Send Loop


# Write a new line to the log file
def log(entry, on_boot=False):
    # Create a new file if log doesn't exist, otherwise append a log entry
    with open("/home/pi/cmdMail_log.txt", "a") as f:

    	# Visible separation for new boot up.
        if on_boot:
            f.write("\n\n\n")

    	# Construct a timestamp
        d = datetime.now()

        # Write the line using a date/time stamp and the message
        f.write(d.strftime("%c") + " - " + entry + "\n")
    # Log File is closed


# ENTRY POINT
def main():
	global is_rip_locked

	# Make the is_rip_locked dictionary
	for station in RIP_SCRIPTS:
	    is_rip_locked[station] = False

	# Ensure the user has setup the script
	if USER_NAME == "" or SEND_TO == "":
		log("Emails variables are not setup.")
		exit(1)

	# Start by sending a boot up email.
	send_boot_mail()

	# Continuously monitor email for new commands, pausing every 30 seconds
	try:
	    while True:
	        read_emails()
	        time.sleep(30)
	except:
		# In case of an uncaught exception, get stacktrace for diag and exit.
	    trace_string = traceback.format_exc()

	    # log it locally in case internet is down
	    log("Something happened, I have crashed:\n" + trace_string)

	    # Build and send an email
	    sub = PI_NAME + " cmdMail crashed"
	    msg = "Something went wrong with cmdMail, here is the stack trace:\n\n" + trace_string
	    send_email(sub, msg)

	    # Exit the program with error code 1
	    exit(1)

main()