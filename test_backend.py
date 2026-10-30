import unittest, tempfile, subprocess, os, sys, json, urllib.request, urllib.error, time, socket
from pathlib import Path
class Persistence(unittest.TestCase):
 def test_lifecycle(self):
  with tempfile.TemporaryDirectory() as d:
   with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
   def start():
    p=subprocess.Popen([sys.executable,'server.py','--port',str(port)],env={**os.environ,'TRACKER_DATA_DIR':d},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(100):
     try:call();return p
     except OSError:time.sleep(.03)
    p.terminate();raise RuntimeError('Startup failed')
   def call(path='/api/state',data=None):
    req=urllib.request.Request(f'http://127.0.0.1:{port}'+path,data=json.dumps(data).encode() if data is not None else None,method='PUT' if data is not None else 'GET')
    with urllib.request.urlopen(req) as r:return json.load(r)
   p=start()
   try:
    self.assertIsNone(call()['data'])
    value={'rows':[{'subject':'Physics','hy':'92'}],'notes':'Remember this'}
    self.assertEqual(call(data={'revision':0,'data':value})['revision'],1)
    with self.assertRaises(urllib.error.HTTPError) as e:call(data={'revision':0,'data':value})
    self.assertEqual(e.exception.code,409)
    with self.assertRaises(urllib.error.HTTPError) as e:call(data={'revision':1,'data':{}})
    self.assertEqual(e.exception.code,400)
    self.assertEqual(call('/api/revision/1'),value)
    p.terminate();p.wait();p=start()
    self.assertEqual(call()['data'],value)
    subprocess.run([sys.executable,'server.py','--backup',d+'/backup.sqlite3'],env={**os.environ,'TRACKER_DATA_DIR':d},check=True,stdout=subprocess.DEVNULL)
    self.assertTrue(Path(d+'/backup.sqlite3').exists())
   finally:p.terminate();p.wait()
if __name__=='__main__':unittest.main()
