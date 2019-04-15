from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

t = ['THIS IS A TEST', 'Creating: Project_Blue-1_29_2019_H10-M56', 'Deleting: Project_Blue-12-19-2018',
     'Creating: Moodle-1_29_2019_H10-M56', 'Deleting: Moodle-just_built_1_23_19',
     'Creating: Node_sandbox-1_29_2019_H10-M56', 'Deleting: Node_sandbox-12-19-2018',
     'Creating: AXIINTER_Webtools-1_29_2019_H10-M56', 'Deleting: AXIINTER_Webtools-12-19-2018',
     'Creating: AWS_Backup_Handler-1_29_2019_H10-M56', 'Deleting: AWS_Backup_Handler-12-19-2018',
     'Creating: WordPress-testbox-1_29_2019_H10-M56', 'Deleting: WordPress-testbox-12-19-2018']

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
    password = 'ModularCatGifs#4#$'

    # The actual mail send
    smtp = smtplib.SMTP('smtp.gmail.com', 587, None, 30)

    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(username, password)
    smtp.sendmail(msg['From'], msg['To'], msg.as_string())
    smtp.close()

if __name__ == "__main__":
    sendEmail('t', ['jake.poirier@axi-international.com'], t)