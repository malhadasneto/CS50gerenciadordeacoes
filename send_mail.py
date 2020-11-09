import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(username, token):
    mail_content = '''Gerenciador de Ações - Código para redefinição de senha\n 
    Copie e cole o seguinte código: ''' + token + '''\n\nCaso você não tenha feito a solicitação, 
    por favor ignore esse email.'''

    #The mail addresses and password
    sender_address = 'zaninmalhadas@gmail.com'
    sender_pass = 'deacavalo'
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