import os, sys, smtplib
from email.message import EmailMessage

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
from src.helpers.env import Env

MAIL_USER=Env.get("MAIL_USER")
MAIL_PWD=Env.get("MAIL_PWD")
MAIL_TO=Env.get("MAIL_TO")


signature="""


That's it 😊, see you next time 🙏.
---
AdTech - Altice Media
"""

def send_mail(message_content="This is a test email sent via SMTP.",  attachment_file_path=None):
    # Set up the email content
    msg = EmailMessage()
    message_content += signature
    msg.set_content(message_content)
    
    msg['Subject'] = "⚠ Alert Bouygues TVS ⚠ "
    msg['From'] = MAIL_USER # "adtech_nextms.fr@alticemedia.com"
    msg['CC'] = MAIL_USER
    msg['To'] = MAIL_TO
    
    # Attach the file 
    if attachment_file_path is not None and os.path.isfile(attachment_file_path):
        print("email_sender: attachment_file_path exist ... ")
        attachment_file_path = attachment_file_path.replace("\\", "/")
        with open(attachment_file_path, 'rb') as f:
            file_data = f.read()
            file_name = attachment_file_path.split("/")[-1]
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            
            print(f"email_sender: attachment_file len : {len(file_data)}")
    else:
        print(f"attachment_file_path : `{attachment_file_path}` not found !!")
    
    # Connect to the SMTP server and send the email
    with smtplib.SMTP('smtp.office365.com', 587) as server:
        server.starttls()
        server.login(MAIL_USER, MAIL_PWD)
        server.send_message(msg)
        
if __name__ == "__main__":
    send_mail("test ......")