# XML Downloader

## Overview

This is a Python Flask web application that automates the bulk download of XML invoice files. The application provides both a web interface and a complete REST API where users can input invoice keys and track the download progress in real-time through a background processing system.

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
- June 19, 2025: Enhanced XML extraction with multiple detection strategies
- June 19, 2025: **PRODUCTION READY** - System validated with authentic XML downloads, interface fully operational
- June 19, 2025: **API INTEGRATION COMPLETE** - Added comprehensive REST API with full CRUD operations
- June 19, 2025: **FULL SYSTEM READY** - Web interface + REST API + Python client + complete documentation
- June 19, 2025: **GENERIC SYSTEM** - Removed all specific site references, created API documentation page
- June 19, 2025: **INTERFACE CLEANED** - Removed all site-specific references from user interface and documentation
- June 19, 2025: **DANFE GENERATION ADDED** - Implemented PDF DANFE generation from XML using ReportLab library
- June 19, 2025: **COMPLETE SAAS PLATFORM** - Implemented full authentication system with user registration, login, trial periods
- June 19, 2025: **ASAAS PAYMENT INTEGRATION** - Integrated PIX payment system via Asaas API for automatic billing
- June 19, 2025: **PRICING STRUCTURE UPDATED** - XML download R$0.10, DANFE generation FREE, Labels module R$49.90
- June 19, 2025: **PREMIUM UI REDESIGN** - Implemented sophisticated silver gradient design with glass morphism effects
- June 19, 2025: **STORYTELLING LANDING PAGE** - Created conversion-focused landing page with success stories and problem/solution narrative
- June 19, 2025: **COMPLETE AUTHENTICATION SYSTEM** - Implemented Google OAuth, password reset via email, modern login/registration templates
- June 19, 2025: **FULL UI MODERNIZATION** - Reestilized all internal pages with consistent modern design (Purple #8A05BE theme)
- June 19, 2025: **UNIFIED DESIGN SYSTEM** - All pages now use Inter font, modern cards, consistent navigation, and professional styling
- June 19, 2025: **SIDEBAR NAVIGATION COMPLETE** - Implemented unified sidebar menu across all templates with functional routing to all system modules
- June 19, 2025: **DOWNLOAD SYSTEM FULLY OPERATIONAL** - Confirmed XML download working (4750 bytes valid XML from REAL SINALIZACAO), fixed interface to show download buttons after completion, added direct file serving route
- June 19, 2025: **DANFE SEFAZ OFFICIAL LAYOUT IMPLEMENTED** - Integrated brazilfiscalreport library for SEFAZ-compliant DANFE generation, replaced custom ReportLab implementation with official NFe model 55 layout
- June 19, 2025: **STRIPE PAYMENT SYSTEM FULLY IMPLEMENTED** - Complete credit-based billing system with live Stripe integration, checkout sessions, webhooks, automatic charging per XML download, modern payment interface with starter/professional/enterprise packages
- June 19, 2025: **PRODUCTION READINESS FIXES** - Corrected Flask application context issues preventing XML database registration, implemented dual XML storage (XMLFile + ImportedXML), fixed JavaScript errors in templates, unified label generation system with professional transport labels based on CrossWMS model
- June 20, 2025: **SYSTEM CONTEXT FIXES COMPLETE** - Systematically corrected Flask application context management in all threaded operations, fixed XMLFile and ImportedXML database registration, corrected dashboard recent activity display, implemented proper charging system with trial period support, verified XML download and database storage working correctly
- June 20, 2025: **COMPREHENSIVE DATABASE EXPANSION** - Enhanced ImportedXML model with complete NFe data storage including emission date, total value, gross weight, volumes quantity, complete sender/recipient information (name, city, state, address, CEP), implemented advanced filtering system for easy XML search by date ranges, locations, weight, and value ranges

## User Preferences

Preferred communication style: Simple, everyday language.

## Current Pricing Structure
- Download XML: R$ 0,10 per file (web + API)
- DANFE Generation: FREE (always included)
- Labels Module: R$ 49,90 (one-time access fee)
- Minimum recharge: R$ 19,90
- 7-day free trial for all new users

## System Architecture Updates
- **Authentication**: Flask-Login with PostgreSQL user management
- **Payment Processing**: Asaas PIX integration with automatic webhook processing
- **UI Framework**: Premium glass morphism design with silver gradients
- **Pricing Logic**: Per-use billing with free DANFE generation
- **Trial System**: 7-day free access to all features
- **Admin Panel**: User management and pricing configuration