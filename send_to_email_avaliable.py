import smtplib as smtp
from email.mime.text import MIMEText
from email.header import Header



def send_email_about_avaliable(avaliable):
    login = 'otchet064@gmail.com'
    password = 'vbgzqbkjukpuppkv'

    server = smtp.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(login, password)


    subject = 'Сайт(ы) снова доступен(ы) после более часа недоступности.'

    text = "" # здесь можно какай-то шаблон написать
    for site in avaliable:
        text += str(site) + "\n"

    print(text)

    message = MIMEText(text, 'plain', 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    server.sendmail(login, 'pivmatal@gmail.com', message.as_string())


# avaliable = ["Публичное акционерное общество 'ВАНТ МОБАЙЛ БАНК'", "Общество с ограниченной ответственностью Инвестиционная компания «Финдом»", "Акционерное общество 'ЮниКредит Банк'"]
# avaliable.append("TEST COMPANY")

# send_email_about_avaliable(avaliable)



