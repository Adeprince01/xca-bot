# Project Improvements Plan

This document outlines the planned improvements for the Twitter/X Monitor application based on the initial code review.

## Completed Improvements

### Backend: Configuration Management (Security) ✅
- Added `.gitignore` to prevent sensitive files from being committed
- Configured to ignore:
  - Python cache files
  - Environment variables (.env)
  - Configuration files (config.json)
  - Log files
  - Database files
  - IDE/Editor specific files
  - OS specific files
  - Exported data

### Backend: Robust Process Management (Scheduler) ✅
- Replaced subprocess/PID management with APScheduler
- Implemented proper async job scheduling
- Added startup/shutdown handlers
- Improved error handling and logging
- Updated all relevant endpoints to work with scheduler

### Backend: Live Log Streaming ✅
- Added SSE endpoint (`/stream/logs`) for log streaming
- Implemented log buffer system using deque
- Added log management endpoints:
  - `POST /logs/clear`: Clears the log file
  - `GET /logs/download`: Downloads the log file
- Added custom log handler to capture logs for streaming

### Frontend & Backend: Real-time Updates ✅
- Added SSE endpoints in backend:
  - `/stream/status` for monitoring status
  - `/stream/matches` for new matches
  - `/stream/logs` for log updates
- Implemented EventSource connections in frontend
- Removed polling mechanism
- Updated state management for real-time updates
- Added reconnection logic for dropped connections

### Frontend: Enhanced Configuration UX ✅
- Added tag input component using react-select
- Implemented for usernames, regex patterns, and keywords
- Added loading state for configuration saves
- Improved error feedback
- Styled to match the application theme

### Frontend: Dynamic Dashboard Data ✅
- Updated cards with real-time data from SSE streams
- Implemented proper timestamp formatting using formatDateTime 
- Added new functionality:
  - "Run Check Now" button for immediate checks
  - Shows active user badges on dashboard
  - Shows uptime information
  - Added local timezone display for "Matches Today"
  - Shows matches filtered for current day only
- Added loading states and indicators for all actions
- Improved error messaging with detailed error information

### Frontend: Bug Fixes & Stability ✅
- Fixed CSS import path for tag-input styles
- Added missing ThemeProvider component
- Installed next-themes package for theme support
- Resolved module resolution errors

## In Progress

### Frontend: Improved Error Handling (Next Focus)
- [ ] Enhance error message display components
- [ ] Standardize error handling across the app
- [ ] Implement retry mechanisms for failed requests

## Pending Improvements

### Backend: Rate Limiting
- [ ] Implement Twitter API rate limit handling
- [ ] Add rate limit monitoring
- [ ] Implement backoff strategies

### Backend: Database Indexing
- [ ] Review database schema
- [ ] Add appropriate indexes
- [ ] Optimize queries

### General: Documentation
- [ ] Update README with setup instructions
- [ ] Document API endpoints
- [ ] Add configuration guide
- [ ] Document deployment process

### Future: Testing
- [ ] Plan test strategy
- [ ] Set up testing framework
- [ ] Write initial tests

## Change Log

### 2024-03-21
- ✅ Added `.gitignore` for configuration security
- ✅ Implemented APScheduler for robust process management
- ✅ Added real-time updates via SSE (status, matches, logs)
- ✅ Implemented live log streaming with buffer system
- ✅ Added log management endpoints (clear, download)
- ✅ Updated frontend to use SSE instead of polling
- ✅ Enhanced configuration UX with tag inputs
- ✅ Improved dashboard with real-time data and better UX
- ✅ Fixed module import issues (CSS paths, ThemeProvider)

## Frontend (`app/`, `lib/`)

### 1. Real-time Updates (Status & Matches via SSE)
*   **Goal:** Replace polling with Server-Sent Events for instant UI updates.
*   **Steps:**
    *   **Backend:**
        *   [ ] Modify `twitter-monitor-backend/api.py` to add an SSE endpoint (e.g., `/stream`).
        *   [ ] This endpoint should yield events for status changes (running/stopped) and new matches found.
        *   [ ] Integrate SSE updates with the chosen process management approach (e.g., push updates when scheduler status changes or when `monitor.check_tweets` finds a match).
    *   **Frontend:**
        *   [ ] Modify `app/page.tsx`.
        *   [ ] Remove the `setInterval` polling in `useEffect`.
        *   [ ] Use the `EventSource` API to connect to the backend `/stream` endpoint.
        *   [ ] Update `isRunning`, `status`, and `recentMatches` state based on received server events.

