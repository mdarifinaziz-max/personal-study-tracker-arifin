const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'tracker-ui-'));
 const server=spawn('python3',['server.py','--port','18763'],{env:{...process.env,TRACKER_DATA_DIR:dir,TRACKER_PASSWORD:'',RENDER_EXTERNAL_HOSTNAME:''},stdio:'ignore'});
 let browser;
 try{
  for(let i=0;i<100;i++){try{await fetch('http://127.0.0.1:18763/api/state');break;}catch{await new Promise(r=>setTimeout(r,50));}}
  browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',args:['--no-sandbox']});
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error('BROWSER:',e.message)});
  await page.goto('http://127.0.0.1:18763');await page.waitForSelector('.subject');
  await page.click('.agenda-toggle');assert(await page.locator('#agendaShell').evaluate(e=>e.classList.contains('open')));
  await page.click('.routine-toggle');assert(await page.locator('#routineWrap').evaluate(e=>e.classList.contains('open')));
  const count=await page.locator('.subject').count();
  await page.getByRole('button',{name:'+ Add subject',exact:true}).click();assert.equal(await page.locator('.subject').count(),count+1);
  await page.locator('.subject-name').last().fill('Browser regression');
  const wasOpen=await page.locator('.syllabus-panel').first().evaluate(e=>e.classList.contains('open'));await page.locator('.syllabus-launch').first().click();await page.waitForFunction(was=>document.querySelector('.syllabus-panel').classList.contains('open')!==was,wasOpen);
  await page.fill('#scheduleDate','2026-12-01');await page.fill('#scheduleSubject','UI test');await page.fill('#scheduleSyllabus','Regression task');await page.click('#scheduleSubmit');
  await page.waitForFunction(()=>document.body.innerText.includes('Saved to disk ✓'));
  await page.waitForTimeout(2300);
  const saved=await (await fetch('http://127.0.0.1:18763/api/state')).json();assert(saved.data.rows.some(r=>r.subject==='Browser regression'));
  const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export backup',exact:true}).click();await download;
  await page.reload();await page.waitForSelector('.subject');assert.equal(await page.locator('.subject-name').last().inputValue(),'Browser regression');
  assert.deepEqual(errors,[]);console.log('PASS: agenda, routine, add subject, edit, syllabus, schedule, export, save and reload; no browser errors');
 }finally{if(browser)await browser.close();server.kill();}
})().catch(e=>{console.error(e);process.exitCode=1;});
