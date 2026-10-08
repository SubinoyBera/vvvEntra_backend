from enum import StrEnum

from sqlalchemy import Enum


def str_enum(enum_cls: type[StrEnum], name: str, length: int = 30) -> Enum:
    """Column type: a plain VARCHAR holding the enum's lowercase value.

    Not a native Postgres ENUM. The matching CHECK constraint is added explicitly 
    in each model's __table_args__ via sql_in().
    """
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        length=length,
        values_callable=lambda e: [member.value for member in e],
    )


def sql_in(column: str, enum_cls: type[StrEnum]) -> str:
    """SQL text for a CHECK constraint: "col IN ('a', 'b', ...)"."""
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return f"{column} IN ({values})"