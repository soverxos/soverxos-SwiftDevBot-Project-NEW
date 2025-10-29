"""
WebPanel Service - Dynamic Web Interface for SwiftDevBot
Integrates with Module Host to display module-generated web tabs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, os, sys
from pathlib import Path
import asyncio
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "Systems"))

from Systems.core.logging.logger import get_logger, init_logging

app = FastAPI(title="webpanel", description="SwiftDevBot Web Panel with Module Integration")
app.mount("/static", StaticFiles(directory="Systems/SysModules/webpanel/frontend"), name="static")

logger = get_logger("webpanel", "service", "webpanel")

# Module Host connection
MODULE_HOST_URL = "http://localhost:8104"

class ModuleHostClient:
    """Client for communicating with Module Host"""

    def __init__(self, host_url: str):
        self.host_url = host_url.rstrip('/')

    async def get_modules(self) -> dict:
        """Get all loaded modules from Module Host"""
        try:
            response = requests.get(f"{self.host_url}/modules", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get modules: {response.status_code}")
                return {"modules": {}, "total": 0}
        except Exception as e:
            logger.error(f"Error connecting to Module Host: {e}")
            return {"modules": {}, "total": 0}

    async def get_module_web_tabs(self, module_name: str) -> list:
        """Get web tabs for a specific module"""
        try:
            # Get module info
            response = requests.get(f"{self.host_url}/modules/{module_name}", timeout=5)
            if response.status_code == 200:
                module_data = response.json()
                web_tabs = module_data.get("web_tabs", [])
                return [{"module": module_name, "tabs": web_tabs}]
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting web tabs for {module_name}: {e}")
            return []

    async def get_all_web_tabs(self) -> list:
        """Get all web tabs from all modules"""
        modules_data = await self.get_modules()
        all_tabs = []

        for module_name in modules_data.get("modules", {}):
            tabs = await self.get_module_web_tabs(module_name)
            all_tabs.extend(tabs)

        return all_tabs

# Global client
module_client = ModuleHostClient(MODULE_HOST_URL)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await init_logging()
    logger.info("WebPanel starting up...")

    # Test connection to Module Host
    test_response = await module_client.get_modules()
    if test_response.get("total", 0) >= 0:
        logger.info(f"Connected to Module Host, {test_response.get('total', 0)} modules available")
    else:
        logger.warning("Could not connect to Module Host")

@app.get("/health")
async def health():
    """Health check endpoint"""
    modules_info = await module_client.get_modules()
    return {
        "status": "ok",
        "service": "webpanel",
        "module_host_connected": modules_info.get("total", -1) >= 0,
        "modules_available": modules_info.get("total", 0)
    }

@app.get("/api/modules")
async def get_modules_api():
    """API endpoint to get modules information"""
    return await module_client.get_modules()

@app.get("/api/modules/{module_name}/tabs")
async def get_module_tabs_api(module_name: str):
    """API endpoint to get web tabs for a module"""
    tabs = await module_client.get_module_web_tabs(module_name)
    if tabs:
        return {"tabs": tabs[0]["tabs"]}
    else:
        raise HTTPException(status_code=404, detail="Module not found or has no web tabs")

@app.get("/profile", response_class=HTMLResponse)
async def profile():
    """Main profile page with module web tabs"""
    modules_data = await module_client.get_modules()
    modules = modules_data.get("modules", {})

    # Build navigation tabs
    nav_tabs = []
    tab_contents = []

    # Add system info tab
    nav_tabs.append('<button class="tab-button active" onclick="openTab(event, \'system-info\')">🏠 System</button>')
    tab_contents.append(f'''
        <div id="system-info" class="tab-content active">
            <h2>🏠 SwiftDevBot System Info</h2>
            <div class="system-stats">
                <div class="stat-card">
                    <h3>🧩 Modules Loaded</h3>
                    <div class="stat-number">{len(modules)}</div>
                </div>
                <div class="stat-card">
                    <h3>⚙️ Services</h3>
                    <div class="stat-number">7</div>
                </div>
                <div class="stat-card">
                    <h3>💾 Databases</h3>
                    <div class="stat-number">3</div>
                </div>
            </div>
        </div>
    ''')

    # Add module tabs
    for module_name, module_info in modules.items():
        if module_info.get("web_tabs"):
            tab_id = f"module-{module_name}"
            nav_tabs.append(f'<button class="tab-button" onclick="openTab(event, \'{tab_id}\')">{module_info.get("name", module_name)}</button>')

            # Generate tab content with module web tabs
            tab_content = f'<div id="{tab_id}" class="tab-content"><h2>{module_info.get("name", module_name)}</h2>'

            # For now, just show module info - in future this would call module's web_tab handler
            tab_content += f'''
                <div class="module-info">
                    <p><strong>Version:</strong> {module_info.get("version", "N/A")}</p>
                    <p><strong>Description:</strong> {module_info.get("description", "No description")}</p>
                    <p><strong>Commands:</strong> {", ".join(module_info.get("commands", []))}</p>
                    <p><strong>Events:</strong> {", ".join(module_info.get("events", []))}</p>
                    <p><strong>Web Tabs:</strong> {", ".join(module_info.get("web_tabs", []))}</p>
                </div>
            '''

            tab_content += '</div>'
            tab_contents.append(tab_content)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SwiftDevBot Web Panel</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}

            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}

            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}

            .tab-bar {{
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 0 20px;
                display: flex;
                gap: 5px;
                overflow-x: auto;
            }}

            .tab-button {{
                background: none;
                border: none;
                padding: 15px 20px;
                cursor: pointer;
                border-radius: 8px 8px 0 0;
                transition: all 0.3s;
                white-space: nowrap;
            }}

            .tab-button:hover {{
                background: #e9ecef;
            }}

            .tab-button.active {{
                background: white;
                border-bottom: 3px solid #007bff;
                font-weight: bold;
            }}

            .tab-content {{
                display: none;
                padding: 30px;
                min-height: 400px;
            }}

            .tab-content.active {{
                display: block;
            }}

            .system-stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}

            .stat-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }}

            .stat-card h3 {{
                margin: 0 0 10px 0;
                color: #666;
                font-size: 0.9em;
            }}

            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #007bff;
            }}

            .module-info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-top: 20px;
            }}

            .module-info p {{
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 SwiftDevBot</h1>
                <p>Modular Telegram Bot Platform</p>
            </div>

            <div class="tab-bar">
                {"".join(nav_tabs)}
            </div>

            {"".join(tab_contents)}
        </div>

        <script>
            function openTab(evt, tabName) {{
                var i, tabcontent, tabbuttons;

                // Hide all tab contents
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].style.display = "none";
                }}

                // Remove active class from all tab buttons
                tabbuttons = document.getElementsByClassName("tab-button");
                for (i = 0; i < tabbuttons.length; i++) {{
                    tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
                }}

                // Show the current tab and add active class
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }}
        </script>
    </body>
    </html>
    """

    return html

@app.get("/api/health")
async def api_health():
    """JSON API health endpoint"""
    modules_data = await module_client.get_modules()
    return {
        "status": "healthy",
        "webpanel": "running",
        "module_host_connection": "ok" if modules_data.get("total", -1) >= 0 else "failed",
        "modules_count": modules_data.get("total", 0)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
