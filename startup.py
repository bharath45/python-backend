#!/usr/bin/env python3
"""
Startup script for Azure App Service
"""
import os
from app import app

if __name__ == "__main__":
    # Get port from environment variable (Azure sets this)
    port = int(os.environ.get('PORT', 5001))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)
