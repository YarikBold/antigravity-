// finisher_timer.js — интерактивный таймер финишеров (5 режимов).
// Точность через Date.now() (не плывёт при блокировке экрана), звук через AGAudio (user gesture).
// Оборачивает legacy window.startFinisher из timer.js: все существующие кнопки получают
// новый движок + флаг S.has_completed_finisher для умного перехвата завершения.
(function(){
'use strict';

const FT_MODES = {
  tabata:  { label: 'Табата',           work: 20, rest: 10, rounds: 8 },
  '30-30': { label: 'Интервалы 30/30',  work: 30, rest: 30, rounds: 10 },
  pyramid: { label: 'Пирамида 15–45',   seq: [15, 30, 45, 30, 15], rest: 15 },
  emom:    { label: 'EMOM',             work: 40, rest: 20, rounds: 12 },
  amrap:   { label: 'AMRAP',            work: 600, rest: 0, rounds: 1 }
};

let ftTimer = null;
const FT = { mode: null, round: 1, isWork: true, segmentEndAt: 0, seqIdx: 0 };

function ftFmt(sec){
  sec = Math.max(0, Math.ceil(sec));
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return m + ':' + s;
}

function ftBeep(freq, dur){
  try { if (typeof AGAudio !== 'undefined') AGAudio.beep(freq, dur); } catch (e) {}
  try { if (navigator.vibrate) navigator.vibrate(120); } catch (e) {}
}

function ftPreset(){ return FT_MODES[FT.mode]; }

function ftSegLen(){
  const p = ftPreset();
  if (!p) return 20;
  if (p.seq) return p.seq[FT.seqIdx] !== undefined ? p.seq[FT.seqIdx] : p.rest;
  return FT.isWork ? p.work : (p.rest || 0);
}

function ftTotalRounds(){
  const p = ftPreset();
  if (!p) return 1;
  return p.rounds || (p.seq ? p.seq.length : 1);
}

function ftPaint(left){
  const display = document.getElementById('finisher-display');
  const roundEl = document.getElementById('finisher-round');
  const bar = document.getElementById('finisher-bar');
  const ring = document.getElementById('finisher-ring');
  const total = ftSegLen() || 1;
  if (display) display.textContent = ftFmt(left);
  if (roundEl) roundEl.textContent = 'Раунд ' + FT.round + '/' + ftTotalRounds() + ' — ' + (FT.isWork ? 'Работа' : 'Отдых');
  if (bar) bar.style.width = Math.min(100, Math.max(0, (100 - (left / total) * 100))) + '%';
  if (ring) ring.classList.toggle('active', FT.isWork);
}

function ftStopTick(){
  if (ftTimer) { clearInterval(ftTimer); ftTimer = null; }
}

function ftFinishNaturally(doneText){
  ftStopTick();
  try { S.has_completed_finisher = true; } catch (e) {}
  try { if (typeof saveWorkoutDraft === 'function') saveWorkoutDraft(); } catch (e) {}
  const display = document.getElementById('finisher-display');
  if (display) display.textContent = doneText || 'Готово!';
  ftBeep(880, 400);
  setTimeout(function(){
    if (typeof showSection === 'function') showSection('active-workout');
    const blk = document.getElementById('finisher-block');
    if (blk) { blk.style.borderColor = 'rgba(34,197,94,.5)'; }
  }, 1500);
}

function ftAdvance(){
  const mode = FT.mode;
  const p = ftPreset();
  if (mode === 'tabata' || mode === '30-30' || mode === 'emom'){
    if (!FT.isWork){
      FT.round++;
      if (FT.round > p.rounds){ ftFinishNaturally('Готово!'); return; }
    }
    FT.isWork = !FT.isWork;
  } else if (mode === 'pyramid'){
    const nextIsWork = !FT.isWork;
    if (nextIsWork){
      FT.seqIdx++;
      if (FT.seqIdx >= p.seq.length){ ftFinishNaturally('Готово!'); return; }
    }
    FT.isWork = nextIsWork;
  } else if (mode === 'amrap'){
    ftFinishNaturally('Время!');
    return;
  }
  FT.segmentEndAt = Date.now() + ftSegLen() * 1000;
}

window.startFinisherMode = function(mode){
  const preset = FT_MODES[mode];
  if (!preset) return;
  try { if (typeof AGAudio !== 'undefined') AGAudio.unlock(); } catch (e) {}
  FT.mode = mode;
  FT.round = 1;
  FT.isWork = true;
  FT.seqIdx = 0;
  FT.segmentEndAt = Date.now() + (preset.seq ? preset.seq[0] : preset.work) * 1000;
  const lbl = document.getElementById('finisher-mode-label');
  if (lbl) lbl.textContent = preset.label;
  const blk = document.getElementById('finisher-block');
  if (blk) blk.style.borderColor = '';
  if (typeof showSection === 'function') showSection('finisher-screen');
  ftStopTick();
  ftPaint(ftSegLen());
  ftTimer = setInterval(function(){
    const left = Math.max(0, (FT.segmentEndAt - Date.now()) / 1000);
    ftPaint(left);
    if (left <= 0){
      ftBeep(FT.isWork ? 660 : 440, 200);
      ftAdvance();
    }
  }, 200);
};

window.stopFinisherMode = function(){
  ftStopTick();
  if (typeof showSection === 'function') showSection('active-workout');
};

// Перехват legacy-кнопок: startFinisher()/stopFinisher() теперь ведут в новый движок.
try {
  if (typeof window.startFinisher === 'function') window._legacyStartFinisher = window.startFinisher;
} catch (e) {}
window.startFinisher = function(mode){ return window.startFinisherMode(mode); };
try {
  if (typeof window.stopFinisher === 'function') window._legacyStopFinisher = window.stopFinisher;
} catch (e) {}
window.stopFinisher = function(){ return window.stopFinisherMode(); };

window.FT_MODES = FT_MODES;
})();
