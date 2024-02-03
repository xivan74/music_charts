from no1 import process
import schedule


chat_id = "-1002082261665"
private_chat_id = "242137500"
group_chat_id = "-1002082261665"
work_chat_id = "-4158012020"


if __name__ == '__main__':
    while True:
        schedule.every().day.at("12:39", "UTC").do(process, chat_id=chat_id)
