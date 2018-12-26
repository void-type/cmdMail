#! /usr/bin/python3

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


# Reads new emails and performs tasks if certain commands are found


# Write a new line to the log file
def log(entry, log_file_path=log_file_path):
    with open(log_file_path, "a") as log_file:
        time_stamp = datetime.now().strftime("%c")
        log_file.write(time_stamp + " - " + entry + "\n")
    # Log File is closed


# Returns a string with the home global IP
def get_home_ip():
    return str(urlopen("http://ipecho.net/plain").read().decode("utf-8"))


# Send an email
def send_email(subject, message=" "):
    # Construct the email in single-string format
    eml = "\r\n".join(["From: " + email_from,
                       "To: " + email_send_to,
                       "Subject: " + email_subject_prefix + ": " + subject,
                       "",
                       message])

    # Send retry loop
    sent = False
    while not sent:
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(email_user_name, email_password)
            server.sendmail(email_from, [email_send_to], eml)
            server.quit()
            sent = True
        except smtplib.SMTPException as e:
            # In case of errors, wait, and then resend
            # Subject can help identify what function tried to send the email
            log("Send Email Error: " + subject + ", " + str(e.args[0]))
            time.sleep(60)
    # End Send retry loop


# Read new emails for commands
def read_emails():
    done = False
    messages = ""

    # Read retry loop
    while not done:
        try:
            # Connect to gmail and send credentials
            pop_conn = poplib.POP3_SSL("pop.gmail.com")
            pop_conn.user(email_user_name)
            pop_conn.pass_(email_password)

            # Connect to server and get new emails
            messages = [pop_conn.retr(i) for i in range(
                1, len(pop_conn.list()[1]) + 1)]

            pop_conn.quit()
            done = True
        except Exception as e:
            # In case of errors, wait, then try again
            error_message = "No arguments found with exception."
            if e.args[0]:
                error_message = e.args[0]
            log("Read Email Error: " + str(error_message))
            time.sleep(60)
    # End Read retry loop

    return messages


# Send an email with the global IP address in it
def send_ip_email():
    ip = get_home_ip()

    log("Home IP requested. Found " + ip)

    # Build and send the email
    sub = "Home IP"
    msg = ip
    send_email(sub, msg)


def find_commands(messages):
    # Exits cmdMail.py
    if "raspi stop listening" in messages:
        log("No longer listening.")
        sub = "Not listening"
        msg = "I am no longer listening."
        send_email(sub, msg)
        exit(0)

    # Returns the external IP address
    if "raspi home ip" in messages:
        threading.Thread(target=send_ip_email).start()


# ENTRY POINT
def main():
    # Ensure the user has setup the script
    if email_user_name == "" or email_send_to == "" or email_password == "":
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
            messages = read_emails()

            # Turn the emails into a single lower case string
            messages = str(messages).lower()

            find_commands(messages)

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
