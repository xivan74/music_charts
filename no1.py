import os

import requests
from db_utils import pg_conn
from datetime import date, datetime, timedelta
from random import shuffle
from youtube_search import YoutubeSearch, urllib
from urllib import parse
from json import loads

BASE_YT_URL = "https://youtube.com"
start_year = 1955
end_year = 2000
russian_month = ["января", "февраля", "марта", "апреля", "мая", "июня",
                 "июля", "августа", "сентября", "октября", "ноября", "декабря"]
countries = {
    "UK": {"emoji": "🇬🇧", "rus": "Великобритания"},
    "USA": {"emoji": "🇺🇸", "rus": "США"},
    "France": {"emoji": "🇫🇷", "rus": "Франция"},
    "Italy": {"emoji": "🇮🇹", "rus": "Италия"},
    "Australia": {"emoji": "🇦🇺", "rus": "Австралия"},
    "Germany": {"emoji": "🇩🇪", "rus": "Германия"},
    "Spain": {"emoji": "🇪🇸", "rus": "Испания"},
    "Netherlands": {"emoji": "🇳🇱", "rus": "Нидерланды"},
    "Austria": {"emoji": "🇦🇹", "rus": "Австрия"},
    "Russia": {"emoji": "🇷🇺", "rus": "Россия"}
}

post_bot_key = os.getenv('MUSIC_POST_BOT_KEY')
notif_session = requests.Session()
private_chat_id = "242137500"
group_chat_id = "-1002082261665"
work_chat_id = "-4158012020"
post_url = "https://api.telegram.org/bot{BOT_KEY}/sendMessage?chat_id={CHAT_ID}&text={TEXT}&parse_mode=HTML"

no1_list_sql = """
SELECT t.country, t.week_date, t.artist, t.title
FROM  	(
        SELECT DISTINCT country 
        FROM public."no1_Singles"
        ) mo
CROSS JOIN LATERAL
        (
        SELECT *
        FROM public."no1_Singles" mi
        WHERE mi.country = mo.country
            AND week_date <= make_date(%s, %s, %s)
        ORDER BY week_date DESC
        LIMIT 1
        ) t
ORDER BY random();
"""
used_years_sql = f"""
SELECT year
FROM "used_years"
WHERE used_in_chat = {group_chat_id}
ORDER BY used_when DESC;
"""
planned_posts_for_date_sql = f"""
SELECT country, chart_date, artist, title, yt_url
FROM "planned_posts"
WHERE published = False AND post_date = %s;
"""
last_planned_post_date_sql = f"""
SELECT post_date, chart_date
FROM "planned_posts"
WHERE published = False and post_date = (
    SELECT max(post_date) FROM "planned_posts"
);
"""
last_post_date_sql = f"""
SELECT year, used_when
FROM "used_years"
WHERE used_when = (
    SELECT max(used_when) FROM "used_years"
);
"""
mark_planned_posts_as_published_sql = f"""
UPDATE planned_posts
SET published = True
WHERE post_date = %s;
"""
used_years_insert_sql = """
 INSERT INTO used_years 
 (year, used_when, used_in_chat, post_time, post_id) 
 VALUES (%s, %s, %s, to_timestamp(%s), %s)
 RETURNING id;
"""
planned_posts_insert_sql = """
 INSERT INTO planned_posts 
 (post_date, chart_date, artist, title, yt_url, country) 
 VALUES (%s, %s, %s, %s, %s, %s)
 RETURNING id;
"""
used_songs_insert_sql = """
 INSERT INTO songs 
 (artist, title, yt_url, used_year_id, country) 
 VALUES (%s, %s, %s, %s, %s);
"""
conn = pg_conn()


def get_no1_list(chart_date: date):
    year = chart_date.year
    month = chart_date.month
    day = chart_date.day
    with conn.cursor() as curs:
        curs.execute(no1_list_sql, (year, month, day))
        no1_all = curs.fetchall()
    return no1_all


def get_yt_urls(no1_list: list[tuple], search_page: bool = False):
    new_no1_list = []
    for no1 in no1_list:
        country, week_date, artist, title = no1
        yt_url = get_yt_url(artist, title)
        yt_search_url = get_yt_search_url(artist, title)
        new_no1_list.append((country, week_date, artist.upper(), title, yt_url, yt_search_url))
    return new_no1_list


def print_no1_list(no1_list):
    no1_list_str = ""
    for no1 in no1_list:
        country, week_date, artist, title, yt_url, yt_search_url = no1
        song = f"{artist} - {title}"
        yt_link = f"<a href='{yt_url}'>{song}</a> (<a href='{yt_search_url}'>найти другой клип</a>)"
        no1_row = f"{countries[country]['emoji']} <b>{countries[country]['rus']} |</b> {yt_link}"
        no1_list_str += f"{no1_row}\n"
    return no1_list_str


def get_yt_url(artist, title):
    search_string = f"{artist} - {title}"
    results = YoutubeSearch(search_string, max_results=1).to_dict()
    return f"{BASE_YT_URL}/watch?v={results[0]['id']}"


