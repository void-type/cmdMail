from urllib.request import urlopen
import utilities
import emailer

current_home_ip = ""


# Send an email with the global IP address in it
def send_ip_email():
    ip = check_against_current()

    utilities.log("Home IP requested. Found " + ip)
    emailer.send("Home IP", ip)


# Return the current home IP and log any changes.
def check_against_current():
    global current_home_ip
    new_current_home_ip = get()

    if(new_current_home_ip != current_home_ip):
        current_home_ip = new_current_home_ip
        utilities.log(current_home_ip, "ip.log")

    return current_home_ip


# Returns a string with the home global IP
def get():
    return urlopen("http://ipecho.net/plain").read().decode("utf-8")
