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
from config import *

# Write a new line to the log file
def log(entry, log_file=LOG_FILE):
    # Create a new file if log doesn't exist, otherwise append a log entry
    with open(log_file, "a") as f:

        # Construct a timestamp
        d = datetime.now()

        # Write the line using a date/time stamp and the message
        f.write(d.strftime("%c") + " - " + entry + "\n")
    # Log File is closed


# Returns a string with the home global IP
def get_home_ip():
    return str(urlopen("http://ipecho.net/plain").read().decode("utf-8"))


# Send an email with the global IP address in it
def send_ip_email():
    ip = get_home_ip()

    log("Home IP requested. Found " + ip)

    # Build and send the email
    sub = "Home IP"
    msg = ip
    send_email(sub, msg)


# Send an email
def send_email(subject, message=" "):
    # Construct the email in single-string format
    eml = "\r\n".join(["From: " + FROM_NAME,
                       "To: " + SEND_TO,
                       "Subject: " + SUBJECT_PREFIX + ": " + subject,
                       "",
                       message])

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
            log("Send Email Error: " + subject + ", " + str(e.message) + ".")
            time.sleep(60)
    # End Send Loop


# Read new emails from an account for commands
def read_emails():
    done = False
    messages = ""

    # main loop
    while not done:
        try:
            # Connect to gmail and send credentials
            pop_conn = poplib.POP3_SSL("pop.gmail.com")
            pop_conn.user(USER_NAME)
            pop_conn.pass_(PASSWORD)

            # Connect to server and get new emails
            messages = [pop_conn.retr(i) for i in range(
                1, len(pop_conn.list()[1]) + 1)]

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

    # Exits cmdMail.py
    if "raspi stop listening" in messages:
        log("No longer listening.")

        # Build and send an email
        sub = "Not listening"
        msg = "I am no longer listening."
        send_email(sub, msg)

        # Exit the program
        exit(0)

    # Returns the external IP address
    if "raspi home ip" in messages:
        t = threading.Thread(target=send_ip_email)
        t.start()


# ENTRY POINT
def main():
    # Ensure the user has setup the script
    if USER_NAME == "" or SEND_TO == "" or PASSWORD == "":
        log("Email variables are not setup. Exiting.")
        exit(1)

    # Start by sending a boot up email.
    # 2 minute delay to allow drivers and internet connection to get going
    time.sleep(120)
    log("Booting up.")

    # Build and send the email
    sub = "Startup complete"
    msg = "I have successfully booted up.\nHome IP Address: " + get_home_ip() + "."
    send_email(sub, msg)

    loop_delay = 30
    home_ip_delay = (5 * 60) / loop_delay
    loop_count = 10
    home_ip = ""

    # Continuously monitor email for new commands, pausing every 30 seconds
    try:
        while True:
            read_emails()

            # Every (home_ip_delay * loop_delay) seconds, check the home IP and log any changes.
            if(loop_count % home_ip_delay == 0):
                new_home_ip = get_home_ip()
                if(new_home_ip != home_ip):
                    home_ip = new_home_ip
                    log(home_ip, "ip.log")

            time.sleep(30)
            loop_count += 1
    except:
        # In case of an uncaught exception, get stacktrace for diag and exit.
        trace_string = traceback.format_exc()

        # log it locally in case internet is down
        log("Something happened, I have crashed:\n" + trace_string)

        # Build and send an email
        sub = "cmdMail crashed"
        msg = "Something went wrong with cmdMail, here is the stack trace:\n\n" + trace_string
        send_email(sub, msg)

        # Exit the program with error code 1
        exit(1)


main()