### 2. Live Log Streaming
*   **Goal:** Display logs dynamically in the UI instead of static text.
*   **Steps:**
    *   **Backend:**
        *   [ ] Enhance `twitter-monitor-backend/api.py`.
        *   [ ] Option A: Create an SSE endpoint (`/logstream`) that tails the `twitter_monitor.log` file and pushes new lines.
        *   [ ] Option B: Modify the core monitoring logic to push log records to a queue that the SSE endpoint can consume.
        *   [ ] Add API endpoints:
            *   [ ] `POST /logs/clear`: Clears the log file content.
            *   [ ] `GET /logs/download`: Returns the log file for download.
    *   **Frontend:**
        *   [ ] Modify the "Logs" tab in `app/page.tsx`.
        *   [ ] Fetch initial logs using the existing `/logs` endpoint on tab load.
        *   [ ] Connect to the new `/logstream` SSE endpoint (if using Option A) or integrate log events into the main `/stream` (if using Option B).
        *   [ ] Append new log lines to the display area. Maintain scroll position if the user isn't scrolled to the bottom.
        *   [ ] Implement `onClick` handlers for "Clear Logs" and "Download Logs" buttons to call the new backend API endpoints.

### 3. Enhanced Configuration UX (Tag Input)
*   **Goal:** Improve usability for managing lists (usernames, keywords, patterns).
*   **Steps:**
    *   **Frontend:**
        *   [ ] Choose and install a suitable tag input component library (e.g., `react-tag-input`, `react-select` in Creatable mode) or build a simple custom component.
        *   [ ] In `app/page.tsx`, replace the `<Textarea>` elements for "Twitter/X Usernames", "Regex Patterns", and "Keywords" with the chosen tag input component.
        *   [ ] Update the `onChange` handlers (`setConfig`) to correctly handle the array data format provided by the tag input component.
        *   [ ] Ensure the component loads initial values correctly from the `config` state.

### 4. Dynamic Dashboard Data
*   **Goal:** Display accurate, up-to-date information on the dashboard cards.
*   **Steps:**
    *   **Backend:**
        *   [ ] Ensure the `/status` endpoint in `api.py` provides accurate `last_check` timestamp and potentially `uptime` (if feasible with the chosen process manager).
        *   [ ] Consider adding `matches_today` count to the `/status` response.
    *   **Frontend:**
        *   [ ] Modify the "Dashboard" `TabsContent` in `app/page.tsx`.
        *   [ ] Display `status.last_check` formatted using `formatDateTime` from `lib/utils.ts`.
        *   [ ] Display `status.uptime` if available.
        *   [ ] Display `status.matches_today` or calculate it based on the `recentMatches` array's timestamps.
        *   [ ] Use the actual `config.monitoring.usernames.length` instead of the potentially stale length from initial load.

