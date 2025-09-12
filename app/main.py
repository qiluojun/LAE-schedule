from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import activities, scheduled_events, calendar, statistics

app = FastAPI(
    title="LAE - 个人日程与主支线管理系统",
    description="Personal schedule and task management system",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(scheduled_events.router, prefix="/api/events", tags=["scheduled_events"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_root():
    return {"message": "LAE Schedule System API"}