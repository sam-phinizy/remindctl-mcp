from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

Priority = Literal["none", "low", "medium", "high"]
ReminderFilter = Literal[
    "today", "tomorrow", "week", "overdue", "upcoming", "completed", "all"
]


class _Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Reminder(_Base):
    id: str
    title: str
    due_date: datetime | None = None
    is_completed: bool = False
    list_id: str = Field(alias="listID")
    list_name: str
    priority: Priority = "none"
    notes: str | None = None


class ReminderList(_Base):
    id: str
    title: str
    reminder_count: int = 0
    overdue_count: int = 0


class AuthStatus(_Base):
    authorized: bool
    status: str
