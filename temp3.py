import requests
import re
import psycopg2
from helpers import brl
from tax_calculator import tax_for_html, calculate_tax

DATABASE_URL = "postgres://rtugygfqnqcauo:2aeaa614dc46d36a0f3fe19e55269d96386d0377a3be6c727635f0b3f458edbb@ec2-34-234-185-150.compute-1.amazonaws.com:5432/dcoqc4i24nrr8h?ssl=true"

# second, now we have to think in months, not sales. and include daytrade = -1 (daytrade_a and b)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
daytrade = daytrade_a = daytrade_b = 1
id = 2

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(username, token):
    mail_content = '''Gerenciador de Ações - Código para redefinição de senha\n 
    Copie e cole o seguinte código: ''' + token + '''\n\nCaso você não tenha feito a solicitação, 
    por favor ignore esse email.'''

    #The mail addresses and password
    sender_address = 'zaninmalhadas@gmail.com'
    sender_pass = 'xvpbsandxljdtdqo'
    receiver_address = username
    #Setup the MIME
    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = 'Gerenciador de Ações - Redefinição de Senha'
    #The subject line
    #The body and the attachments for the mail
    message.attach(MIMEText(mail_content, 'plain'))
    #Create SMTP session for sending the mail
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    text = message.as_string().encode("utf-8")
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
    return 1

send_mail('malhadasneto@hotmail.com', "tokenéesse")