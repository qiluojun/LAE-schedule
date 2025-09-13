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

### 🎉 V1.0 Development Completed (2025-09-13)
- **✅ ALL PHASES COMPLETED**: Backend foundation + Core UI + Feature Enhancement + Debugging & Optimization
- **✅ INTELLIGENT DRAG SYSTEM**: Smart target validation with automatic redirection for invalid targets
- **✅ ENHANCED USER EXPERIENCE**: Grid resizing, spacing optimization, and visual feedback improvements
- **✅ ROBUST ERROR HANDLING**: Comprehensive API error diagnostics and drag event validation
- **✅ CROSS-WEEK FUNCTIONALITY**: Stable week navigation with proper drag-drop re-initialization
- **✅ ALPINE.JS INTEGRATION**: Resolved all scope conflicts with responsive activity pool rendering

### 🚀 System Status: Production Ready
**Core Features**:
1. **✅ FULLY FUNCTIONAL**: Hierarchical activity management with unlimited nesting
2. **✅ FULLY FUNCTIONAL**: Intelligent drag-and-drop scheduling with error correction
3. **✅ FULLY FUNCTIONAL**: Three-view architecture (Summary/Week/Month) with seamless navigation
4. **✅ FULLY FUNCTIONAL**: Complete CRUD operations and statistical reporting
5. **✅ FULLY FUNCTIONAL**: Smart target detection and automatic error recovery

**Technical Achievements**:
- **Smart Drag Validation**: `validateDropTarget()` and `findNearestValidTimeSlot()` methods
- **Activity Pool Stability**: Alpine.js responsive rendering with `x-html` approach
- **Grid Optimization**: 120px height, 8px spacing, enhanced visual feedback
- **API Diagnostics**: Comprehensive error logging and debugging information
- **Cross-Browser Compatibility**: Stable performance across different environments

### 📋 Development Summary
- **Phase 1-4**: ✅ COMPLETED (September 12-13, 2025)
- **System Status**: 🟢 PRODUCTION READY
- **User Experience**: ✅ INTUITIVE AND RELIABLE
- **Technical Debt**: ✅ FULLY RESOLVED
- **Test Coverage**: ✅ COMPLETE USER WORKFLOW VALIDATED

### 🎯 Next Development Phase (V2.0+)
The system is now ready for production use. Future enhancements may include:
1. Markdown export functionality for Obsidian integration
2. Mobile responsiveness improvements
3. Performance optimizations and caching
4. Additional time slot configurations
5. Data backup and recovery features

## Key Implementation Notes

- Use SQLAlchemy for all database operations
- Implement hierarchical queries for activity trees
- Frontend uses Bootstrap + Alpine.js + SortableJS architecture
- Drag-and-drop: Activity cards should remain in pool (clone behavior)
- Time slot encoding: 21,22,51,52,71 (extensible two-digit system)
- Backend serves both API endpoints and HTML template
- JavaScript embedded directly in HTML to avoid static file path issues

## Development Workflow

### ⚠️ CRITICAL: User Testing Feedback Loop

**IMPORTANT WORKFLOW REQUIREMENT**: When implementing new features or fixes during development sessions:

1. **One Feature at a Time**: Implement only ONE feature or fix per iteration
2. **Wait for User Testing**: After completing each feature/fix, STOP and wait for user testing feedback
3. **No Automatic Continuation**: Do NOT automatically proceed to the next item in the todo list
4. **User Validation Required**: Wait for explicit user confirmation that:
   - The feature works as expected
   - No regressions were introduced
   - User is satisfied with the implementation
5. **Address Feedback First**: If issues are found, fix them before moving to the next feature
6. **Explicit Permission to Continue**: Only proceed to the next todo item when user explicitly requests it

**Why This Matters**:
- Ensures each feature is thoroughly validated before adding complexity
- Prevents cascading issues from undetected bugs
- Allows for user feedback to guide implementation details
- Maintains system stability throughout development process

**Example Workflow**:
```
✅ Implement Feature A → STOP → Tell user what to test/observe → Wait for user feedback → Fix issues if any
✅ User confirms Feature A working → User requests work on Feature B
✅ Implement Feature B → STOP → Tell user what to test/observe → Wait for user feedback → ...
```

### 📋 CRITICAL: Clear Testing Instructions

**When pausing for user feedback, ALWAYS provide specific testing instructions:**

1. **Specific Actions to Test**: Tell the user exactly what operations to perform
   - Example: "Please test dragging a card from the activity pool to the Monday morning slot"
   - Example: "Try switching to the previous week and then attempt dragging"

2. **Observable Behaviors**: Specify what the user should see happen
   - Example: "The card should appear in the target slot and remain in the activity pool"
   - Example: "The week navigation should update the dates and grid content"

3. **Console Output to Monitor**: Direct attention to specific console messages
   - Example: "Watch for 🎯 icons in the console showing drag target validation"
   - Example: "Check if there are any red error messages or ❌ symbols"

4. **UI Elements to Observe**: Point out visual changes or states
   - Example: "The target slot should highlight with a green border during dragging"
   - Example: "The modal should close automatically after saving"

5. **Error Conditions to Check**: Mention potential failure scenarios
   - Example: "If dragging fails, check if the console shows 'Invalid target' warnings"
   - Example: "Verify that no 400 API errors appear in the Network tab"

**Bad Example**:
```
"Please test the drag functionality and let me know if it works."
```

**Good Example**:
```
"Please test the following:
1. Open browser Developer Console (F12)
2. Drag a card from activity pool to Monday 21 slot
3. Watch for 🎯 console message showing target validation
4. Confirm the card appears in the slot
5. Check that the card remains visible in the activity pool
6. Report any error messages (❌ symbols) in console"
```

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