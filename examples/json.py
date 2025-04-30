from dataclasses import dataclass
from typing import Final

from parsec import Parser
from parsec.text.lexeme import (
    lex_colon,
    lex_comma,
    lex_l_bracket,
    lex_l_curly,
    lex_literal,
    lex_number,
    lex_r_bracket,
    lex_r_curly,
    lex_string,
)


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


jsonValue = Parser[str, JsonValue]()
jsonNull = lex_literal('null').map(lambda _: JsonNull())
jsonBool = lex_literal('true').map(lambda _: JsonBool(True)) | lex_literal('false').map(lambda _: JsonBool(False))
jsonNumber = lex_number.map(JsonNumber)
jsonString = lex_string.map(JsonString)
jsonArray = jsonValue.sep_by(lex_comma).between(lex_l_bracket, lex_r_bracket).map(JsonArray)
jsonObject = (
    (lex_string.suffix(lex_colon) & jsonValue)
    .sep_by(lex_comma)
    .between(lex_l_curly, lex_r_curly)
    .map(lambda v: JsonObject(dict(v)))
)
jsonValue.define((jsonNull | jsonBool | jsonNumber | jsonString | jsonArray | jsonObject).as_type(JsonValue))
