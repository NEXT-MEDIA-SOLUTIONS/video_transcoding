import os, sys, smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

if __package__ is None:
    sys.path.append('.')
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
from src.helpers.env import Env

MAIL_HOST=Env.get("MAIL_HOST","smtp.office365.com")
MAIL_PORT=int(Env.get("MAIL_PORT",587))
MAIL_USER=Env.get("MAIL_USER")
MAIL_PWD=Env.get("MAIL_PWD")
MAIL_TO=Env.get("MAIL_TO")
MAIL_CC=Env.get("MAIL_CC")
if "," in MAIL_TO:
    MAIL_TO = MAIL_TO.split(",")

signature="""


---
Cordialement,
Votre équipe de support.
AdTech - RMC & BFM ADS
"""

def send_mail(subject="⚠ Alert Bouygues TVS ⚠ ", message_content="This is a test email sent via SMTP.",  attachment_file_path=None, important=False):
    # Set up the email content
    msg = EmailMessage()
    message_content += signature
    msg.set_content(message_content)
    
    msg['Subject'] = subject
    msg['From'] = MAIL_USER
    msg['CC'] = MAIL_CC
    msg['To'] = MAIL_TO
    if important:
        msg['Importance'] = 'High'  # Mark the email as important
    
    # Attach the file
    if attachment_file_path is None:
        pass
    elif os.path.isfile(attachment_file_path):
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
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as server:
        server.starttls()
        if MAIL_PWD is not None:
            server.login(MAIL_USER, MAIL_PWD)
        server.send_message(msg)


def send_html_mail(subject="⚠ Alert Bouygues TVS ⚠ ", message_content="This is a test email sent via SMTP.", mail_recever=None,  attachment_files=None, important=False):
    # Set up the email content
    
    html_content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DWH ETL Jobs Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .job {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status {
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 3px;
        }
        .success {
            background-color: #2ecc71;
            color: white;
        }
        .failure {
            background-color: #e74c3c;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .error-message {
            background-color: #ffebee;
            border-left: 5px solid #e74c3c;
            padding: 10px;
            margin-top: 10px;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <h1>⚠ Alert Bouygues TVS ⚠</h1>
    <pre style="background-color: #23222a; padding: 10px; border-left: 4px solid #2700e8; overflow-x: auto; color: white;"><code>Environment: {ENV}</code></pre>
    <br>
    {msg}
    <br>
    <footer>
        <p>---</p>
        <p>Cordialement,</p>
        <p>Votre équipe de support.</p>
        <p>AdTech - RMC & BFM ADS</p>
    </footer>
</body>
</html>
""".replace("{msg}",message_content).replace("{ENV}", "PROD" if Env.get("ENV")=="p" else "DEV")
    msg = MIMEMultipart()
    msg.attach(MIMEText(html_content, 'html'))
    msg['Subject'] = subject
    msg['From'] = MAIL_USER
    msg['CC'] = MAIL_CC
    if mail_recever is None:
        mail_recever=MAIL_TO
        mail_recever=', '.join(mail_recever) if isinstance(mail_recever, list) else mail_recever
    msg['To'] = mail_recever
    if important:
        msg['Importance'] = 'High'  # Mark the email as important
    
    # Attach the file
    if attachment_files is None:
        pass
    elif isinstance(attachment_files, list) and len(attachment_files)>0:
        for attachment_file_path in attachment_files:
            if os.path.isfile(attachment_file_path):
                print("email_sender: attachment_file_path exist ... ")
                attachment_file_path = attachment_file_path.replace("\\", "/")
                file_name = attachment_file_path.split("/")[-1]
                with open(attachment_file_path, 'rb') as f:
                    file_data = f.read()
                    
                    # msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
                    
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(file_data)  # file_data est le contenu binaire de votre fichier
                    encoders.encode_base64(attachment)
                    attachment.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
                    msg.attach(attachment)
                    
                    print(f"email_sender: attachment_file len : {len(file_data)}")
            else:
                print(f"attachment_file_path : `{attachment_file_path}` not found !!")

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as server:
        server.starttls()
        if MAIL_PWD is not None:
            server.login(MAIL_USER, MAIL_PWD)
        server.send_message(msg)
    # with open(os.path.join(Env.get("DATA_PATH","./data"),"test_mail.html"),"w", encoding="utf-8") as f:
    #     f.write(html_content)
        
        
# if __name__ == "__main__":
#     send_mail("test ......",important=True)