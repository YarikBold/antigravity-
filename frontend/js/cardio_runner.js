// cardio_runner.js [6] — полноэкранный кардио-раннер: LISS вход (15м) -> EMOM MetCon (15м, 3 круга по 5 станций) -> LISS заминка (15м)
// Точность на timestamp: Date.now() - segmentStart (чек-лист №5), звук через AGAudio (user gesture, чек-лист №4)

const CR_PLAN = {
  liss_in: { label: 'LISS Разгон', minutes: 15, hint: 'Дорожка, уклон 8-10%, скорость 4.8-5.2 км/ч. Дыши носом, пульс ~120-130.' },
  emom_minutes: 15, // 3 круга × 5 станций по 1 мин
  stations: [
    { name: 'Махи гирей', reps: '18 повторений', weight: '16-20 кг', hint: 'Хип-хайдж, гиря до уровня груди' },
    { name: 'Отжимания от пола', reps: '15 повторений', weight: '', hint: 'Корпус в линию, грудь до пола' },
    { name: 'Кубковые приседания', reps: '14 повторений', weight: '12-16 кг', hint: 'Гиря у груди, глубоко' },
    { name: 'Скалолаз', reps: '35 секунд', weight: '', hint: 'Быстрые смены ног, пресс держи' },
    { name: 'Отдых', reps: '60 секунд', weight: '', hint: 'Дыши, готовься к следующей станции' }
  ],
  liss_out: { label: 'LISS Заминка', minutes: 15, hint: 'Велотренажер / эллипсоид, легкий темп. Дожигаем жирные кислоты.' }
};

const cr = { phase: null, phaseStart: 0, phaseDurSec: 0, minuteEndAt: 0, minuteStart: 0, stationIdx: 0, round: 1, timer: null, running: false };

function crFmt(sec){ sec = Math.max(0, sec); const m = Math.floor(sec/60).toString().padStart(2,'0'); const s = Math.floor(sec%60).toString().padStart(2,'0'); return `${m}:${s}`; }

function launchCardioRunner(){
  if(!S.userId) return alert('Сначала выбери профиль');
  showSection('cardio-runner');
  crRenderIdle();
}

function crRenderIdle(){
  const el = document.getElementById('cr-body');
  const title = document.getElementById('cr-title');
  if(title) title.textContent = 'Гибридное Кардио';
  if(el) el.innerHTML = `
    <div class="glass p-5 grad-border max-w-md mx-auto w-full">
      <div class="text-white font-bold text-lg mb-3">45 минут жиросжигания</div>
      <div class="space-y-2 mb-4">
        <div class="flex items-center gap-3 p-3 rounded-xl bg-black/20"><span class="w-8 h-8 rounded-lg flex items-center justify-center font-black" style="background:rgba(245,158,11,.2);color:#F59E0B">1</span><div><div class="text-white text-sm font-bold">LISS Разгон — 15 мин</div><div class="text-gray-400 text-xs">Дорожка, уклон 8-10%, 4.8-5.2 км/ч</div></div></div>
        <div class="flex items-center gap-3 p-3 rounded-xl bg-black/20"><span class="w-8 h-8 rounded-lg flex items-center justify-center font-black" style="background:rgba(236,72,153,.2);color:#EC4899">2</span><div><div class="text-white text-sm font-bold">EMOM MetCon — 15 мин</div><div class="text-gray-400 text-xs">3 круга: гиря → отжимания → кубок → скалолаз → отдых</div></div></div>
        <div class="flex items-center gap-3 p-3 rounded-xl bg-black/20"><span class="w-8 h-8 rounded-lg flex items-center justify-center font-black" style="background:rgba(139,92,246,.2);color:#A78BFA">3</span><div><div class="text-white text-sm font-bold">LISS Заминка — 15 мин</div><div class="text-gray-400 text-xs">Велотренажер / эллипсоид</div></div></div>
      </div>
      <button onclick="crStart()" class="btn-primary flex items-center justify-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"/></svg> Начать кардио</button>
    </div>`;
}

function crStart(){
  AGAudio.unlock(); // user gesture (чек-лист №4)
  cr.running = true;
  crEnterPhase('liss_in');
}

