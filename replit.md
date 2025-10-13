# XML Downloader

## Overview

This Python Flask web application automates the bulk download of XML invoice files, offering both a web interface and a comprehensive REST API. Its core purpose is to streamline the process of obtaining XML invoices using invoice keys, providing real-time progress tracking through a background processing system. The project aims to reduce manual labor, improve data accuracy, and offer integrated solutions like DANFE generation and customizable transport labels, positioning itself as a comprehensive solution for logistics and financial operations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### UI/UX Decisions
- **Frontend Framework**: Flask with Jinja2 templating.
- **UI Framework**: Bootstrap 5, featuring a dark theme with custom CSS for hover effects and animations.
- **JavaScript**: Vanilla JavaScript for real-time validation and progress tracking.
- **Icons**: Font Awesome 6.0.
- **Visual Design**: Premium glass morphism design with silver gradients and a consistent purple (#8A05BE) branding theme across all internal pages. Utilizes Inter font, modern cards, and consistent navigation.
- **Layout Standards**: All internal pages extend `base.html` with a sidebar navigation, light gray background (#f8f9fa), and a 280px left margin for content.

### Technical Implementations
- **Web Framework**: Flask (Python 3.11).
- **Web Automation**: Selenium WebDriver with headless Chrome for web scraping, including user agent spoofing and robust error handling.
- **Background Processing**: Python threading for concurrent downloads and real-time progress updates via AJAX.
- **API**: Comprehensive REST API (v1.0) for job management, file listing, and downloads, authenticated with a single API key per user. Supports both JSON data and raw XML file retrieval.
- **Authentication**: Flask-Login, Google OAuth, and a 7-day free trial system.
- **Session Management**: Flask sessions with a configurable secret key.
- **Payment Processing**: Stripe for volume-based XML credits and monthly subscriptions for the Labels Module, with webhook integration for recurring payments.
- **Email Processing**: POP3/IMAP email import system for XML attachments, including encryption for credentials and duplicate detection.
- **XML Processing**: Advanced XML parser for Brazilian NFe structure, extracting 19 detailed fields including sender/recipient data, values, and volumes.
- **Label Generation**: Customizable transport label generator (PDF) with multiple layouts (Modern, High Contrast, Transul Professional), dynamic field boundary control, logo integration, QR codes, and multi-volume support.
- **Credit System**: Volume-based pricing for XML downloads, free DANFE generation, and a subscription model for the labels module.
- **Deployment**: Gunicorn for production, with environment-aware performance optimizations for Chrome WebDriver.
- **Security**: Robust security middleware including rate limiting, CSRF protection, admin-only routes, file access validation, and multi-tenant data segregation.
- **User Activity**: Comprehensive logging of user activities (e.g., XML uploaded, label generated) displayed on the dashboard.
- **Automated XML/DANFE Downloader**: `/NotaFiscalBaixador` route that automatically downloads both XML and DANFE files from meudanfe.com.br using Selenium automation. Accepts 44-digit invoice keys and processes downloads in background threads with real-time progress tracking.

### System Design Choices
- **Data Storage**: Local filesystem for XML files (`/downloads`), in-memory job tracking with thread-safe locks. PostgreSQL is configured but not actively used for primary data storage.
- **Modularity**: Separation of concerns into `app.py` (web interface), `automation.py` (automation engine), `xml_processor.py`, `download_service.py`, `email_xml_processor.py`, and various label generator modules.

## External Dependencies

- **Python Packages**:
    - `Flask`: Web framework.
    - `Selenium`: Web automation.
    - `Requests`: HTTP client.
    - `Gunicorn`: Production WSGI server.
    - `psycopg2-binary`: PostgreSQL adapter (configured).
    - `cryptography`: For email password encryption.
    - `Stripe Python library`: For payment processing.
    - `ReportLab`: For PDF generation (labels, DANFE).
    - `brazilfiscalreport`: For SEFAZ-compliant DANFE generation.

- **System Dependencies**:
    - `Chrome/Chromium`: Browser for Selenium automation.
    - `GeckoDriver`: WebDriver for Firefox (backup).

- **CDN Dependencies**:
    - `Bootstrap 5`: UI framework.
    - `Font Awesome 6`: Icon library.