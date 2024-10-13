from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pesquisa.router_questionario import router as router_quest

app = FastAPI()
app.mount("/static", StaticFiles(directory="pesquisa/static"), name="static")
app.add_middleware(GZipMiddleware)

templates = Jinja2Templates(directory='pesquisa/templates')


app.include_router(router_quest)

@app.get('/test')
def read_root():
    return {'message': 'Olá Mundo!'}


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('base.html', {'request': request})
