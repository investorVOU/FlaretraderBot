# Flare Crypto Dashboard

## Overview

This is a Flask-based cryptocurrency trading dashboard focused on the Flare Network ecosystem. The application provides a comprehensive platform for tracking portfolio performance, executing mock trades, and interacting with a chatbot for trading commands. It features a dark-themed UI built with Bootstrap and includes real-time data visualization capabilities.

**Status**: Fully functional chat-based trading interface with AI bot as primary interaction method.

## Recent Changes

**July 21, 2025**
- ✓ Redesigned as chat-first trading interface per user request
- ✓ AI chatbot is now the primary way users interact with the system
- ✓ Dashboard features integrated chat interface with quick command buttons
- ✓ Enhanced chatbot with wrap/unwrap functionality for FLR ↔ WFLR
- ✓ Added contextual responses for market info and trading help
- ✓ Simplified navigation to focus on AI Trading as main interface
- ✓ Portfolio and market data shown as sidebar to chat interface
- ✓ All trading operations (buy/sell/swap/wrap) accessible via natural language
- ✓ Mock data supports full Flare Network ecosystem trading simulation

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a traditional Flask MVC architecture with the following key components:

- **Backend**: Python Flask web framework with SQLAlchemy ORM
- **Database**: SQLite (default) with support for PostgreSQL via environment configuration
- **Frontend**: Server-side rendered HTML templates using Jinja2, enhanced with Bootstrap 5 and Chart.js
- **Data Layer**: SQLAlchemy models for database interactions
- **Mock Trading**: Simulated trading system with portfolio tracking

## Key Components

### Database Models (models.py)
- **Token**: Stores cryptocurrency information (symbol, name, price, market cap, volume, 24h change)
- **Portfolio**: Tracks user holdings (token symbol, balance, average buy price)
- **Trade**: Records trading history (buy/sell/swap operations with timestamps)
- **ChatMessage**: Stores chatbot interactions and executed trades

### Core Application Structure
- **app.py**: Flask application initialization, database configuration, and middleware setup
- **routes.py**: Web route handlers for dashboard, trading, portfolio, and chat interfaces
- **chatbot.py**: Natural language processing for trading commands using regex patterns
- **mock_data.py**: Database initialization with sample data and mock trading execution

### Frontend Components
- **Dashboard**: Portfolio overview with charts and market data
- **Trading Interface**: Tabbed interface for buy/sell/swap operations
- **Portfolio View**: Detailed holdings analysis with P&L calculations
- **Chat Interface**: Conversational trading bot with command suggestions

## Data Flow

1. **Initialization**: App starts, creates database tables, and populates with mock data
2. **Dashboard**: Displays real-time portfolio value, token prices, and recent trades
3. **Trading**: Users submit trade orders through forms or chat commands
4. **Mock Execution**: Trades are simulated, portfolio balances updated, and trade history recorded
5. **Real-time Updates**: Frontend JavaScript fetches updated data for charts and displays

## External Dependencies

### Backend Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Werkzeug**: WSGI utilities and proxy handling

### Frontend Dependencies
- **Bootstrap 5**: UI framework and responsive design
- **Chart.js**: Data visualization and interactive charts
- **Font Awesome**: Icon library for enhanced UI

### Development Tools
- **SQLite**: Default database for development
- **Python Logging**: Application monitoring and debugging

## Deployment Strategy

The application is configured for flexible deployment:

### Environment Configuration
- **DATABASE_URL**: Configurable database connection (defaults to SQLite)
- **SESSION_SECRET**: Secure session management (defaults to development key)
- **ProxyFix**: Handles reverse proxy headers for production deployment

### Development Setup
- Flask development server on port 5000
- SQLite database with automatic table creation
- Debug mode enabled for development
- Mock data initialization on first run

### Production Considerations
- Environment variables for secure configuration
- Database connection pooling with health checks
- Proxy middleware for load balancer compatibility
- Logging configuration for monitoring

The application architecture supports easy scaling and can be deployed on platforms like Heroku, Railway, or traditional VPS environments with minimal configuration changes.