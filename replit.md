# MeuDANFe XML Downloader

## Overview

This is a Python Flask web application that automates the bulk download of XML invoices from MeuDANFe.com.br. The application provides a web interface where users can input invoice keys and track the download progress in real-time through a background processing system.

## System Architecture

### Frontend Architecture
- **Framework**: Flask with Jinja2 templating
- **UI Framework**: Bootstrap 5 with dark theme
- **Styling**: Custom CSS with hover effects and animations
- **JavaScript**: Vanilla JavaScript for real-time validation and progress tracking
- **Icons**: Font Awesome 6.0

### Backend Architecture
- **Web Framework**: Flask (Python 3.11)
- **WSGI Server**: Gunicorn for production deployment
- **Web Automation**: Selenium WebDriver with Chrome (headless mode)
- **Background Processing**: Python threading for concurrent downloads
- **Session Management**: Flask sessions with configurable secret key

### Data Storage
- **File System**: Local storage for downloaded XML files in `/downloads` directory
- **In-Memory**: Job tracking using Python dictionaries with thread-safe locks
- **Database Ready**: PostgreSQL configured in environment but not actively used (Drizzle ORM can be added later)

## Key Components

### 1. Web Interface (`app.py`)
- **Main Application**: Flask app with route handlers
- **Job Management**: `DownloadJob` class for tracking download progress
- **Thread Safety**: Mutex locks for concurrent job access
- **Real-time Updates**: AJAX endpoints for progress monitoring

### 2. Automation Engine (`automation.py`)
- **Web Scraping**: Selenium WebDriver for automated browser interaction
- **Download Management**: Handles file downloads with proper directory structure
- **Error Handling**: Comprehensive exception handling for web automation failures
- **User Agent Spoofing**: Mimics real browser behavior to avoid detection

### 3. Frontend Components
- **Main Form** (`templates/index.html`): Invoice key input with real-time validation
- **Progress Tracker** (`templates/download.html`): Real-time download progress monitoring
- **Validation System** (`static/js/main.js`): Client-side invoice key validation (44-digit format)

## Data Flow

1. **User Input**: User pastes invoice keys into the web form
2. **Validation**: Client-side JavaScript validates 44-digit invoice key format
3. **Job Creation**: Server creates a new download job with unique ID
4. **Background Processing**: Threading system processes downloads concurrently
5. **Progress Updates**: Real-time AJAX calls update progress bar and statistics
6. **File Management**: Downloaded XMLs are organized in the `/downloads` directory
7. **Completion**: Users can download a ZIP file containing all successful downloads

## External Dependencies

### Python Packages
- **Flask**: Web framework and templating
- **Selenium**: Web automation and browser control
- **Requests**: HTTP client for API calls
- **Gunicorn**: Production WSGI server
- **psycopg2-binary**: PostgreSQL adapter (configured but not actively used)

### System Dependencies
- **Chrome/Chromium**: Browser for Selenium automation
- **GeckoDriver**: WebDriver for Firefox (backup option)
- **PostgreSQL**: Database system (available but not implemented)

### CDN Dependencies
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome 6**: Icon library

## Deployment Strategy

### Development Environment
- **Runtime**: Python 3.11 with Nix package management
- **Server**: Flask development server with auto-reload
- **Port**: 5000 with automatic port forwarding

### Production Environment
- **Deployment Target**: Autoscale deployment on Replit
- **WSGI Server**: Gunicorn with bind to 0.0.0.0:5000
- **Process Management**: Gunicorn handles multiple worker processes
- **Static Files**: Served directly by Flask (suitable for small-scale deployment)

### Configuration
- **Environment Variables**: Session secret key configurable via `SESSION_SECRET`
- **File Permissions**: Downloads directory auto-created with proper permissions
- **Browser Options**: Headless Chrome with security and performance optimizations

## Changelog
- June 19, 2025: Initial setup with Flask web application
- June 19, 2025: Implemented Selenium automation with Chrome WebDriver
- June 19, 2025: Added comprehensive logging system for debugging
- June 19, 2025: Fixed Chrome stability issues and WebDriver crashes
- June 19, 2025: Added individual file download capability (non-ZIP)
- June 19, 2025: Implemented fresh driver instances per download to prevent crashes
- June 19, 2025: **FULLY FUNCTIONAL** - Successfully tested with real invoice key, automation working perfectly
- June 19, 2025: Enhanced XML extraction with multiple detection strategies for meudanfe.com.br

## User Preferences

Preferred communication style: Simple, everyday language.