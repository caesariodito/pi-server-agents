const OTHER='__other';
const state=loadState();

function loadState(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch{return {}}}
function saveState(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch{}}
function otherBox(id){return document.querySelector(`textarea[data-other="${CSS.escape(id)}"]`)}
function syncOther(id,focus=false){const box=otherBox(id);if(!box)return;box.hidden=state[id]!==OTHER;if(!box.hidden&&focus)box.focus()}

for(const input of document.querySelectorAll('input[type="radio"][data-choice]')){
  if(state[input.name]===input.value)input.checked=true;
  input.addEventListener('change',()=>{state[input.name]=input.value;saveState();syncOther(input.name,true);renderAnswers()});
}
for(const box of document.querySelectorAll('textarea[data-other]')){
  const id=box.dataset.other;box.value=state[id+':other']||'';syncOther(id);
  box.addEventListener('input',()=>{state[id+':other']=box.value;saveState();renderAnswers()});
}
const notes=document.getElementById('review-notes');
if(notes){notes.value=state.__notes||'';notes.addEventListener('input',()=>{state.__notes=notes.value;saveState();renderAnswers()})}

function acceptAll(){
  for(const group of document.querySelectorAll('[data-decision]')){
    const rec=group.querySelector('input[data-recommended="true"]');
    if(!rec)continue;rec.checked=true;state[rec.name]=rec.value;syncOther(rec.name);
  }
  saveState();renderAnswers();flash('Recommendations selected. Review exceptions, then copy answers.');
}
function cleanLabel(input){return input.closest('.option').querySelector('.option-title').textContent.replace('my answer','').trim()}
function answerFor(id,input){
  if(!input)return '(no answer)';
  if(input.value!==OTHER)return cleanLabel(input);
  const typed=(state[id+':other']||'').trim();
  return typed?'OTHER — '+typed.replace(/\n+/g,' / '):'OTHER — will explain in chat';
}
function answerText(){
  const lines=[`${TITLE} — review answers — ${new Date().toISOString().slice(0,10)}`,''];let unanswered=0,discuss=0;
  for(const group of document.querySelectorAll('[data-decision]')){
    const id=group.dataset.decision,title=group.dataset.title||'';
    const picked=group.querySelector('input[type="radio"]:checked');
    if(!picked)unanswered++;else if(picked.value===OTHER&&!(state[id+':other']||'').trim())discuss++;
    lines.push(`${id} — ${title}\n    ${answerFor(id,picked)}`);
  }
  const free=(state.__notes||'').trim();if(free)lines.push('','Not asked about:',free);
  if(unanswered)lines.push('',`${unanswered} item(s) still unanswered.`);
  if(discuss)lines.push(`${discuss} item(s) marked OTHER with no text — discuss in chat.`);
  return lines.join('\n');
}
function renderAnswers(){const out=document.getElementById('answers');if(out)out.value=answerText()}
async function copyAnswers(){
  renderAnswers();const out=document.getElementById('answers');let ok=false;
  try{await navigator.clipboard.writeText(out.value);ok=true}catch{}
  if(!ok){out.select();try{ok=document.execCommand('copy')}catch{}}
  flash(ok?'Copied. Paste answers into Pi.':'Copy blocked. Select answer box and copy manually.');
}
function downloadAnswers(){
  renderAnswers();const blob=new Blob([answerText()],{type:'text/markdown'});const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);a.download=FILENAME;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);flash(`Saved ${FILENAME}.`);
}
function clearAnswers(){
  for(const key of Object.keys(state))delete state[key];saveState();
  for(const input of document.querySelectorAll('input[type="radio"][data-choice]'))input.checked=false;
  for(const box of document.querySelectorAll('textarea[data-other]')){box.value='';box.hidden=true}
  if(notes)notes.value='';renderAnswers();flash('Answers cleared.');
}
function toggleGuides(){
  const guides=[...document.querySelectorAll('.guide')];const show=guides.some(g=>g.hidden);
  for(const guide of guides)guide.hidden=!show;flash(show?'Writing guides shown.':'Writing guides hidden.');
}
function toggleTheme(){
  const root=document.documentElement,dark=matchMedia('(prefers-color-scheme: dark)').matches;
  const current=root.dataset.theme||(dark?'dark':'light');root.dataset.theme=current==='dark'?'light':'dark';
}
function flash(message){const el=document.getElementById('flash');if(!el)return;el.textContent=message;el.hidden=false;clearTimeout(flash.timer);flash.timer=setTimeout(()=>el.hidden=true,3500)}
renderAnswers();
