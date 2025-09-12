# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Required Reading Before Starting

**IMPORTANT**: Before beginning any work, read these key documents to understand the current project state:

1. **DEVELOPMENT_STATUS.md** - Current development state, known issues, and immediate next steps
2. **README.md** - Complete project overview, data models, and technical specifications  
3. This CLAUDE.md file - Development guidance and API reference

These documents contain critical information about completed work, current problems, and debugging context that you MUST understand before making any changes.

## Project Overview

LAE (个人日程与主支线管理系统) is a personal schedule and task management system designed to help manage multiple parallel tasks with time uncertainty and anxiety. This is a blueprint project (version 1.0) focused on implementing a scheduling system with hierarchical task management.

## Architecture

This project follows a **lightweight web framework** approach running locally with browser access:

- **Backend**: Python with Flask/FastAPI
- **Database**: SQLite with SQLAlchemy ORM  
- **Frontend**: HTML, CSS, JavaScript with drag-and-drop functionality
- **Integration**: Markdown export for Obsidian workflow

## Core Data Models

The system is built around two main SQL tables defined via SQLAlchemy:

### `activities` (活动库)
- Hierarchical activity/task structure with unlimited parent-child nesting
- Fields: `id`, `name`, `parent_id`, `description`, `created_at`

### `scheduled_events` (已安排日程)
- Specific schedule instances linking activities to time slots
- Fields: `id`, `activity_id`, `event_date`, `time_slot`, `goal`, `notes`, `status`
- Time slot encoding: Two-digit system where first digit = period, second digit = sequence
  - Current slots: 21,22 (morning), 51,52 (afternoon), 71 (evening)
  - Extensible for future periods (e.g., 81,82 for bedtime)
- `notes` field for additional information (not included in statistics)

## Key Features & Views

### Week View (Core Interface)
- 7-day × 5-timeslot grid layout
- Drag-and-drop activity cards from sidebar pool
- Goal input modal for each scheduled activity
- Primary interaction interface for schedule management

### Month View 
- High-level overview of schedule density
- Navigation entry point to weekly views
- Activity count aggregation per day

### Summary View
- Activity management center (CRUD operations)
- Statistics dashboard for all activities
- Goal tracking and progress overview

## Development Status

### ✅ Completed Phases
**Phase 1**: Backend foundation (COMPLETED)
- FastAPI project structure with SQLAlchemy models
- Complete CRUD API endpoints for activities and scheduled_events
- Calendar APIs for week/month/day views
- Statistics APIs with hierarchical data support
- Database schema with notes field added

**Phase 2**: Core UI development (PARTIALLY COMPLETED)
- HTML page framework with Bootstrap + Alpine.js + SortableJS
- Summary view with activity management and tree structure
- Week view with 7×N dynamic grid layout
- Month view basic structure
- ⚠️ **ISSUE**: Drag-and-drop functionality has technical problems in browser

### ✅ Current State (UPDATED - All Issues Resolved)
- Backend APIs are fully functional and tested ✅
- Frontend interface is fully working with resolved drag-drop ✅
- Application runs at http://127.0.0.1:8000 ✅
- Core interaction flow completely functional ✅
- All critical bugs resolved ✅

### 🎉 Completed Tasks (Phase 2 FINISHED)
**✅ SUCCESS**: All critical functionality now working properly.

Resolved issues:
1. **✅ FIXED**: Drag-and-drop functionality fully operational
2. **✅ FIXED**: Activity card cloning behavior working (cards remain in pool after drag)
3. **✅ FIXED**: Modal popup works correctly after successful drop
4. **✅ FIXED**: Goal and notes editing workflow verified
5. **✅ COMPLETED**: Full user interaction testing successful

### 🔄 Ready for Phase 3: Feature Enhancement
Priority items for next development session:
1. Complete month view calendar functionality  
2. Advanced statistics and reporting features
3. Enhanced user experience improvements
4. Testing drag-and-drop workflow with user validation

## Key Implementation Notes

- Use SQLAlchemy for all database operations
- Implement hierarchical queries for activity trees
- Frontend uses Bootstrap + Alpine.js + SortableJS architecture
- Drag-and-drop: Activity cards should remain in pool (clone behavior)
- Time slot encoding: 21,22,51,52,71 (extensible two-digit system)
- Backend serves both API endpoints and HTML template
- JavaScript embedded directly in HTML to avoid static file path issues

## Development Commands

### Start Development Server
```bash
python run.py
```
Server will run on http://127.0.0.1:8000 with auto-reload enabled.

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Initialize Database
```bash
python -m app.create_db
```

### API Documentation
- Interactive API docs: http://127.0.0.1:8000/docs
- ReDoc documentation: http://127.0.0.1:8000/redoc

## API Endpoints

### Activities (`/api/activities/`)
- `GET /` - List all activities
- `POST /` - Create new activity
- `GET /tree` - Get hierarchical activity tree
- `GET /{id}` - Get specific activity
- `PUT /{id}` - Update activity
- `DELETE /{id}` - Delete activity

### Scheduled Events (`/api/events/`)
- `GET /` - List scheduled events (supports date filtering)
- `POST /` - Create new scheduled event
- `GET /{id}` - Get specific event
- `PUT /{id}` - Update event
- `DELETE /{id}` - Delete event

### Calendar (`/api/calendar/`)
- `GET /week/{date}` - Get week schedule for given date
- `GET /month/{year}/{month}` - Get month overview
- `GET /day/{date}` - Get detailed day schedule

### Statistics (`/api/statistics/`)
- `GET /summary` - System-wide statistics
- `GET /activities/{id}/statistics` - Activity-specific statistics
- `GET /activities/tree-statistics` - Tree view with statistics

## Technical Issues & Debugging (RESOLVED ✅)

### ✅ Resolved Issues (Session Summary)
1. **✅ Drag-and-drop functionality**: Fixed SortableJS integration with Alpine.js context binding
2. **✅ Modal popup problems**: Resolved CSS priority conflicts between Bootstrap `d-block` and Alpine.js `x-show`
3. **✅ JavaScript initialization**: Fixed missing methods and proper initialization timing

### 🔧 Solutions Implemented
- **Bootstrap CSS Fix**: Used dynamic class binding `:class="{ 'd-block': condition }"` to prevent `!important` override
- **Context-Aware Initialization**: SortableJS only initializes in appropriate views (week view for drag-drop)
- **Robust State Management**: Added `forceCloseModal()` method for complete modal state cleanup
- **Alpine.js Integration**: Fixed `this` binding conflicts using `const self = this` pattern
- **Complete Error Handling**: Resolved all JavaScript initialization errors

### 📁 Key Files Modified
- `app/templates/index.html` - Fixed all JavaScript integration issues
- All drag-drop logic now working correctly
- Browser Developer Console shows no errors
- Network tab confirms API calls working properly

### 🛠️ Debugging Methods Used
- Console debugging with detailed logging
- CSS inspection for Bootstrap/Alpine conflicts  
- JavaScript error tracking and resolution
- API connectivity testing

## Primary Use Case

The first core application scenario is `zeroPPD` - this should be considered when implementing features and testing the system.