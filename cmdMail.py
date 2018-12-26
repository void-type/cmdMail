#! /usr/bin/python3

import ssl
import time
from subprocess import call
import threading
import traceback
import config
import emailer
import ip_address
import utilities


# Reads new emails and performs tasks if certain commands are found


def on_startup():
    # Ensure the user has setup the script
    if config.email_user_name == "" or config.email_send_to == "" or config.email_password == "":
        utilities.log("Email variables are not setup. Exiting.")
        exit(1)

    # Start by sending a boot up email.
    # 2 minute delay to allow drivers and internet connection to get going
    time.sleep(120)
    utilities.log("Booting up.")

    ip = ip_address.check_against_current()

    # Build and send the email
    sub = "Startup complete"
    msg = "I have successfully booted up.\n"
    msg += "Home IP Address: " + ip
    emailer.send(sub, msg)

def read_commands():
    messages = str(emailer.read()).lower()

    # Exits cmdMail.py
    if "raspi stop listening" in messages:
        utilities.log("No longer listening.")
        sub = "Stopped"
        msg = "I am no longer listening."
        emailer.send(sub, msg)
        exit(0)

    # Returns the external IP address
    if "raspi home ip" in messages:
        threading.Thread(target=ip_address.send_ip_email).start()


def regular_interval():
    ip_address.check_against_current()


def main():
    on_startup()

    # Delays measured in seconds.
    loop_delay = 10
    regular_interval_delay = 30 * 60
    loop_count = 0

    # Continuously monitor email for new commands, pausing every 30 seconds
    try:
        while True:
            # Check for commands in emails every loop
            read_commands()

            # On a regular interval, run certain jobs
            if((loop_count * loop_delay) % regular_interval_delay == 0):
                regular_interval()

            time.sleep(loop_delay)
            loop_count += 1
    except:
        # In case of an uncaught exception, get stacktrace for diag and exit.
        trace_string = traceback.format_exc()

        # log it locally in case internet is down
        utilities.log("Something happened, I have crashed:\n" + trace_string)

        # Build and send an email
        sub = "cmdMail crashed"
        msg = "Something went wrong with cmdMail, here is the stack trace:\n\n" + trace_string
        emailer.send(sub, msg)

        # Exit the program with error code 1
        exit(1)


main()
