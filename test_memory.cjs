const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 for(const protocol of ['file:','https:']){
  const values=new Map();const elements=[];
  const context={window:{},location:{protocol},document:{createElement:()=>({style:{},setAttribute(){}}),body:{append(e){elements.push(e);},prepend(){}}},localStorage:{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)},setInterval(){},addEventListener(){},AbortSignal,fetch:async()=>({ok:false})};
  vm.runInNewContext(fs.readFileSync('memory.js','utf8'),context);
  assert.equal(await context.window.memoryStore.open(),null);
  context.window.memoryStore.save({rows:[{subject:'Physics'}]});
  assert.equal(JSON.parse(values.get('trackerOffline')).rows[0].subject,'Physics');
  assert.match(elements[0].textContent,/Saved in this browser/);
 }
 console.log('PASS: standalone file and unavailable-server fallback save data');
})();