def get_yt_search_url(artist, title):
    search_string = f"{artist} - {title}"
    encoded_search = urllib.parse.quote_plus(search_string)
    return f"{BASE_YT_URL}/results?search_query={encoded_search}"


def get_chart_year():
    # очень кривая реализация, нужна доработка
    repeat_after = 30
    all_years = set(range(start_year, end_year + 1))
    with conn.cursor() as curs:
        curs.execute(used_years_sql)
        used_years = curs.fetchmany(repeat_after)
    used_years_list = {uy[0] for uy in used_years}
    last_year = used_years[0][0]
    not_used_years_list = list(all_years - used_years_list)
    while abs(not_used_years_list[0] - last_year) < 7 or not_used_years_list[0] == min(not_used_years_list):
        shuffle(not_used_years_list)
    return not_used_years_list[0]


def send_message(text, chat_id):
    encoded_text = parse.quote(text)
    notif_full_url = post_url.format(BOT_KEY=post_bot_key, CHAT_ID=chat_id, TEXT=encoded_text)
    return notif_session.get(notif_full_url, timeout=5)


def get_message_head(chart_date: date):
    message = (f"<b>{chart_date.day} {russian_month[chart_date.month - 1]} {chart_date.year} года | Лидеры "
               f"хит-парадов разных стран в этот день</b>")
    return message


def insert_used_songs(no1_list, used_year_id):
    with conn.cursor() as curs:
        for no1 in no1_list:
            country, week_date, artist, title, yt_url, yt_search_url = no1
            curs.execute(used_songs_insert_sql, (artist, title, yt_url, used_year_id, country))
    conn.commit()


def insert_used_year(chart_year, used_when, chat_id, post_datetime, post_id):
    with conn.cursor() as curs:
        curs.execute(used_years_insert_sql, (chart_year, used_when, chat_id, post_datetime, post_id))
        conn.commit()
        new_id = curs.fetchone()[0]
    return new_id


def get_post_answer(result_text):
    post_answer = loads(result_text)
    return post_answer


def get_post_datetime(post_answer):
    return post_answer["result"]["date"]


def get_post_id(post_answer):
    return post_answer["result"]["message_id"]


def get_chat_name(post_answer):
    return post_answer["result"]["chat"]["username"]


def plan_post(post_date, chart_date, no1_list):
    for no1 in no1_list:
        country, week_date, artist, title, yt_url, yt_search_url = no1
        with conn.cursor() as curs:
            curs.execute(planned_posts_insert_sql, (post_date, chart_date, artist, title, yt_url, country))
        conn.commit()


def get_no1_planned_list(post_date: datetime):
    with conn.cursor() as curs:
        curs.execute(planned_posts_for_date_sql, [post_date.date()])
        planned_list = curs.fetchall()
    return planned_list


def last_planned_post_date():
    with conn.cursor() as curs:
        curs.execute(last_planned_post_date_sql)
        last_planned = curs.fetchone()
    return last_planned


def last_post_date():
    with conn.cursor() as curs:
        curs.execute(last_post_date_sql)
        last_post = curs.fetchone()
    return last_post


def get_last_post_date_for_planning():
    # Нужно добавить случай, когда обе таблицы пустые и тогда использовать день из параметра (или вчера-сегодня-завтра)
    last_planned = last_planned_post_date()
    if last_planned is not None:
        post_date, chart_date = last_planned
        return post_date
    year, used_when = last_post_date()
    return used_when


def get_no1_full_list(chart_date):
    no1_list = get_no1_list(chart_date)
    return get_yt_urls(no1_list, search_page=False)


def get_no1_full_list_plus_yt_search(chart_date):
    no1_list = get_no1_list(chart_date)
    return get_yt_urls(no1_list, search_page=True)


def mark_planned_posts_as_published(post_date):
    with conn.cursor() as curs:
        curs.execute(mark_planned_posts_as_published_sql, [post_date.date()])
    conn.commit()


def get_no1_list_text(chart_date: datetime, no1_full_list, source="bot"):
    no1_list_str = print_no1_list(no1_full_list)
    if source == "bot":
        bot_string = "Хочешь за 500 рублей свой клип по этим песням?"
        bot_link = "https://www.donationalerts.com/r/best20centurymusic"
        bottom_string = f"♫ <tg-spoiler><a href='{bot_link}'>{bot_string}</a></tg-spoiler> ♫"
        top_string = bottom_string
    else:
        bot_string = "Получи <b>СВОЙ</b> список лидеров хит-парадов за <b>ЛЮБОЙ ДЕНЬ</b>"
        bot_link = "https://t.me/best_20_century_hits_bot"
        bottom_string = f"♫ <tg-spoiler><a href='{bot_link}'>{bot_string}</a></tg-spoiler> ♫"
        top_string = bottom_string
    head = f"{get_message_head(chart_date)}\n\n{top_string}"
    footer = "<b>♪ <a href='https://t.me/best_20_century_hits'>@best_20_century_hits</a> ♪</b>"
    message = f"{head}\n\n{no1_list_str}\n{bottom_string}\n\n{footer}"
    return message


