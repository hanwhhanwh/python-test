import smtplib
from email.mime.text import MIMEText
 
smtp = smtplib.SMTP('mail.smtp-server.kr', 25)
smtp.ehlo()      # say Hello
#smtp.starttls()  # TLS 사용시 필요
smtp.login('sender@smtp-server.kr', 'pasword@2!')
 
msg = MIMEText('Mail contents test<br />test.. test..')
msg['From'] = 'sender@smtp-server.kr'
msg['To'] = 'hbesthee@naver.com'
msg['Subject'] = '메일 발송 시험 (2021.08.05)'
smtp.sendmail('sender@smtp-server.kr', 'hbesthee@naver.com', msg.as_string())
 
smtp.quit()