// timer.js [6] — динамический таймер отдыха (RIR-sensitive) + HIIT-финишер.
// Точность на timestamp: Date.now() - start, отсчёт не замедляется при блокировке экрана.

let timerEndAt = 0;        // timestamp конца отдыха
let timerPausedLeft = 0;   // остаток (сек) при паузе
let timerInterval = null;
let finisherInterval = null;
let finisherState = {mode:null, round:0, total:0, isWork:true, remaining:0, segmentEndAt:0, seq:null, seqIdx:0};
const FINISHER_PRESETS = {
  tabata:  {label:'Табата',   work:20, rest:10, rounds:8},
  '30-30': {label:'30/30',    work:30, rest:30, rounds:10},
  pyramid: {label:'Пирамида', seq:[15,30,45,30,15], rest:15},
  emom:    {label:'EMOM',     work:40, rest:20, rounds:12},
  amrap:   {label:'AMRAP',    work:600, rest:0, rounds:1}
};

function formatTimer(s){ if(s<0) s=0; const m=Math.floor(s/60).toString().padStart(2,'0'); const sec=(Math.floor(s)%60).toString().padStart(2,'0'); return `${m}:${sec}`; }

// Динамическая база отдыха: RIR<=1 — 180с, RIR>=2 — 120с, изоляция — 60-90с
function restDurationFor(rir, mechanics){
  if(mechanics === 'isolation') return (rir >= 2) ? 60 : 90;
  return (rir <= 1) ? 180 : 120;
}

function updateTimerDisplay(){
  const el = document.getElementById('timer-display');
  if(!el) return;
  const left = timerPausedLeft || Math.max(0, Math.ceil((timerEndAt - Date.now())/1000));
  el.textContent = formatTimer(left);
}

function startRestTimer(seconds, rir, mechanics){
  if(seconds) timerPausedLeft = 0;
  const dur = seconds || restDurationFor(rir, mechanics || 'compound') || 90;
  if(timerInterval){ clearInterval(timerInterval); timerInterval = null; }
  if(seconds || timerPausedLeft === 0 || timerPausedLeft === undefined){ timerPausedLeft = 0; }
  timerEndAt = Date.now() + (timerPausedLeft > 0 ? timerPausedLeft*1000 : dur*1000);
  timerPausedLeft = 0;
  updateTimerDisplay();
  const btn = document.getElementById('btn-timer-start');
  const ring = document.getElementById('timer-ring');
  if(ring) ring.classList.add('active');
  timerInterval = setInterval(() => {
    updateTimerDisplay();
    const left = (timerEndAt - Date.now())/1000;
    if(left <= 0){
      clearInterval(timerInterval); timerInterval = null;
      if(btn) btn.textContent = 'Готово! 🔔';
      if(ring) ring.classList.remove('active');
      try{ navigator.vibrate && navigator.vibrate([200,100,200]); }catch{}
      try{ if(typeof AGAudio !== 'undefined') AGAudio.beep(880, 400); }catch{}
      setTimeout(()=>{ if(btn){ btn.textContent='Старт 90с'; btn.onclick = ()=>startRestTimer(90); } resetTimer(); }, 3000);
    }
  }, 250);
  if(btn){
    btn.textContent = 'Пауза';
    btn.onclick = () => {
      if(timerInterval){
        timerPausedLeft = Math.max(0, (timerEndAt - Date.now())/1000);
        clearInterval(timerInterval); timerInterval = null;
        btn.textContent = 'Продолжить';
        if(ring) ring.classList.remove('active');
        btn.onclick = () => startRestTimer(null, rir, mechanics);
      } else {
        startRestTimer(null, rir, mechanics);
      }
    };
  }
}

function resetTimer(){
  if(timerInterval){ clearInterval(timerInterval); timerInterval = null; }
  timerEndAt = Date.now() + 90*1000; timerPausedLeft = 0;
  updateTimerDisplay();
  const btn = document.getElementById('btn-timer-start');
  const ring = document.getElementById('timer-ring');
  if(ring) ring.classList.remove('active');
  if(btn){ btn.textContent = 'Старт 90с'; btn.onclick = ()=>startRestTimer(90); }
}

