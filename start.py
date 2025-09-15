#!/usr/bin/env python3
"""
Ultra-simple startup script for Railway deployment
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Vriddhi API on port {port}")

    uvicorn.run(
        "app.simple_main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )