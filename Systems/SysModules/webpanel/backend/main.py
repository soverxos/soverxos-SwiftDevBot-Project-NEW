from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, os, glob

app = FastAPI(title="webpanel")
app.mount("/static", StaticFiles(directory="Systems/SysModules/webpanel/frontend"), name="static")

PROFILE_TABS = []  # {title, icon, html}

def load_extensions():
    PROFILE_TABS.clear()
    for tab in glob.glob("Modules/*/web/templates/profile_tab.html"):
        module_id = tab.split(os.sep)[1]
        with open(tab, "r", encoding="utf-8") as f:
            html = f.read()
        PROFILE_TABS.append({"title": module_id.capitalize(), "icon": "🧩", "html": html})

@app.on_event("startup")
async def on_startup():
    load_extensions()

@app.get("/profile", response_class=HTMLResponse)
async def profile():
    base = "<h2>👤 Профиль пользователя</h2>"
    blocks = [f"<section><h3>{t['icon']} {t['title']}</h3>{t['html']}</section>" for t in PROFILE_TABS]
    return base + "\n".join(blocks)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
