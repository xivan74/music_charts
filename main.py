from no1 import process
import schedule

chat_id = "-1002082261665"


while True:
    schedule.every().day.at("11:59", "UTC").do(process, chat_id=chat_id)
