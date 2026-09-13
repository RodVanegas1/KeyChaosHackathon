import os
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database.connection import get_db_connection
from beany.router import router as beany_router
app=FastAPI(title='Bancoagrícola - Beany Backend',version='2.2.0')
orig=[x.strip() for x in os.getenv('ALLOWED_ORIGINS','*').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=orig,allow_credentials=False,allow_methods=['*'],allow_headers=['*'])
app.include_router(beany_router,prefix='/api/beany',tags=['Beany'])
@app.get('/')
def root(): return {'status':'ok','service':'Bancoagrícola - Beany Backend','version':'2.2.0'}
@app.get('/health')
def health():
 c=get_db_connection()
 if not c: raise HTTPException(503,'API activa, pero MySQL no está disponible.')
 try:
  cur=c.cursor(); cur.execute('SELECT 1'); cur.fetchone(); return {'status':'ok','database':'connected'}
 finally: cur.close(); c.close()
