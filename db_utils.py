import os.path

from sqlalchemy import create_engine, Table, Column, Integer, String, \
    Date, Boolean, insert, update, delete
from sqlalchemy.orm import sessionmaker, registry, relationship
from data_types import ChartItem, No1Item
import psycopg2
from config import db_url, db_url2, BASE_DIR
import sqlite3

engine = create_engine(db_url, echo=False)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = Session()

charts_mapper = registry()


def table_def(table_name):
    return Table(
        table_name,
        charts_mapper.metadata,
        Column("id", Integer, primary_key=True),
        Column("week_date", Date, index=True),
        Column("position", Integer),
        Column("artist", String),
        Column("title", String)
    )


def no1_table_def(table_name):
    return Table(
        table_name,
        charts_mapper.metadata,
        Column("id", Integer, primary_key=True),
        Column("country", String),
        Column("week_date", Date),
        Column("position", Integer),
        Column("artist", String),
        Column("title", String)
    )


def create_table(table_name):
    table: Table = table_def(table_name=table_name)
    table.metadata.create_all(engine)
    return table


def create_no1_table(table_name):
    table: Table = no1_table_def(table_name=table_name)
    table.metadata.create_all(engine)
    return table


def insert_record(table: Table, data: ChartItem):
    data_json = data.model_dump(exclude_none=True)
    print(data_json)
    print(table)
    table_record = insert(table).values(data_json)
    session.execute(table_record)
    session.commit()


def insert_records(table: Table, data: list[ChartItem]):
    chart_items = []
    for chart_item in data:
        chart_items.append(chart_item.model_dump(exclude_none=True))
    table_records = insert(table).values(chart_items)
    session.execute(table_records)
    session.commit()


def pg_conn():
    return psycopg2.connect(db_url)


def db_conn():
    # для подключения к sqlite3
    db_file = os.path.join(BASE_DIR, db_url2)
    return sqlite3.connect(db_file)


