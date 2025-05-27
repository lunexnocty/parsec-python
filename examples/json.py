from dataclasses import dataclass
from typing import Final

from parsec import Parser
from parsec.text import lex


class JsonValue: ...


@dataclass
class JsonObject:
    value: dict[str, JsonValue]


@dataclass
class JsonArray:
    value: list[JsonValue]


@dataclass
class JsonString:
    value: str


@dataclass
class JsonNumber:
    value: int | float


@dataclass
class JsonBool:
    value: bool


@dataclass
class JsonNull:
    value: Final[None] = None


"""EBNF of Json
>>> JsonValue := <JsonNull> | <JsonBool> | <JsonNumber> | <JsonString> | <JsonArray> | <JsonObject>
>>> JsonNull := "null"
>>> JsonBool := "true" | "false"
>>> JsonNumber := { number }
>>> JsonString := { string }
>>> JsonArray := '[' [<JsonValue> (',' <JsonValue>)*] ']'
>>> JsonObject := '{' [<JsonString> ':' <JsonValue> (',' <JsonString> ':' <JsonValue>)*] '}'
"""

jsonValue = Parser[str, JsonValue]()
jsonNull = lex.literal('null').map(lambda _: JsonNull())
jsonBool = lex.literal('true').map(lambda _: JsonBool(True)) | lex.literal('false').map(lambda _: JsonBool(False))
jsonNumber = lex.number.map(JsonNumber)
jsonString = lex.string.map(JsonString)
jsonArray = jsonValue.sep_by(lex.comma).default([]).between(lex.l_bracket, lex.r_bracket).map(JsonArray)
jsonObject = (
    (lex.string.suffix(lex.colon) & jsonValue)
    .sep_by(lex.comma)
    .default([])
    .between(lex.l_curly, lex.r_curly)
    .map(lambda v: JsonObject(dict(v)))
)
jsonValue.define((jsonNull | jsonBool | jsonNumber | jsonString | jsonArray | jsonObject).as_type(JsonValue))