def add_yt_search_url_to_list(no1_list: list[tuple]):
    no1_new_list = []
    for no1 in no1_list:
        if len(no1) == 5:
            country, week_date, artist, title, yt_url = no1
            yt_search_url = get_yt_search_url(artist, title)
            no1 = (country, week_date, artist, title, yt_url, yt_search_url)
            no1_new_list.append(no1)
    return no1_new_list


def make_post(chat_id, post_date: datetime, use_planned=1):
    no1_full_list = list()
    if use_planned == 1:
        print("USE Planned")
        no1_list = get_no1_planned_list(post_date)
        no1_full_list = add_yt_search_url_to_list(no1_list)

        print(no1_full_list)
        chart_date = no1_full_list[0][1]
        chart_year = chart_date.year
    elif len(no1_full_list) == 0 or use_planned == 0:
        print("NOT USE PLANNED")
        chart_year = get_chart_year()
        chart_date = post_date.replace(year=chart_year)
        no1_full_list = get_no1_full_list(chart_date)
    else:
        return
    print(no1_full_list)

    message = get_no1_list_text(chart_date, no1_full_list, source="group")
    print(message)
    res = send_message(message, chat_id)
    print(res.text)
    if res.status_code == 200:
        post_answer = get_post_answer(res.text)
        post_datetime = get_post_datetime(post_answer)
        post_id = get_post_id(post_answer)
        if chat_id != private_chat_id:
            used_year_id = insert_used_year(chart_year, post_date, chat_id, post_datetime, post_id)
            insert_used_songs(no1_full_list, used_year_id)
        if chat_id == group_chat_id:
            chat_name = get_chat_name(post_answer)
            private_message = f"Создан <a href='https://t.me/{chat_name}/{post_id}'>пост</a>"
            send_message(private_message, private_chat_id)
            mark_planned_posts_as_published(post_date)


def make_planned(from_year, delta):
    planned_years = get_years_list(from_year=from_year, delta=delta)
    last_post_date = get_last_post_date_for_planning()
    post_date: date = last_post_date
    print("Last Post Date:", last_post_date)
    for planned_year in planned_years:
        post_date += timedelta(days=1)
        chart_date = post_date.replace(year=planned_year)
        print(chart_date)
        no1_full_list = get_no1_full_list(chart_date)
        print(no1_full_list)
        print("==========\n")
        plan_post(post_date, chart_date, no1_full_list)


def process(chat_id, post_date=""):
    if post_date == "":
        post_date = datetime.now()
    make_post(chat_id, post_date, use_planned=1)


def get_years_list(from_year: int, delta: int):
    years = list(range(start_year, end_year + 1))
    sh_y = []
    ly = len(years)
    ind = years.index(from_year)
    new_ind = ind
    while len(sh_y) < ly:
        i = 0
        while years[new_ind] in sh_y:
            new_ind = ind + delta
            new_ind %= ly
            i += 1
            if i > 1000:
                print("Не получилось создать последовательность лет для отложенного постинга.")
                print("Попробуйте вызывать get_years_list с параметром delta = 7 или 9 или 11.")
                return
        ind = new_ind
        sh_y.append(years[ind])
    return sh_y


def correct_panned(post_date: datetime):
    """
    На самом деле функция ничего не исправляет.
    Она только сообщает о различиях между запланированным постом и чартом
    Исправление этого различия не реализовано

    Возвращает 0, когда нет запланированного поста на дату from_date

    :param from_date:
    :return:
    """
    planned_list = get_no1_planned_list(post_date)
    if len(planned_list) == 0:
        return 0
    planned_dict = {}
    chart_date = post_date
    for planned in planned_list:
        planned_dict[planned[0]] = {}
        chart_date = planned[1]
        planned_dict[planned[0]]["artist"] = planned[2]
        planned_dict[planned[0]]["title"] = planned[3]

    no1_list = get_no1_list(chart_date)
    print(f"Planned {post_date.date()}. NO 1 List to {chart_date}:\n")
    no1_dict = {}
    for no1 in no1_list:
        no1_dict[no1[0]] = {}
        no1_dict[no1[0]]["artist"] = no1[2].upper()
        no1_dict[no1[0]]["title"] = no1[3]

    for country, no1_item in no1_dict.items():
        if no1_item["artist"] != planned_dict[country]["artist"] or no1_item["title"] != planned_dict[country]["title"]:
            print("НЕ СОВПАДАЮТ ДАННЫЕ!", post_date.date(), country)
            print("Planned:", planned_dict[country]["artist"], planned_dict[country]["title"])
            print("No 1:", no1_item["artist"], no1_item["title"])

    return 1


def correct_all_planned(start_date: datetime):
    now = start_date
    res = 1
    while res == 1:
        res = correct_panned(now)
        now += timedelta(days=1)


def send_planned_to_chat(now: datetime):
    i = 0
    while i < 1:
        make_post(work_chat_id, now, use_planned=1)
        now += timedelta(days=1)
        i += 1


if __name__ == '__main__':
    now = datetime(year=2024, month=5, day=12)
    # years_list = get_years_list(from_year=1963, delta=9)
    # print(years_list)
    # make_planned(from_year=1963, delta=9)
    # correct_all_planned(now)
    send_planned_to_chat(now)
