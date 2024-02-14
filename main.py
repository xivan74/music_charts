import time
from datetime import date
from no1 import process
import schedule


private_chat_id = "242137500"
group_chat_id = "-1002082261665"
work_chat_id = "-4158012020"
chat_id = group_chat_id


if __name__ == '__main__':
    time_to_publish = "06:59"
    tz_to_publish = "UTC"
    print("Запускаем расписание.")
    tmp_pd = date(year=2024, month=2, day=13)
    schedule.every().day.at(time_to_publish, tz_to_publish).do(process, chat_id=chat_id, post_date=tmp_pd)
    while True:
        time.sleep(1)
        time_of_next_run = schedule.next_run()
        print(f"\rСледующая публикация состоится в {time_of_next_run}", end="")
        schedule.run_pending()
