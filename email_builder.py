from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def build_html_message(message_arr):
    html = '<table cellpadding="0" cellspacing="0" border="0" width="100%" ' \
           'style="font-family: Courier; font-size: 15px;">'
    for string in message_arr:
        if 'Creating' in string:
            html += '<tr style="color: #4392f1;"><th align="left" style="padding-bottom: 5px;">' + string + "</th></tr>"
        elif 'Deleting' in string:
            html += '<tr style="color: #dc493a;"><th align="left" style="padding-bottom: 5px;">' + string + "</th></tr>"
        else:
            html += '<tr style="color: black;"><th align="left" style="padding-bottom: 5px; font-size: 25px;">' + string + "</th></tr>"
    html += "</table>"
    return html


def sendEmail(subject, recipients, msgText):
    '''Sends email to cell phone alerting user of sale/purchase'''

    # Build the message
    msg = MIMEMultipart()
    msg['From'] = 'AXI AWS Backup'
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject
    emailContent = MIMEText(build_html_message(msgText), 'html')
    msg.attach(emailContent)

    # Credentials (if needed)
    username = 'remote.pc.axi@gmail.com'
    password = ''

    # The actual mail send
    smtp = smtplib.SMTP('smtp.gmail.com', 587, None, 30)

    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(username, password)
    smtp.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp.close()

if __name__ == "__main__":
    build_html_message(t)
    # sendEmail('t', ['jake.poirier@axi-international.com'], build_html_message(t))