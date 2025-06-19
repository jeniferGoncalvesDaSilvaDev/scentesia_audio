# NeuroAudio Processing System

## Overview

The NeuroAudio Processing System is a Streamlit-based web application designed to process audio frequency data from Excel files. The system provides a user-friendly interface for uploading Excel files containing THz frequency data, processing them through a backend API, and displaying results. The application is built with Python and configured for deployment on Replit's autoscale infrastructure.

## System Architecture

The system follows a client-server architecture with the following components:

### Frontend
- **Streamlit Web Application**: Provides the user interface for file uploads and result visualization
- **Session State Management**: Maintains processing status, job IDs, and results across user interactions
- **File Validation**: Client-side validation of Excel files before processing

### Backend Integration
- **FastAPI Backend**: External API service for processing audio data (referenced but not included in this repository)
- **RESTful Communication**: HTTP requests for file upload and processing status checks
- **Asynchronous Processing**: Support for long-running audio processing tasks

## Key Components

### Main Application (`app.py`)
- Streamlit interface configuration with wide layout and custom theming
- File upload and validation workflow
- API communication for processing requests
- Session state management for maintaining user context
- Real-time status updates and result display

### Utility Functions (`utils.py`)
- **Excel File Validation**: Ensures uploaded files contain required THz column
- **Data Validation**: Verifies numeric frequency data integrity
- **File Processing Helpers**: Format file sizes and manage file operations
- **API Configuration**: Dynamic API base URL resolution

### Configuration Files
- **Streamlit Config**: Headless server configuration for deployment
- **Replit Config**: Python 3.11 environment with autoscale deployment
- **Dependencies**: Managed through pyproject.toml with core libraries

## Data Flow

1. **File Upload**: User uploads Excel file through Streamlit interface
2. **Client Validation**: File structure and THz column validated locally
3. **API Submission**: Valid files sent to FastAPI backend with company metadata
4. **Processing**: Backend processes audio frequency data (external service)
5. **Status Polling**: Frontend monitors processing status through API calls
6. **Result Display**: Processed results presented in Streamlit interface

## External Dependencies

### Core Libraries
- **Streamlit 1.46.0+**: Web application framework for interactive interfaces
- **Pandas 2.3.0+**: Data manipulation and Excel file processing
- **Requests 2.32.4+**: HTTP client for API communication
- **OpenPyXL 3.1.5+**: Excel file reading and writing capabilities

### System Dependencies
- **Python 3.11**: Runtime environment with modern language features
- **Nix Package Manager**: Stable 24.05 channel for reproducible builds
- **glibc Locales**: Internationalization support

## Deployment Strategy

### Replit Configuration
- **Autoscale Deployment**: Automatic scaling based on demand
- **Port Configuration**: Streamlit server running on port 5000
- **Workflow Automation**: Parallel task execution for application startup
- **Environment Isolation**: Nix-based package management for consistency

### Production Considerations
- Headless server operation for cloud deployment
- Configurable API endpoints for different environments
- Session state persistence for user experience continuity
- Error handling and connection monitoring for API dependencies

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- June 19, 2025: Initial NeuroAudio Processing System setup
- June 19, 2025: Implemented complete FastAPI backend with audio generation and PDF reporting
- June 19, 2025: Enhanced PDF reports with educational statistics explanations and improved histograms
- June 19, 2025: Added automatic download functionality for both audio and PDF files
- June 19, 2025: Localized interface and reports to Portuguese

## User Preferences

- Language: Portuguese for reports and interface elements
- Download behavior: Automatic downloads directly in browser
- Report content: Educational explanations of statistics in simple terms
- Communication style: Simple, everyday language