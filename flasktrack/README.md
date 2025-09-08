# flasktrack

A Flask application

## Prerequisites

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management and [just](https://github.com/casey/just) for task running.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install just
cargo install just  # or see https://github.com/casey/just#installation
```

## Quick Start

```bash
# Set up everything for development
just install

# Run the development server
just run
```

Visit `http://localhost:5000` to see your application.

## Project Structure

```
flasktrack/
├── app/                    # Application package
│   ├── controllers/        # Route handlers (Rails-style)
│   ├── models/            # Database models
│   ├── forms/             # WTForms
│   ├── views/             # HTML templates
│   ├── static/            # CSS, JS, images
│   └── config.py          # Configuration
├── migrations/            # Database migrations
├── tests/                 # Test suite
├── .env.example          # Environment variables template
└── run.py                # Application entry point
```

## Features

- User authentication (login, register, logout)
- Database migrations with Flask-Migrate
- Form validation with Flask-WTF
- Password hashing with Flask-Bcrypt
- CSRF protection
- Responsive design

## Common Tasks

```bash
# Show all available commands
just

# Run tests
just test

# Run tests with coverage
just test-cov

# Format and lint code
just format
just lint

# Database migrations
just migrate "Add user table"
just upgrade

# Open Flask shell
just shell

# Clean up cache files
just clean
```

## Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

## Built with FlaskTrack

This project was scaffolded with [FlaskTrack](https://github.com/yourusername/flasktrack), a Rails-inspired Flask framework.