"""Private single-user tracker. Standard library only."""
import json, os, sqlite3, argparse, base64, hmac
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('TRACKER_DATA_DIR',ROOT/'data'))
DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'tracker.sqlite3'
def connect():
    db=sqlite3.connect(DB,timeout=15)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS revisions (id INTEGER PRIMARY KEY AUTOINCREMENT, saved_at TEXT DEFAULT CURRENT_TIMESTAMP, data TEXT NOT NULL)')
    return db
with connect() as db: pass
class Handler(BaseHTTPRequestHandler):
    def reply(self,code,data,kind='application/json'):
        body=json.dumps(data).encode() if kind=='application/json' else data
        self.send_response(code); self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY')
        self.end_headers();self.wfile.write(body)
    def allowed(self):
        host=self.headers.get('Host','')
        expected=f'127.0.0.1:{self.server.server_port}'
        public_host=os.environ.get('RENDER_EXTERNAL_HOSTNAME','')
        if host not in (expected,f'localhost:{self.server.server_port}',public_host):
            self.reply(403,{'error':'Local access only'});return False
        origin=self.headers.get('Origin')
        if origin and origin not in (f'http://{host}',f'https://{host}'):
            self.reply(403,{'error':'Cross-origin access denied'});return False
        password=os.environ.get('TRACKER_PASSWORD')
        if password:
            try:
                scheme,encoded=self.headers.get('Authorization','').split(' ',1)
                username,provided=base64.b64decode(encoded,validate=True).decode().split(':',1)
                valid=scheme.lower()=='basic' and username=='arifin' and hmac.compare_digest(provided.encode(),password.encode())
            except (ValueError,UnicodeError):valid=False
            if not valid:
                self.send_response(401);self.send_header('WWW-Authenticate','Basic realm="Personal study tracker", charset="UTF-8"');self.send_header('Content-Length','0');self.end_headers();return False
        return True
    def do_GET(self):
        if not self.allowed():return
        if self.path=='/api/state':
            with connect() as db: row=db.execute('SELECT id,data FROM revisions ORDER BY id DESC LIMIT 1').fetchone()
            return self.reply(200,{'revision':row[0] if row else 0,'data':json.loads(row[1]) if row else None})
        if self.path=='/api/history':
            with connect() as db: rows=db.execute('SELECT id,saved_at FROM revisions ORDER BY id DESC LIMIT 100').fetchall()
            return self.reply(200,[{'revision':r[0],'saved_at':r[1]} for r in rows])
        if self.path.startswith('/api/revision/'):
            try: n=int(self.path.rsplit('/',1)[1])
            except ValueError:return self.reply(400,{'error':'Invalid revision'})
            with connect() as db: row=db.execute('SELECT data FROM revisions WHERE id=?',(n,)).fetchone()
            return self.reply(200,json.loads(row[0])) if row else self.reply(404,{'error':'Not found'})
        files={'/':('index.html','text/html; charset=utf-8'),'/memory.js':('memory.js','application/javascript')}
        if self.path not in files:return self.reply(404,{'error':'Not found'})
        name,kind=files[self.path];self.reply(200,(ROOT/name).read_bytes(),kind)
    def do_PUT(self):
        if not self.allowed():return
        if self.path!='/api/state':return self.reply(404,{'error':'Not found'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>5_000_000:return self.reply(413,{'error':'Invalid size'})
            obj=json.loads(self.rfile.read(n));data=obj['data'];rev=obj['revision']
            if type(rev)!=int or not isinstance(data,dict) or not isinstance(data.get('rows'),list) or not all(isinstance(r,dict) and isinstance(r.get('subject'),str) for r in data['rows']):raise ValueError()
            encoded=json.dumps(data,allow_nan=False)
        except (ValueError,KeyError,TypeError):return self.reply(400,{'error':'Invalid tracker data'})
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT id,data FROM revisions ORDER BY id DESC LIMIT 1').fetchone()
            current=row[0] if row else 0
            if rev!=current:return self.reply(409,{'error':'Revision conflict','revision':current})
            if row and row[1]==encoded:return self.reply(200,{'revision':current})
            cursor=db.execute('INSERT INTO revisions(data) VALUES (?)',(encoded,));new=cursor.lastrowid
        self.reply(200,{'revision':new})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','8000')));parser.add_argument('--backup',type=Path)
    args=parser.parse_args()
    if args.backup:
        with connect() as source, sqlite3.connect(args.backup) as target:source.backup(target)
        print('Backup complete:',args.backup)
    else:
        print(f'Tracker running on port {args.port}',flush=True)
        host='0.0.0.0' if os.environ.get('RENDER_EXTERNAL_HOSTNAME') else '127.0.0.1'
        if host=='0.0.0.0' and not os.environ.get('TRACKER_PASSWORD'):
            raise SystemExit('TRACKER_PASSWORD is required for hosted deployment')
        ThreadingHTTPServer((host,args.port),Handler).serve_forever()
