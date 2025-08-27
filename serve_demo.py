#!/usr/bin/env python3
"""
Simple HTTP server to demonstrate the published app in browsers
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def print_colored(message: str, color: str = Colors.NC, emoji: str = ""):
    print(f"{color}{emoji} {message}{Colors.NC}")

def serve_demo(port=8000):
    """Serve the demo HTML file"""
    
    # Check if demo.html exists
    demo_path = Path("sample-app/demo.html")
    if not demo_path.exists():
        print_colored("Demo HTML file not found!", Colors.RED, "❌")
        print_colored("Make sure sample-app/demo.html exists", Colors.YELLOW, "⚠️")
        return False
    
    # Change to sample-app directory to serve files
    if Path("sample-app").exists():
        os.chdir("sample-app")
    elif not Path("demo.html").exists():
        print_colored("Run this script from the workshop root directory", Colors.RED, "❌")
        return False
    
    print_colored("LocalStack Workshop Demo Server", Colors.BLUE, "🌐")
    print("=" * 50)
    print_colored(f"Starting HTTP server on port {port}...", Colors.BLUE, "🚀")
    print_colored(f"Demo URL: http://localhost:{port}/demo.html", Colors.GREEN, "🔗")
    print_colored("Press Ctrl+C to stop the server", Colors.YELLOW, "ℹ️")
    print("=" * 50)
    
    # Try to open browser automatically
    try:
        webbrowser.open(f'http://localhost:{port}/demo.html')
        print_colored("Opening demo in your default browser...", Colors.GREEN, "🌍")
    except Exception as e:
        print_colored("Could not auto-open browser. Please navigate to the URL above.", Colors.YELLOW, "⚠️")
    
    # Start the server
    try:
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print_colored("\nDemo server stopped", Colors.YELLOW, "⏹️")
        return True
    except OSError as e:
        if "Address already in use" in str(e):
            print_colored(f"Port {port} is already in use. Try a different port:", Colors.RED, "❌")
            print_colored(f"python3 serve_demo.py --port {port + 1}", Colors.BLUE, "💡")
        else:
            print_colored(f"Server error: {e}", Colors.RED, "❌")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Serve LocalStack workshop demo in browser')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Port to serve on (default: 8000)')
    
    args = parser.parse_args()
    
    serve_demo(args.port)

if __name__ == "__main__":
    main()