// --- HIIT финишер (timestamp-based) ---
function startFinisher(mode){
  const preset = FINISHER_PRESETS[mode];
  if(!preset) return;
  finisherState = {mode, round:1, isWork:true, seq:preset.seq||null, seqIdx:0,
    remaining: preset.seq ? preset.seq[0] : preset.work,
    segmentEndAt: Date.now() + (preset.seq ? preset.seq[0] : preset.work)*1000};
  const lbl = document.getElementById('finisher-mode-label');
  if(lbl) lbl.textContent = preset.label;
  showSection('finisher-screen');
  if(finisherInterval) clearInterval(finisherInterval);
  runFinisherTick();
}

function runFinisherTick(){
  const display = document.getElementById('finisher-display');
  const roundEl = document.getElementById('finisher-round');
  const bar = document.getElementById('finisher-bar');
  const ring = document.getElementById('finisher-ring');
  const preset = FINISHER_PRESETS[finisherState.mode];
  const totalSegment = (finisherState.isWork ? (finisherState.seq ? finisherState.seq[finisherState.seqIdx] : preset.work) : preset.rest) || preset.work;
  if(bar) bar.style.width = '0%';

  finisherInterval = setInterval(() => {
    const now = Date.now();
    const left = Math.max(0, (finisherState.segmentEndAt - now)/1000);
    finisherState.remaining = left;
    if(display) display.textContent = formatTimer(left);
    if(roundEl) roundEl.textContent = `Раунд ${finisherState.round}/${preset.rounds || (preset.seq ? preset.seq.length : 1)} — ${finisherState.isWork ? 'Работа' : 'Отдых'}`;
    if(bar) bar.style.width = (100 - (left/totalSegment)*100) + '%';
    if(ring) ring.classList.toggle('active', finisherState.isWork);

    if(left <= 0){
      try{ if(typeof AGAudio !== 'undefined') AGAudio.beep(finisherState.isWork ? 660 : 440, 200); }catch{}
      try{ navigator.vibrate && navigator.vibrate(120); }catch{}

      if(finisherState.mode === 'tabata' || finisherState.mode === '30-30' || finisherState.mode === 'emom'){
        if(!finisherState.isWork){
          finisherState.round++;
          if(finisherState.round > preset.rounds){
            clearInterval(finisherInterval); finisherInterval = null;
            if(display) display.textContent = 'Готово!';
            setTimeout(()=>showSection('workout-complete'), 1500);
            return;
          }
        }
        finisherState.isWork = !finisherState.isWork;
      } else if(finisherState.mode === 'pyramid'){
        const nextIsWork = !finisherState.isWork;
        if(nextIsWork){
          finisherState.seqIdx++;
          if(finisherState.seqIdx >= preset.seq.length){
            clearInterval(finisherInterval); finisherInterval = null;
            if(display) display.textContent = 'Готово!';
            setTimeout(()=>showSection('workout-complete'), 1500);
            return;
          }
        }
        finisherState.isWork = nextIsWork;
      } else if(finisherState.mode === 'amrap'){
        clearInterval(finisherInterval); finisherInterval = null;
        if(display) display.textContent = 'Время!';
        setTimeout(()=>showSection('workout-complete'), 1500);
        return;
      }

      const seg = finisherState.isWork
        ? (finisherState.seq ? finisherState.seq[finisherState.seqIdx] : preset.work)
        : (preset.rest || 0);
      finisherState.segmentEndAt = Date.now() + seg*1000;
      if(bar) bar.style.width = '0%';
    }
  }, 200);
}

function stopFinisher(){
  if(finisherInterval){ clearInterval(finisherInterval); finisherInterval = null; }
  showSection('active-workout');
}

function toggleCheatSheet(){
  const s = document.getElementById('cheat-sheet');
  const i = document.getElementById('cheat-icon');
  if(!s) return;
  s.classList.toggle('hidden');
  if(i) i.textContent = s.classList.contains('hidden') ? '▼' : '▲';
}
