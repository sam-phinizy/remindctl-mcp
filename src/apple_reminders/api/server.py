from apple_reminders.client import AsyncRemindersClient
from apple_reminders.exceptions import (
    RemindersAuthError,
    RemindersError,
    RemindersNotFoundError,
    RemindersTimeoutError,
)
from apple_reminders.models import Priority

client = AsyncRemindersClient()


def create_app():
    """Create and return the FastAPI app. Lazily imports fastapi."""
    from typing import Annotated
    from fastapi import Body, FastAPI, Request  # lazy import — requires apple-reminders-py[api]
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    app = FastAPI(title="Apple Reminders API", version="0.2.0")

    # -- Exception handlers --

    @app.exception_handler(RemindersNotFoundError)
    async def not_found_handler(request: Request, exc: RemindersNotFoundError):
        return JSONResponse(status_code=404, content={"error": str(exc)})

    @app.exception_handler(RemindersAuthError)
    async def auth_handler(request: Request, exc: RemindersAuthError):
        return JSONResponse(status_code=403, content={"error": str(exc)})

    @app.exception_handler(RemindersTimeoutError)
    async def timeout_handler(request: Request, exc: RemindersTimeoutError):
        return JSONResponse(status_code=504, content={"error": str(exc)})

    @app.exception_handler(RemindersError)
    async def base_handler(request: Request, exc: RemindersError):
        return JSONResponse(status_code=500, content={"error": str(exc)})

    # -- Request bodies --

    class AddReminderRequest(BaseModel):
        title: str
        list: str | None = None
        due: str | None = None
        notes: str | None = None
        priority: Priority | None = None

    class EditReminderRequest(BaseModel):
        title: str | None = None
        due: str | None = None
        notes: str | None = None
        priority: Priority | None = None
        list: str | None = None
        clear_due: bool = False

    class CompleteRequest(BaseModel):
        ids: list[str]

    class CreateListRequest(BaseModel):
        name: str

    class RenameListRequest(BaseModel):
        new_name: str

    # -- Reminder routes --

    @app.get("/reminders")
    async def get_reminders(filter: str = "today", list: str | None = None):
        results = await client.show(filter, list=list)
        return [r.model_dump(by_alias=True) for r in results]

    @app.post("/reminders", status_code=201)
    async def add_reminder(body: Annotated[AddReminderRequest, Body()]):
        result = await client.add(
            body.title, list=body.list, due=body.due, notes=body.notes, priority=body.priority
        )
        return result.model_dump(by_alias=True)

    @app.post("/reminders/complete")
    async def complete_reminders(body: Annotated[CompleteRequest, Body()]):
        results = await client.complete(body.ids)
        return [r.model_dump(by_alias=True) for r in results]

    @app.patch("/reminders/{id}")
    async def edit_reminder(id: str, body: Annotated[EditReminderRequest, Body()]):
        result = await client.edit(
            id, title=body.title, due=body.due, notes=body.notes,
            priority=body.priority, list=body.list, clear_due=body.clear_due,
        )
        return result.model_dump(by_alias=True)

    @app.delete("/reminders/{id}")
    async def delete_reminder(id: str, force: bool = True):
        return await client.delete(id, force=force)

    @app.post("/reminders/{id}/uncomplete")
    async def uncomplete_reminder(id: str):
        result = await client.uncomplete(id)
        return result.model_dump(by_alias=True)

    # -- List routes --

    @app.get("/lists")
    async def get_lists():
        results = await client.lists()
        return [rl.model_dump(by_alias=True) for rl in results]

    @app.get("/lists/{name}")
    async def get_list(name: str):
        results = await client.get_list(name)
        return [r.model_dump(by_alias=True) for r in results]

    @app.post("/lists", status_code=201)
    async def create_list(body: Annotated[CreateListRequest, Body()]):
        result = await client.create_list(body.name)
        return result.model_dump(by_alias=True)

    @app.patch("/lists/{name}")
    async def rename_list(name: str, body: Annotated[RenameListRequest, Body()]):
        result = await client.rename_list(name, body.new_name)
        return result.model_dump(by_alias=True)

    @app.delete("/lists/{name}")
    async def delete_list(name: str, force: bool = False):
        return await client.delete_list(name, force=force)

    # -- Status --

    @app.get("/status")
    async def get_status():
        result = await client.status()
        return result.model_dump(by_alias=True)

    return app


def main() -> None:
    import uvicorn  # lazy import — requires apple-reminders-py[api]
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
