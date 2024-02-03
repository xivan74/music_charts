import requests
from db_utils import pg_conn
from datetime import date, datetime
from random import shuffle
from youtube_search import YoutubeSearch
from urllib import parse
from json import loads

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

# super_bot_key = os.getenv('SUPER_BOT_KEY')
super_bot_key = "6577858071:AAEzOUDahiaVHO0D_tT8bALNG_NNadN6pMM"
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
ORDER BY random()
"""
used_years_sql = f"""
SELECT year
FROM "used_years"
WHERE used_in_chat = {group_chat_id}
ORDER BY used_when DESC
"""
used_years_insert_sql = """
 INSERT INTO used_years 
 (year, used_when, used_in_chat, post_time, post_id) 
 VALUES 
 (%s, %s, %s, to_timestamp(%s), %s);
"""
conn = pg_conn()


def get_no1_list(chart_date: date):
    year = chart_date.year
    month = chart_date.month
    day = chart_date.day
    with conn.cursor() as curs:
        curs.execute(no1_list_sql, (year, month, day))
        no1_all = curs.fetchall()
    # print(f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}")
    return no1_all


def get_yt_urls(no1_list: list[tuple]):
    new_no1_list = []
    for no1 in no1_list:
        country, week_date, artist, title = no1
        yt_url = get_yt_url(artist, title)
        new_no1_list.append((country, week_date, artist, title, yt_url))
    return new_no1_list


def print_no1_list(no1_list):
    no1_list_str = ""
    for no1 in no1_list:
        country, week_date, artist, title, yt_url = no1
        song = f"{artist.upper()} - {title}"
        yt_link = f"<a href='{yt_url}'>{song}</a>"
        no1_row = f"{countries[country]['emoji']} <b>{countries[country]['rus']} |</b> {yt_link}"
        no1_list_str += f"{no1_row}\n"
    return no1_list_str


def get_yt_url(artist, title):
    search_string = f"{artist} - {title}"
    results = YoutubeSearch(search_string, max_results=1).to_dict()
    return f"https://www.youtube.com/watch?v={results[0]['id']}"


def get_chart_year():
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
    notif_full_url = post_url.format(BOT_KEY=super_bot_key, CHAT_ID=chat_id, TEXT=encoded_text)
    return notif_session.get(notif_full_url, timeout=5)


def get_message_head(chart_date: date):
    message = f"<b>{chart_date.day} {russian_month[chart_date.month-1]} {chart_date.year} года | Лидеры хит-парадов</b>"
    return message


def insert_used_songs(post_date, chart_year, no1_list):
    pass


def insert_used_year(chart_year, used_when, chat_id, post_datetime, post_id):
    with conn.cursor() as curs:
        curs.execute(used_years_insert_sql, (chart_year, used_when, chat_id, post_datetime, post_id))
    conn.commit()


def get_post_answer(result_text):
    post_answer = loads(result_text)
    return post_answer


def get_post_datetime(post_answer):
    return post_answer["result"]["date"]


def get_post_id(post_answer):
    return post_answer["result"]["message_id"]


def get_chat_name(post_answer):
    return post_answer["result"]["chat"]["username"]


def process(chat_id):
    post_date = datetime.now()
    chart_year = get_chart_year()
    chart_date = post_date.replace(year=chart_year)
    no1_list = get_no1_list(chart_date)
    no1_list_with_yt = get_yt_urls(no1_list)
    no1_list_str = print_no1_list(no1_list_with_yt)
    message = f"{get_message_head(chart_date)}\n\n{no1_list_str}"
    print(message)
    res = send_message(message, chat_id)
    print(res.text)
    if res.status_code == 200:
        post_answer = get_post_answer(res.text)
        print(post_answer)
        post_datetime = get_post_datetime(post_answer)
        post_id = get_post_id(post_answer)
        if chat_id != private_chat_id:
            insert_used_year(chart_year, post_date, chat_id, post_datetime, post_id)
        if chat_id == group_chat_id:
            chat_name = get_chat_name(post_answer)
            private_message = f"Создан <a href='https://t.me/{chat_name}/{post_id}'>пост</a>"
            send_message(private_message, private_chat_id)


now = datetime.now()
# now = datetime(year=1988, month=6, day=18)
process(work_chat_id)


