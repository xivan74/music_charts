from pydantic import BaseModel, field_validator
from datetime import date


class ChartItem(BaseModel):
    week_date: date
    position: int
    artist: str
    title: str

    @field_validator("position", mode="before")
    @classmethod
    def remove_whitespaces(cls, raw: str) -> str:
        return raw.strip()


class No1Item(ChartItem):
    position: int = 1
    country: str


def validate_charts_data_list(data_list):
    validated_data = list()
    for data_item in data_list:
        validated_item = validate_chart_data(data_item)
        validated_data.append(validated_item)
    print("List Validated")
    return validated_data


def validate_no1_data_list(data_list):
    validated_data = list()
    for data_item in data_list:
        validated_item = validate_no1_data(data_item)
        validated_data.append(validated_item)
    print("List Validated")
    return validated_data


def validate_no1_common_data_list(data_list, country):
    validated_data = list()
    for data_item in data_list:
        if "position" not in data_item.keys() or data_item["position"].strip() == '1':
            validated_item = validate_no1_common_data(data_item, country)
            validated_data.append(validated_item)
    print("List Validated")
    return validated_data


def validate_chart_data(data_item):
    return ChartItem.model_validate(data_item)


def validate_no1_data(data_item):
    return No1Item.model_validate(data_item)


def validate_no1_common_data(data_item, country):
    data_item["country"] = country
    return No1Item.model_validate(data_item)
