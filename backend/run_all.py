#!/usr/bin/env python
"""
Unified startup script for Autonomous Talent Partner
Starts FastAPI backend and MCP server simultaneously
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure we're in the backend directory
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

def start_fastapi_backend():
    """Start FastAPI backend with Uvicorn"""
    logger.info("🚀 Starting FastAPI Backend on http://127.0.0.1:8000...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
        "--log-level",
        "info"
    ]
    return subprocess.Popen(cmd, cwd=str(backend_dir))

def start_mcp_server():
    """Start MCP server"""
    # Give FastAPI time to start first
    time.sleep(2)
    logger.info("🤖 Starting MCP Server...")
    cmd = [
        sys.executable,
        "mcp_server.py"
    ]
    return subprocess.Popen(cmd, cwd=str(backend_dir))

def main():
    """Start both servers"""
    processes = []
    
    try:
        logger.info("=" * 60)
        logger.info("Autonomous Talent Partner - Unified Server Startup")
        logger.info("=" * 60)
        
        # Start FastAPI backend
        fastapi_process = start_fastapi_backend()
        processes.append(("FastAPI Backend", fastapi_process))
        
        # Start MCP server
        mcp_process = start_mcp_server()
        processes.append(("MCP Server", mcp_process))
        
        logger.info("=" * 60)
        logger.info("✅ All servers started successfully!")
        logger.info("=" * 60)
        logger.info("\n📊 Services Running:")
        logger.info("   • FastAPI Backend: http://127.0.0.1:8000")
        logger.info("   • FastAPI Docs:   http://127.0.0.1:8000/docs")
        logger.info("   • MCP Server:     Ready for connections")
        logger.info("\n💡 Press Ctrl+C to stop all servers\n")
        
        # Keep processes running
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    logger.error(f"❌ {name} process died with exit code {process.returncode}")
                    # Restart it
                    if name == "FastAPI Backend":
                        logger.info(f"🔄 Restarting {name}...")
                        process = start_fastapi_backend()
                    elif name == "MCP Server":
                        logger.info(f"🔄 Restarting {name}...")
                        process = start_mcp_server()
                    
                    # Update process list
                    processes = [(n, p) for n, p in processes if n != name]
                    processes.append((name, process))
                    
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Shutting down all servers...")
        for name, process in processes:
            try:
                logger.info(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"   ✅ {name} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"   Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"   Error stopping {name}: {e}")
        
        logger.info("\n✅ All servers shut down gracefully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        # Kill all processes
        for name, process in processes:
            try:
                process.kill()
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