function crEnterPhase(phase){
  cr.phase = phase;
  cr.phaseStart = Date.now();
  cr.stationIdx = 0;
  cr.round = 1;
  if(phase === 'liss_in'){ cr.phaseDurSec = CR_PLAN.liss_in.minutes*60; crRenderLISS(CR_PLAN.liss_in, 'LISS Разгон'); }
  else if(phase === 'emom'){ cr.phaseDurSec = CR_PLAN.emom_minutes*60; crEnterMinute(); }
  else if(phase === 'liss_out'){ cr.phaseDurSec = CR_PLAN.liss_out.minutes*60; crRenderLISS(CR_PLAN.liss_out, 'LISS Заминка'); }
  if(cr.timer) clearInterval(cr.timer);
  cr.timer = setInterval(crTick, 250);
  crTick();
}

function crPhaseHeader(){
  const total = 45*60;
  const doneSec = crDoneSeconds();
  const el = document.getElementById('cr-body');
  if(el) el.insertAdjacentHTML('beforebegin', '');
  const bar = document.getElementById('cr-phase-bar');
  if(bar){
    const segs = ['LISS', 'EMOM', 'ЗАМИНКА'];
    bar.innerHTML = segs.map((s,i)=>{
      const cls = i < crPhaseIndex() ? 'done' : (i === crPhaseIndex() ? 'active' : '');
      return `<div class="cr-phase-seg ${cls}" title="${s}"></div>`;
    }).join('');
  }
  const elapsed = document.getElementById('cr-total-elapsed');
  if(elapsed) elapsed.textContent = crFmt(doneSec) + ' / 45:00';
}

function crPhaseIndex(){ return cr.phase==='liss_in' ? 0 : (cr.phase==='emom' ? 1 : 2); }
function crDoneSeconds(){
  if(cr.phase==='liss_in') return Math.min(cr.phaseDurSec, Math.floor((Date.now()-cr.phaseStart)/1000));
  if(cr.phase==='emom') return 15*60 + Math.min(cr.phaseDurSec, Math.floor((Date.now()-cr.phaseStart)/1000));
  if(cr.phase==='liss_out') return 30*60 + Math.min(cr.phaseDurSec, Math.floor((Date.now()-cr.phaseStart)/1000));
  return 0;
}

function crRenderLISS(plan, title){
  const el = document.getElementById('cr-body');
  const t = document.getElementById('cr-title');
  if(t) t.textContent = title;
  if(el) el.innerHTML = `
    <div class="flex-1 flex flex-col items-center justify-center gap-4 w-full max-w-md mx-auto">
      <div class="text-gray-400 text-sm font-bold tracking-widest uppercase">${title}</div>
      <div class="cr-timer text-white" id="cr-timer">15:00</div>
      <div class="progress-bar w-full"><div id="cr-bar" style="width:0%"></div></div>
      <div class="glass p-4 w-full">
        <div class="cr-hint">${plan.hint}</div>
      </div>
      <button onclick="crNextPhase()" class="btn-ghost">Пропустить фазу →</button>
    </div>`;
}

function crEnterMinute(){
  const minuteInEmom = Math.floor((Date.now()-cr.phaseStart)/60000);
  cr.stationIdx = minuteInEmom % 5;
  cr.round = Math.floor(minuteInEmom/5) + 1;
  if(minuteInEmom >= CR_PLAN.emom_minutes){ crNextPhase(); return; }
  cr.minuteStart = Date.now();
  cr.minuteEndAt = cr.minuteStart + 60000;
  crRenderEMOMMinute();
}

function crRenderEMOMMinute(){
  const st = CR_PLAN.stations[cr.stationIdx];
  const el = document.getElementById('cr-body');
  const t = document.getElementById('cr-title');
  if(t) t.textContent = 'EMOM MetCon';
  if(el) el.innerHTML = `
    <div class="flex-1 flex flex-col items-center justify-center gap-3 w-full max-w-md mx-auto">
      <div class="cr-round-badge" style="background:rgba(236,72,153,.15);color:#F472B6">Круг ${cr.round}/3 • Мин ${((cr.round-1)*5 + cr.stationIdx + 1)}/15</div>
      <div class="cr-station text-center ${st.name==='Отдых' ? 'text-gray-300' : 'text-white'}">${st.name==='Отдых' ? '🛌 Отдых' : st.name}</div>
      <div class="cr-minute-timer text-white" id="cr-timer">01:00</div>
      <div class="progress-bar w-full"><div id="cr-bar" style="width:0%"></div></div>
      <div class="glass p-3 w-full text-center">
        <div class="text-white font-bold text-lg">${st.reps}</div>
        ${st.weight ? `<div class="text-gray-400 text-xs">вес: ${st.weight}</div>` : ''}
        <div class="cr-hint mt-1">${st.hint}</div>
      </div>
      <button onclick="crNextPhase()" class="btn-ghost">Закончить EMOM →</button>
    </div>`;
  // Предупреждающие бипы на последних 3 секундах минуты
  AGAudio.beep(660, 120);
}