### 5. Improved Error Handling & Feedback
*   **Goal:** Provide clearer error messages and visual feedback during operations.
*   **Steps:**
    *   **Frontend:**
        *   [ ] In `lib/api.ts`, enhance `handleResponse` to extract `errorData.detail` from failed FastAPI responses and include it in the thrown `Error`.
        *   [ ] In `app/page.tsx`, update `catch` blocks for API calls (`toggleMonitoring`, `saveConfiguration`, `refreshData`, etc.) to set the `error` state with the detailed message from the caught error.
        *   [ ] Add loading state variables (e.g., `isSavingConfig`, `isTogglingMonitor`).
        *   [ ] Set loading states to `true` before API calls and `false` in `finally` blocks.
        *   [ ] Disable relevant buttons and show spinners (e.g., using `lucide-react`'s `Loader2`) when loading states are true.

## Backend (`twitter-monitor-backend/`)

### 1. Robust Process Management (Scheduler)
*   **Goal:** Replace fragile `subprocess`/`os.fork` and PID files with a reliable scheduler within the API process.
*   **Steps:**
    *   [ ] Add `APScheduler` or `FastAPI-Scheduler` to `requirements.txt`.
    *   [ ] Modify `api.py`:
        *   [ ] Remove `subprocess`, `os.fork`, PID file logic (`is_monitor_running`, `start_monitor_process`, `stop_monitor_process`).
        *   [ ] Initialize the chosen scheduler.
        *   [ ] Define the monitoring task function (likely wrapping `monitor.check_tweets` or a similar core loop from `twitter_monitor.py`).
        *   [ ] Modify `/start`: Add the monitoring task to the scheduler with the configured interval. Persist job details if needed.
        *   [ ] Modify `/stop`: Remove the monitoring task from the scheduler.
        *   [ ] Modify `/status`: Check the scheduler's state for the monitoring job to determine `is_running`.
    *   [ ] Modify `telegram_bot.py`:
        *   [ ] Remove `os.fork` and PID logic from `start_monitor_command` and `stop_monitor_command`.
        *   [ ] Make these commands call the `POST /start` and `POST /stop` API endpoints using an HTTP client library (like `requests` or `httpx`).

### 2. Rate Limiting Handling
*   **Goal:** Implement proper handling of Twitter API rate limits within the core monitor.
*   **Steps:** (Requires access/modification of `twitter_monitor.py`)
    *   [ ] In the part of the code calling the Twitter API (likely using `tweepy`):
        *   [ ] Add `try...except tweepy.RateLimitError` blocks.
        *   [ ] Log the rate limit error.
        *   [ ] Implement automatic backoff (e.g., `time.sleep()` for the duration indicated by Twitter, or exponential backoff).
    *   [ ] Optionally, check rate limit status headers (`x-rate-limit-*`) after successful requests and log warnings if approaching the limit.

### 3. Logging Enhancements (API & Format)
*   **Goal:** Provide API access to log management and potentially improve log format.
*   **Steps:**
    *   **Backend (`api.py`):**
        *   [ ] Implement `POST /logs/clear`: Truncate or delete `twitter_monitor.log`.
        *   [ ] Implement `GET /logs/download`: Return `twitter_monitor.log` using `FileResponse`.
        *   [ ] (Optional) Configure Python's `logging` module to use a `JSONFormatter` for structured logs. Update the log reading/streaming part if format changes.

### 4. Database Indexing
*   **Goal:** Ensure efficient querying of the matches database.
*   **Steps:** (Requires access/modification of `twitter_monitor.py` or DB schema definition)
    *   [ ] Identify the database schema definition (likely SQLite).
    *   [ ] Ensure the table storing matches (e.g., `matches`) has database indexes created for frequently queried columns, especially `timestamp` and `username`. Example SQL: `CREATE INDEX idx_matches_timestamp ON matches(timestamp);`

### 5. Configuration Management (Security)
*   **Goal:** Prevent accidental committing of sensitive configuration.
*   **Steps:**
    *   [ ] Create/edit `.gitignore` in the `twitter-monitor-backend/` directory.
    *   [ ] Add `config.json` to the `.gitignore` file.
    *   [ ] Add `.env` to the `.gitignore` file.
    *   [ ] Verify that `config.py` correctly loads defaults and prioritizes environment variables over `config.json`.

## General

### 1. Documentation (`README.md`)
*   **Goal:** Provide comprehensive setup and usage instructions.
*   **Steps:**
    *   [ ] Update the root `README.md`.
    *   [ ] Add **Backend Setup** section: Python version, virtual environments, `pip install -r twitter-monitor-backend/requirements.txt`, necessary environment variables (`TWITTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, etc.), how to run the API (`uvicorn twitter-monitor-backend.api:app --reload --port 8000`).
    *   [ ] Add **Frontend Setup** section: Node.js/npm prerequisites, `npm install`, `npm run dev`, environment variables (`NEXT_PUBLIC_API_URL`).
    *   [ ] Add **Configuration** section: Explain `config.json` structure and precedence (Env vars > `config.json`).
    *   [ ] Add **Usage** section: Briefly describe the Web UI tabs and available Telegram Bot commands.
    *   [ ] Add **Process Management** section explaining the chosen approach (e.g., APScheduler).

### 2. Testing (Future)
*   **Goal:** Implement automated tests for reliability.
*   **Steps:** (To be implemented after core features are stable)
    *   [ ] **Backend:** Add unit tests (`pytest`) for API endpoints, configuration loading, and core monitor logic (requires mocking external APIs/DB).
    *   [ ] **Frontend:** Add component tests (`@testing-library/react`) and potentially end-to-end tests (`Cypress`, `Playwright`).

---

*Log: Created IMPROVEMENTS.md outlining the plan.* 