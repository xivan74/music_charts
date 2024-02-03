from no1 import process
import schedule
from datetime import timedelta


chat_id = "-1002082261665"
private_chat_id = "242137500"
group_chat_id = "-1002082261665"
work_chat_id = "-4158012020"


if __name__ == '__main__':
    time_to_publish = "13:59"
    tz_to_publish = "UTC"
    # process(chat_id=chat_id)
    print()
    schedule.every().day.at(time_to_publish, tz_to_publish).do(process, chat_id=chat_id)
    while True:
        time_of_next_run = schedule.next_run()
        print("\rЗапускаем расписание. Следующая публикация состоится в", time_of_next_run, end="")
        schedule.run_pending()