function crTick(){
  if(!cr.running) return;
  const now = Date.now();
  const left = Math.max(0, cr.phaseDurSec - (now - cr.phaseStart)/1000);
  const timerEl = document.getElementById('cr-timer');
  const barEl = document.getElementById('cr-bar');

  crPhaseHeader();

  if(cr.phase === 'emom'){
    const mLeft = Math.max(0, (cr.minuteEndAt - now)/1000);
    if(timerEl) timerEl.textContent = crFmt(Math.ceil(mLeft));
    if(barEl) barEl.style.width = (100 - (mLeft/60)*100) + '%';
    if(mLeft <= 3.05 && mLeft > 2.9) AGAudio.beep(880, 80);
    if(mLeft <= 0){
      AGAudio.beep(520, 150); // смена станции
      crEnterMinute();
    }
    return;
  }

  if(timerEl) timerEl.textContent = crFmt(Math.ceil(left));
  if(barEl) barEl.style.width = (100 - (left/cr.phaseDurSec)*100) + '%';

  if(left <= 3 && left > 2.7) AGAudio.beep(880, 120);
  if(left <= 0){
    if(cr.phase === 'liss_in'){ AGAudio.beep(660, 300); crNextPhase(); }
    else if(cr.phase === 'liss_out'){ crFinish(true); }
  }
}

function crNextPhase(){
  if(cr.phase === 'liss_in'){ AGAudio.beep(660, 300); crEnterPhase('emom'); }
  else if(cr.phase === 'emom'){ AGAudio.beep(520, 300); crEnterPhase('liss_out'); }
}

async function crFinish(auto){
  cr.running = false;
  if(cr.timer){ clearInterval(cr.timer); cr.timer = null; }
  const btnId = 'cr-finish-btn';
  const el = document.getElementById('cr-body');
  if(el) el.innerHTML = `<div class="text-center flex flex-col items-center gap-3"><div class="text-4xl">🔥</div><div class="text-white font-bold text-xl">${auto ? 'Кардио завершено!' : 'Кардио-сессия'}</div><div class="text-gray-400 text-sm">LISS + EMOM + LISS выполнено</div><div class="glass p-3 w-full max-w-xs text-left text-sm space-y-1"><div class="flex justify-between"><span class="text-gray-400">Тип сессии</span><span class="text-white font-bold">cardio</span></div><div class="flex justify-between"><span class="text-gray-400">Длительность</span><span class="text-white font-bold" id="cr-done-min">~45 мин</span></div><div class="flex justify-between"><span class="text-gray-400">RPE</span><span class="text-white font-bold">7-8</span></div></div><button id="${btnId}" onclick="crSave()" class="btn-primary flex items-center justify-center gap-2"><svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> Сохранить тренировку</button></div>`;
  AGAudio.beep(880, 400);
}

async function crSave(){
  const btn = document.getElementById('cr-finish-btn');
  if(btn){ btn.innerHTML = '<span class="spinner"></span> Сохранение...'; btn.disabled = true; }
  const minutes = Math.max(1, Math.round((Date.now() - cr.phaseStart)/60000));
  const payload = {
    user_id: String(S.userId),
    plan_id: String(S.user.current_plan_id || ''),
    duration_minutes: 45,
    stations_done: [
      { name: 'LISS Разгон', minutes: 15 },
      { name: 'EMOM MetCon', minutes: 15, rounds: 3 },
      { name: 'LISS Заминка', minutes: 15 }
    ],
    perceived_effort_rpe: 7
  };
  let persisted = false;
  try{
    const r = await api('/api/workouts/cardio-complete', { method:'POST', body: JSON.stringify(payload) });
    persisted = r.status === 'ok';
  }catch(e){
    console.warn('cardio-complete failed:', e.message);
    alert('Не удалось сохранить кардио: ' + e.message);
  }
  if(persisted && typeof loadDashboard === 'function'){
    try{ S.workoutLogs = await api('/api/logs/' + S.userId); }catch{}
  }
  showSection('dashboard');
  if(persisted && typeof renderCalendar === 'function') renderCalendar();
}
