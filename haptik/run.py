#!/usr/bin/env python
"""Application entry point."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models.user import User

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return {'db': db, 'User': User}


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )