// app.js — управление экранами, профилями, дашбордом, readiness
const S = {
  userId: null, user: null, planData: null,
  selectedDay: null, dayExercises: [], workoutSets: {}, lastWeights: {}, _pendingSubs: []
};

async function api(path, opts={}) {
  const r = await fetch(path, { headers: {'Content-Type':'application/json'}, ...opts });
  if (!r.ok) {
    let detail = '';
    try { const j = await r.json(); detail = j.detail || j.message || JSON.stringify(j); } catch {}
    try { if(!detail) detail = await r.text(); } catch {}
    throw new Error('API ' + r.status + (detail ? ': ' + detail : ''));
  }
  return r.json();
}

function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  if (el) el.classList.add('active');
  const header = document.getElementById('app-header');
  if (header) header.classList.toggle('hidden', id === 'profile-select');
  if (id === 'pullup-plan' && typeof renderPullupPlan === 'function') renderPullupPlan();
  if (id === 'plan-select' && typeof loadPlans === 'function') loadPlans();
}

async function selectProfile(uid) {
  S.userId = uid; localStorage.setItem('ag_uid', uid);
  showSection('loading-screen');
  try {
    S.user = await api('/api/user/' + uid);
    S.lastWeights = await api('/api/last_weights/' + uid);
    await loadDashboard();
  } catch(e) { alert('Ошибка: ' + e.message); showSection('profile-select'); }
}

function logout() { localStorage.removeItem('ag_uid'); showSection('profile-select'); }

async function loadDashboard() {
  const dashName = document.getElementById('dash-name');
  const headerUser = document.getElementById('header-user');
  const pullupGuide = document.getElementById('pullup-guide');
  const dashPlanName = document.getElementById('dash-plan-name');
  const dashPlanDesc = document.getElementById('dash-plan-desc');
  if (dashName) dashName.textContent = S.user.name;
  if (headerUser) headerUser.textContent = S.user.name;
  if (pullupGuide) pullupGuide.classList.toggle('hidden', S.user.id !== '11111111-1111-1111-1111-111111111111' && S.user.id !== 1);
  S.planData = await api('/api/plan/' + S.user.current_plan_id);
  if (dashPlanName) dashPlanName.textContent = S.planData.plan.name;
  if (dashPlanDesc) dashPlanDesc.textContent = S.planData.plan.description;
  try { S.workoutLogs = await api('/api/logs/' + S.userId); } catch(e){ S.workoutLogs = []; }
  renderCalendar();
  renderDayButtons();
  showSection('dashboard');
}

// Calendar ПН-ВС
let calWeekStart = null;
function getWeekStart(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1) - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0,0,0,0);
  return d;
}
function shiftWeek(delta) {
  if (!calWeekStart) calWeekStart = getWeekStart(new Date());
  calWeekStart.setDate(calWeekStart.getDate() + delta * 7);
  renderCalendar();
}
function renderCalendar() {
  const bar = document.getElementById('calendar-bar');
  if(!bar) return;
  bar.innerHTML = '';
  const days = ['ПН','ВТ','СР','ЧТ','ПТ','СБ','ВС'];
  const today = new Date(); today.setHours(0,0,0,0);
  const schedule = S.user.schedule || [];
  const logs = S.workoutLogs || [];
  if (!calWeekStart) calWeekStart = getWeekStart(today);
  const monthNames = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
  const ml = document.getElementById('cal-month-label');
  if(ml) ml.textContent = monthNames[calWeekStart.getMonth()] + ' ' + calWeekStart.getFullYear();
  const hasLogForDate = (date) => {
    const ds = date.toISOString().split('T')[0];
    return logs.some(l => l.date && l.date.startsWith(ds));
  };
  for(let i=0;i<7;i++){
    let d = new Date(calWeekStart); d.setDate(calWeekStart.getDate()+i);
    let dow=d.getDay(); let schedDow = dow===0?0:dow;
    let isToday=d.getTime()===today.getTime();
    let isScheduled=schedule.includes(schedDow);
    let hasLog=hasLogForDate(d);
    let isPast=d<today;
    let cls='cal-day ';
    if(isToday) cls+='today ';
    if(hasLog) cls+='completed ';
    else if(isScheduled && isPast) cls+='missed ';
    else if(isScheduled) cls+='scheduled ';
    let clickHandler=`onclick="openDayFromCalendar(${i})"`;
    bar.innerHTML+=`<div class="${cls}" ${clickHandler} style="cursor:pointer"><div class="day-name">${days[i]}</div><div class="day-num">${d.getDate()}</div></div>`;
  }
  const missed = document.querySelector('.cal-day.missed');
  const warn = document.getElementById('missed-warning');
  if(warn) warn.classList.toggle('hidden', !missed);
}
function openDayFromCalendar(dayOffset) {
  if (!calWeekStart) return;
  const d = new Date(calWeekStart); d.setDate(calWeekStart.getDate() + dayOffset);
  const today = new Date(); today.setHours(0,0,0,0);
  if (d > today) return alert('Нельзя начать тренировку в будущем');
  const dow=d.getDay(); const schedDow=dow===0?0:dow;
  const schedule=S.user.schedule||[];
  if(!schedule.includes(schedDow)) return alert('В этот день тренировка не запланирована');
  const idx=schedule.indexOf(schedDow);
  const programDays=Array.from(new Set(S.planData.exercises.map(e=>e.day_number))).sort((a,b)=>a-b);
  const dayNumber=programDays[idx%programDays.length];
  initReadiness(dayNumber);
}

async function saveSchedule(){
  let selected=Array.from(document.querySelectorAll('.sched-cb:checked')).map(cb=>parseInt(cb.value));
  if(selected.length>4) return alert('Максимум 4 дня в неделю!');
  const btn=document.getElementById('btn-save-sched'); if(btn) btn.textContent='Сохранение...';
  try{ await api('/api/user/'+S.userId+'/schedule',{method:'PATCH',body:JSON.stringify({schedule:selected})}); S.user.schedule=selected; loadDashboard(); }catch(e){ alert('Ошибка: '+e.message); }
}
async function loadPlans(){
  const plans=await api('/api/plans'); const cont=document.getElementById('plan-list'); if(!cont) return; cont.innerHTML='';
  plans.forEach(plan=>{
    const isCurrent=S.user.current_plan_id===plan.id;
    const btn=document.createElement('button');
    btn.className=`glass p-5 card-hover ${isCurrent?'border-l-4 border-purple opacity-100':'opacity-70'}`;
    btn.innerHTML=`<div class="flex items-start justify-between"><div><div class="text-white font-bold text-lg">${plan.name}</div><div class="text-gray-400 text-sm mt-1">${plan.description||''}</div><div class="text-xs text-gray-500 mt-2">${(plan.tags||[]).map(t=>`<span class="px-2 py-0.5 bg-purple/20 rounded text-purple mr-1">${t}</span>`).join('')}</div></div>${isCurrent?'<span class="text-green-400 text-2xl">✓</span>':''}</div>`;
    if(!isCurrent) btn.onclick=()=>selectPlan(plan.id);
    cont.appendChild(btn);
  });
}
async function selectPlan(planId){
  try{ await api('/api/user/'+S.userId+'/plan',{method:'PATCH',body:JSON.stringify({plan_id:planId})}); S.user.current_plan_id=planId; loadDashboard(); }catch(e){ alert('Ошибка: '+e.message); }
}
function renderDayButtons(){
  const cont=document.getElementById('day-buttons'); if(!cont) return; cont.innerHTML='';
  const days=new Set(S.planData.exercises.map(e=>e.day_number));
  days.forEach(d=>{
    let btn=document.createElement('button');
    btn.className='glass p-4 text-left card-hover';
    btn.innerHTML=`<div class="text-purple font-bold uppercase text-xs mb-1">День ${d}</div><div class="text-white font-bold">Начать</div>`;
    btn.onclick=()=>initReadiness(d);
    cont.appendChild(btn);
  });
}

// Readiness
function initReadiness(day){
  S.selectedDay=day;
  S.dayExercises=S.planData.exercises.filter(e=>e.day_number===day);
  document.querySelectorAll('.sore-cb').forEach(cb=>cb.checked=false);
  document.querySelectorAll('.muscle-chip').forEach(b=>b.classList.remove('active'));
  const pain=document.getElementById('readiness-pain')||document.getElementById('pain-level'); if(pain) pain.value=1;
  if(typeof updatePain==='function') updatePain(1);
  const res=document.getElementById('readiness-result'); if(res){ res.classList.add('hidden'); res.innerHTML=''; }
  const btn=document.getElementById('btn-check-readiness'); if(btn) btn.innerHTML='<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 110-16 8 8 0 010 16z"/></svg> Проверить';
  showSection('readiness-form');
}
function toggleMuscle(btn){
  btn.classList.toggle('active');
  const cb=btn.querySelector('.sore-cb'); if(cb) cb.checked=btn.classList.contains('active');
}
function updatePain(val){
  const pv=document.getElementById('pain-value'); if(pv){ pv.textContent=val+' / 10'; let col='#22C55E'; const v=parseInt(val); if(v>=7) col='#EF4444'; else if(v>=4) col=v>=6?'#F97316':'#EAB308'; pv.style.color=col; }
  const p2=document.getElementById('readiness-pain'); if(p2) p2.value=val;
  const p1=document.getElementById('pain-level'); if(p1) p1.value=val;
}
function skipReadiness(){ S._pendingSubs=[]; initWarmup(S.selectedDay, true); }
async function checkReadiness(){
  const btn=document.getElementById('btn-check-readiness');
  const resDiv=document.getElementById('readiness-result');
  const sore=Array.from(document.querySelectorAll('.sore-cb:checked')).map(cb=>cb.value);
  const painEl=document.getElementById('readiness-pain')||document.getElementById('pain-level');
  const pain=painEl?parseInt(painEl.value):1;
  // extended fields for new schema
  const sleepEl=document.getElementById('sleep-quality'); const stressEl=document.getElementById('stress-level'); const cnsEl=document.getElementById('cns-fatigue');
  const sleep_quality=sleepEl?parseInt(sleepEl.value):3;
  const stress_level=stressEl?parseInt(stressEl.value):3;
  const cns_fatigue=cnsEl?parseInt(cnsEl.value):3;
  if(btn) btn.innerHTML='<span class="spinner w-4 h-4 border-2"></span> AI думает...';
  try{
    const data=await api('/api/readiness/check',{method:'POST',body:JSON.stringify({user_id:S.userId, plan_id:S.user.current_plan_id, day_number:S.selectedDay, sore_muscles:sore, pain_level:pain, sleep_quality, stress_level, cns_fatigue})});
    // fallback to legacy endpoint if 404
    if(resDiv){
      resDiv.classList.remove('hidden');
      if(data.status==='ok'){
        resDiv.innerHTML=`<div class="text-green-400 font-bold flex items-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> ${data.message}</div><button onclick="initWarmup(S.selectedDay)" class="btn-primary mt-3 w-full">К разминке</button>`;
      } else if(data.status==='modified'){
        S._pendingSubs=data.substitutions||[];
        let exMap={}; try{ const all=await api('/api/exercises'); exMap=Object.fromEntries(all.map(e=>[e.id,e.name])); }catch{}
        let subs=(S._pendingSubs||[]).map(s=>{
          const orig=S.dayExercises.find(e=>e.exercise_id===s.original_exercise_id)?.exercises.name||s.original_exercise_id;
          const replName=exMap[s.replacement_exercise_id]||('ID '+s.replacement_exercise_id);
          return `<div class="glass p-2 mb-2 text-sm"><span class="text-red-400 line-through">${orig}</span> → <span class="text-green-400">${replName}</span><div class="text-gray-500 text-xs">${s.reason}</div></div>`;
        }).join('');
        resDiv.innerHTML=`<div class="text-yellow-400 font-bold mb-2 flex items-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z"/></svg> Найдены замены (pain ${pain}/10)</div>${subs||'<div class="text-gray-400 text-sm">Нет замен, но совет: '+(data.general_advice||'')+'</div>'}${data.general_advice?`<div class="text-gray-300 text-sm mt-2 flex gap-2"><svg class="w-4 h-4 text-yellow-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.94 12.94 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18"/></svg> ${data.general_advice}</div>`:''}<div class="grid grid-cols-2 gap-2 mt-3"><button onclick="applySubstitutions()" class="btn-primary text-sm">Применить замены</button><button onclick="initWarmup(S.selectedDay, true)" class="btn-ghost text-sm">Игнорировать</button></div>`;
      } else {
        resDiv.innerHTML=`<div class="text-red-400">${data.message||'AI недоступен'}</div><button onclick="initWarmup(S.selectedDay)" class="btn-primary mt-3 w-full">К разминке</button>`;
      }
    }
  } catch(e){
    // try legacy
    try{
      const data2=await api('/api/check_readiness',{method:'POST',body:JSON.stringify({user_id:parseInt(S.userId)||S.userId, plan_id:S.user.current_plan_id, day_number:S.selectedDay, sore_muscles:sore, pain_level:pain})});
      if(resDiv){
        resDiv.classList.remove('hidden');
        if(data2.status==='ok') resDiv.innerHTML=`<div class="text-green-400 font-bold">${data2.message}</div><button onclick="initWarmup(S.selectedDay)" class="btn-primary mt-3 w-full">К разминке</button>`;
        else if(data2.status==='modified'){
          S._pendingSubs=data2.substitutions||[];
          resDiv.innerHTML=`<div class="text-yellow-400 font-bold">Найдены замены</div><div class="grid grid-cols-2 gap-2 mt-3"><button onclick="applySubstitutions()" class="btn-primary text-sm">Применить</button><button onclick="initWarmup(S.selectedDay,true)" class="btn-ghost text-sm">Игнорировать</button></div>`;
        }
      }
    }catch(e2){
      alert('Ошибка: '+e.message);
      if(resDiv){ resDiv.classList.remove('hidden'); resDiv.innerHTML=`<div class="text-red-400">Ошибка: ${e.message}</div><button onclick="initWarmup(S.selectedDay)" class="btn-ghost w-full mt-2">К разминке</button>`; }
    }
  }
  if(btn) btn.innerHTML='<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 110-16 8 8 0 010 16z"/></svg> Проверить';
}
async function applySubstitutions(subs){
  subs=subs||S._pendingSubs||[];
  if(!subs||!subs.length) return initWarmup(S.selectedDay,true);
  try{
    const all=await api('/api/exercises');
    const map=Object.fromEntries(all.map(e=>[e.id,e]));
    subs.forEach(s=>{
      const idx=S.dayExercises.findIndex(e=>e.exercise_id===s.original_exercise_id);
      if(idx!==-1 && map[s.replacement_exercise_id]){
        S.dayExercises[idx]={...S.dayExercises[idx], exercise_id:s.replacement_exercise_id, exercises:map[s.replacement_exercise_id]};
      }
    });
  }catch(e){ console.warn('apply failed',e); }
  showWarmupScreen();
}

function initWarmup(day, ignoreSubs=false){
  S.selectedDay=day;
  if(ignoreSubs) S._pendingSubs=[];
  const needsFresh=!S.dayExercises||S.dayExercises.length===0||S.dayExercises[0].day_number!==day||ignoreSubs;
  if(needsFresh){ S.dayExercises=S.planData.exercises.filter(e=>e.day_number===day); }
  showWarmupScreen();
}
function showWarmupScreen(){
  const exList=S.dayExercises;
  let isLower=exList.some(e=>['quads','hamstrings','glutes'].includes(e.exercises.target_muscle));
  let isUpper=exList.some(e=>['chest','back','shoulders','biceps','triceps'].includes(e.exercises.target_muscle));
  let html='';
  if(isUpper){
    html+=`<div class="glass p-3 flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-purple/15 flex items-center justify-center flex-shrink-0"><svg class="w-5 h-5 text-purple" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 8l4 4-4 4M8 8l-4 4 4 4M12 3v18"/></svg></div><div><div class="text-white font-bold text-sm">Вращения плечами и руками</div><div class="text-gray-400 text-xs">Вперед/назад по 15 раз</div></div></div>`;
    html+=`<div class="glass p-3 flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-pink/15 flex items-center justify-center flex-shrink-0"><svg class="w-5 h-5 text-pink" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12h12M6 12a6 6 0 016-6M18 12a6 6 0 01-6 6"/></svg></div><div><div class="text-white font-bold text-sm">Отжимания от пола/скамьи</div><div class="text-gray-400 text-xs">1 подход х 10-15 легко</div></div></div>`;
  }
  if(isLower){
    html+=`<div class="glass p-3 flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-purple/15 flex items-center justify-center flex-shrink-0"><svg class="w-5 h-5 text-purple" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 12h12"/></svg></div><div><div class="text-white font-bold text-sm">Махи ногами</div><div class="text-gray-400 text-xs">Вперед-назад и в стороны по 10 раз</div></div></div>`;
    html+=`<div class="glass p-3 flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-pink/15 flex items-center justify-center flex-shrink-0"><svg class="w-5 h-5 text-pink" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg></div><div><div class="text-white font-bold text-sm">Воздушные приседания</div><div class="text-gray-400 text-xs">1 подход х 15 раз</div></div></div>`;
  }
  const warmupList=document.getElementById('warmup-list');
  const warmupTitle=document.getElementById('warmup-title');
  if(warmupList) warmupList.innerHTML=html;
  if(warmupTitle) warmupTitle.textContent=(isLower&&isUpper)?'Фулбади разминка':(isLower?'Разминка Низа':'Разминка Верха');
  showSection('warmup-screen');
}

// Auto-init
if(localStorage.getItem('ag_uid')) selectProfile(localStorage.getItem('ag_uid'));
else showSection('profile-select');
