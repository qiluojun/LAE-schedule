from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import scheduled_events, calendar, statistics, domains, activity_types, schedules

app = FastAPI(
    title="LAE - 个人日程与主支线管理系统 v2.0",
    description="Personal schedule and task management system with matrix architecture",
    version="2.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# V1 APIs (for backward compatibility)
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])

# V2 APIs (new architecture)
app.include_router(domains.router, tags=["domains"])
app.include_router(activity_types.router, tags=["activity-types"])
app.include_router(schedules.router, tags=["schedules"])
app.include_router(scheduled_events.router, tags=["scheduled-events"])  # Updated to v2.0

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_root():
    return {"message": "LAE Schedule System API"}