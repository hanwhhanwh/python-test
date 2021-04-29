import smtplib
from email.mime.text import MIMEText
 
smtp = smtplib.SMTP('smtp.live.com', 587)
smtp.ehlo()      # say Hello
smtp.starttls()  # TLS 사용시 필요
smtp.login('hanwh@hunature.net', '**')
 
msg = MIMEText('본문 테스트 메시지')
msg['Subject'] = '메일 발송 시험 (2021.02.15)'
msg['To'] = 'hbesthee@naver.com'
smtp.sendmail('hanwh@hunature.net', 'hbesthee@naver.com', msg.as_string())
 
smtp.quit()