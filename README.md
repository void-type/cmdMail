# cmdMail
An app that responds to commands via email and performs tasks autonomously.

### Dependencies / Installation
This script is written mainly for Raspian on the Raspberry Pi which comes with Python 3.5.3.
You will also need an email account without 2FA for the script to listen to.

This program is meant as a skeleton or sample program to get started with automated tasking and using emails to control a computer.
You can add many other features by extending this program to call out to external programs and scripts.

Note that this script will parse any email that comes to the inbox. This can be a vector for spam emails to unintentionally run commands. It's best if you make commands with words that are unlikely to be found in spam, or use a gibberish keyword.
