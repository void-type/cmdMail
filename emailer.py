import poplib
import smtplib
import time
import config
import utilities

retry_delay = 30

# Send an email
def send(subject, message=" "):
    # Construct the email in single-string format
    eml = "\r\n".join(["To: " + config.email_send_to,
                       "Subject: " + config.email_subject_prefix + ": " + subject,
                       "",
                       message])

    # Send retry loop
    sent = False
    while not sent:
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(config.email_user_name, config.email_password)
            server.sendmail(config.email_user_name, [config.email_send_to], eml)
            server.quit()
            sent = True
        except smtplib.SMTPException as e:
            # In case of errors, wait, and then resend
            # Subject can help identify what function tried to send the email
            utilities.log("Send Email Error: " +
                          subject + ", " + str(e.args[0]))
            time.sleep(retry_delay)
    # End Send retry loop


# Read new emails for commands
def read():
    done = False
    messages = ""

    # Read retry loop
    while not done:
        try:
            # Connect to gmail and send credentials
            pop_conn = poplib.POP3_SSL("pop.gmail.com")
            pop_conn.user(config.email_user_name)
            pop_conn.pass_(config.email_password)

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
            utilities.log("Read Email Error: " + str(error_message))
            time.sleep(retry_delay)
    # End Read retry loop

    return messages
