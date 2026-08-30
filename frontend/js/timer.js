// timer.js — rest + HIIT finisher timers with neon pulse

let timerInterval=null;
let timerRemaining=90;
let finisherInterval=null;
let finisherState={mode:null, round:0, total:0, isWork:true, remaining:0};

function formatTimer(s){ const m=Math.floor(s/60).toString().padStart(2,'0'); const sec=(s%60).toString().padStart(2,'0'); return `${m}:${sec}`; }
function updateTimerDisplay(){ const el=document.getElementById('timer-display'); if(el) el.textContent=formatTimer(timerRemaining); }

function startRestTimer(seconds){
  if(seconds) timerRemaining=seconds;
  if(timerInterval) clearInterval(timerInterval);
  updateTimerDisplay();
  const btn=document.getElementById('btn-timer-start');
  const ring=document.getElementById('timer-ring');
  if(ring) ring.classList.add('active');
  timerInterval=setInterval(()=>{
    timerRemaining--; updateTimerDisplay();
    if(timerRemaining<=0){
      clearInterval(timerInterval); timerInterval=null;
      if(btn) btn.textContent='Готово!';
      if(ring) ring.classList.remove('active');
      try{ navigator.vibrate&&navigator.vibrate([200,100,200]); }catch{}
      try{ const ctx=new (window.AudioContext||window.webkitAudioContext)(); const o=ctx.createOscillator(); o.frequency.value=880; o.connect(ctx.destination); o.start(); setTimeout(()=>o.stop(),400);}catch{}
      setTimeout(()=>{ if(btn) btn.textContent='Старт 90с'; resetTimer(); },3000);
    }
  },1000);
  if(btn){ btn.textContent='Пауза'; btn.onclick=()=>{ if(timerInterval){ clearInterval(timerInterval); timerInterval=null; btn.textContent='Продолжить'; if(ring) ring.classList.remove('active'); btn.onclick=()=>startRestTimer(); } else startRestTimer(); }; }
}
function resetTimer(){ if(timerInterval){ clearInterval(timerInterval); timerInterval=null; } timerRemaining=90; updateTimerDisplay(); const btn=document.getElementById('btn-timer-start'); const ring=document.getElementById('timer-ring'); if(ring) ring.classList.remove('active'); if(btn){ btn.textContent='Старт 90с'; btn.onclick=()=>startRestTimer(90); } }

// Finisher modes per spec
const FINISHER_PRESETS={
  tabata:{label:'Табата', work:20, rest:10, rounds:8, total:160},
  '30-30':{label:'30/30', work:30, rest:30, rounds:10, total:600},
  pyramid:{label:'Пирамида', seq:[15,30,45,30,15], rest:15},
  emom:{label:'EMOM', work:40, rest:20, rounds:12, total:720},
  amrap:{label:'AMRAP', work:600, rest:0, rounds:1}
};

function startFinisher(mode){
  const preset=FINISHER_PRESETS[mode]; if(!preset) return;
  finisherState={mode, round:1, isWork:true, remaining: preset.seq?preset.seq[0]:preset.work, total:preset.rounds*2};
  if(mode==='pyramid'){ finisherState.seq=preset.seq; finisherState.seqIdx=0; finisherState.total=preset.seq.length*2-1; }
  if(mode==='amrap'){ finisherState.remaining=preset.work; }
  document.getElementById('finisher-mode-label').textContent=preset.label;
  showSection('finisher-screen');
  runFinisherTick();
}

function runFinisherTick(){
  if(finisherInterval) clearInterval(finisherInterval);
  const display=document.getElementById('finisher-display');
  const roundEl=document.getElementById('finisher-round');
  const bar=document.getElementById('finisher-bar');
  const ring=document.getElementById('finisher-ring');
  const preset=FINISHER_PRESETS[finisherState.mode];
  let totalDuration = preset.total || 600;
  // for pyramid compute sum
  if(preset.seq) totalDuration = preset.seq.reduce((a,b)=>a+b,0) + (preset.seq.length-1)*preset.rest;

  finisherInterval=setInterval(()=>{
    finisherState.remaining--;
    if(display) display.textContent=formatTimer(finisherState.remaining);
    if(roundEl) roundEl.textContent=`Раунд ${finisherState.round}/${preset.rounds||preset.seq?.length||1} — ${finisherState.isWork?'Работа':'Отдых'}`;
    if(bar){
      // progress based on elapsed
    }
    if(finisherState.remaining<=0){
      // beep
      try{ const ctx=new (window.AudioContext||window.webkitAudioContext)(); const o=ctx.createOscillator(); o.frequency.value=finisherState.isWork?660:440; o.connect(ctx.destination); o.start(); setTimeout(()=>o.stop(),200);}catch{}
      try{ navigator.vibrate&&navigator.vibrate(120);}catch{}
      if(finisherState.mode==='tabata' || finisherState.mode==='30-30' || finisherState.mode==='emom'){
        if(!finisherState.isWork){
          finisherState.round++;
          if(finisherState.round>preset.rounds){
            clearInterval(finisherInterval); finisherState.mode=null;
            if(display) display.textContent='Готово!';
            setTimeout(()=>showSection('workout-complete'),1500);
            return;
          }
        }
        finisherState.isWork=!finisherState.isWork;
        finisherState.remaining=finisherState.isWork?preset.work:preset.rest;
      } else if(finisherState.mode==='pyramid'){
        // pyramid: work/rest alternating through seq
        let nextIsWork = !finisherState.isWork;
        let nextRemaining;
        if(nextIsWork){
          finisherState.seqIdx++;
          if(finisherState.seqIdx>=preset.seq.length){ clearInterval(finisherInterval); if(display) display.textContent='Готово!'; setTimeout(()=>showSection('workout-complete'),1500); return; }
          nextRemaining=preset.seq[finisherState.seqIdx];
        } else nextRemaining=preset.rest;
        finisherState.isWork=nextIsWork;
        finisherState.remaining=nextRemaining;
      } else if(finisherState.mode==='amrap'){
        clearInterval(finisherInterval);
        if(display) display.textContent='Время!';
        setTimeout(()=>showSection('workout-complete'),1500);
        return;
      }
      if(ring) ring.classList.toggle('active', finisherState.isWork);
    }
  },1000);
}

function stopFinisher(){
  if(finisherInterval){ clearInterval(finisherInterval); finisherInterval=null; }
  showSection('active-workout');
}
