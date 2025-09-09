# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

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

Visit `http://localhost:{{ cookiecutter.flask_port }}` to see your application.

## Project Structure

```
{{ cookiecutter.project_slug }}/
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
└── app.py                # Application entry point
```

## Features

- User authentication (login, register, logout)
- **Magic link authentication** - passwordless login via email
  - In development: magic links appear in the terminal
  - In production: magic links are sent via email
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

### Magic Link Authentication

When running locally in development mode, magic links will automatically appear in your terminal instead of being sent via email. This makes it easy to test the authentication flow without setting up an email server.

To configure email for production:
1. Set up your SMTP server details in `.env`
2. Set `FLASK_ENV=production` to disable terminal output
3. Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, and `MAIL_PASSWORD`

## Built with FlaskTrack

This project was scaffolded with [FlaskTrack](https://github.com/yourusername/flasktrack), a Rails-inspired Flask framework.