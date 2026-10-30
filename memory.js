window.memoryStore = (() => {
  let revision=0, pending=null, busy=false, blocked=false;
  const status=document.createElement('div');
  status.setAttribute('role','status');
  status.style.cssText='position:fixed;bottom:12px;right:12px;z-index:99999;background:#172b28;color:white;padding:12px 18px;border-radius:12px;font:14px system-ui;max-width:350px';
  document.body.append(status);
  function say(t){status.textContent=t;}
  async function request(url,options){return fetch(url,{...options,signal:AbortSignal.timeout(10000)});}
  async function flush(){
    if(busy || blocked || pending===null)return;
    busy=true; const data=pending;
    try{
      say('Saving…');
      const r=await request('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,data:JSON.parse(data)})});
      if(r.status===409){blocked=true; say('Another tab saved newer changes. Export your work before reloading to resolve the conflict.');return;}
      if(!r.ok)throw Error('Save failed');
      revision=(await r.json()).revision;
      if(pending===data){pending=null;localStorage.removeItem('trackerPending');}
      say('Saved to disk ✓');
    }catch(e){say('Server unavailable — changes kept in this browser; retrying.');}
    finally{busy=false;}
  }
  setInterval(flush,2000);
  addEventListener('beforeunload',e=>{if(pending!==null){e.preventDefault();e.returnValue='';}});
  return {
    async open(){
      const r=await request('/api/state'); if(!r.ok)throw Error('Cannot read saved state');
      const s=await r.json();revision=s.revision;say('Memory connected');
      const cached=localStorage.getItem('trackerPending');
      if(cached){const c=JSON.parse(cached);if(c.revision!==revision){blocked=true;say('Unsynced work recovered. Export it before reloading; newer server data also exists.');return c.data;}pending=c.data;return c.data;}
      return s.data===null?null:JSON.stringify(s.data);
    },
    save(state){pending=JSON.stringify(state);localStorage.setItem('trackerPending',JSON.stringify({revision,data:pending}));say('Changes queued');flush();}
  };
})();
