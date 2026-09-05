// gym_tools.js [6] — AudioContext-хаб (user gesture), Plate Visualizer, темпо-метроном (3-0-1-0), Workout Share Card для Telegram

// --- Аудио-хаб: контекст создаётся/возобновляется строго по user gesture ---
const AGAudio = {
  ctx: null,
  unlock(){
    if(!this.ctx){
      try{ this.ctx = new (window.AudioContext || window.webkitAudioContext)(); }catch(e){ this.ctx = null; }
    }
    if(this.ctx && this.ctx.state === 'suspended'){ try{ this.ctx.resume(); }catch(e){} }
    return this.ctx;
  },
  beep(freq, durationMs){
    const ctx = this.unlock();
    if(!ctx) return;
    try{
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      osc.type = 'square';
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + durationMs/1000);
      osc.connect(gain); gain.connect(ctx.destination);
      osc.start(); osc.stop(ctx.currentTime + durationMs/1000);
    }catch(e){}
  }
};
// Разблокировка звука на первом касании/клике (политика автоплея браузера)
document.addEventListener('pointerdown', () => AGAudio.unlock(), { once:true });
document.addEventListener('keydown', () => AGAudio.unlock(), { once:true });

// --- Plate Visualizer: жадный расчёт на олимпийский гриф 20 кг ---
const BAR_WEIGHT = 20;
const PLATE_COLORS = {25:'#DC2626',20:'#2563EB',15:'#EAB308',10:'#16A34A',5:'#FFFFFF',2.5:'#374151',1.25:'#EC4899'};
const PLATE_ORDER = [25,20,15,10,5,2.5,1.25];

function plateBreakdown(total){
  if(!total || total <= BAR_WEIGHT) return [];
  let perSide = (total - BAR_WEIGHT)/2;
  let out = [];
  for(let p of PLATE_ORDER){
    while(perSide >= p - 0.001){
      out.push(p);
      perSide = Math.round((perSide - p)*100)/100;
    }
  }
  return out;
}

function renderPlates(totalWeight, containerId){
  const cont = document.getElementById(containerId);
  if(!cont) return;
  const plates = plateBreakdown(totalWeight);
  if(!plates.length){ cont.innerHTML = `<span class="text-[10px] text-gray-500">Гриф 20кг</span>`; return; }
  cont.innerHTML = plates.map(p =>
    `<span class="plate-chip" style="background:${PLATE_COLORS[p]};color:${p===5?'#000':'#fff'}">${p}</span>`
  ).join('<span class="mx-0.5 text-gray-600">|</span>') + `<span class="ml-1 text-[10px] text-gray-400">×2</span>`;
}

// --- Темпо-метроном 3-0-1-0 (3с эксцентрика, 1с концентрика) ---
let metroInterval = null, metroPhaseIdx = 0, metroTick = 0;

function startMetronome(tempo = "3-0-1-0"){
  stopMetronome();
  const parts = tempo.split('-').map(Number);
  const phases = ['Эксцентрика','Пауза','Концентрика','Пауза'];
  const circle = document.getElementById('metronome-circle');
  metroPhaseIdx = 0; metroTick = 0;
  AGAudio.unlock(); // user gesture от кнопки «Старт»
  metroInterval = setInterval(() => {
    metroTick++;
    if(circle){
      circle.classList.add('active');
      setTimeout(()=>circle.classList.remove('active'), 180);
      const l = document.getElementById('metronome-phase');
      if(l) l.textContent = phases[metroPhaseIdx] + ` ${metroTick}/${parts[metroPhaseIdx] || 1}`;
    }
    if(metroTick >= (parts[metroPhaseIdx] || 1)){
      metroTick = 0;
      metroPhaseIdx = (metroPhaseIdx + 1) % parts.length;
      AGAudio.beep(metroPhaseIdx === 2 ? 880 : 440, 70);
    }
  }, 1000);
}

function stopMetronome(){
  if(metroInterval){ clearInterval(metroInterval); metroInterval = null; }
  const c = document.getElementById('metronome-circle');
  if(c) c.classList.remove('active');
}

// --- Workout Share Card: форматированный текст для Telegram ---
function buildShareText(){
  const tonnage = Object.values(S.workoutSets || {}).flat().filter(s=>s.done).reduce((a,s)=>a+(s.weight*s.reps),0);
  const prLines = (S._newPRs || []).map(p=>`🏆 Рекорд e1RM ${p.name}: ${p.e1rm}кг`).join('\n');
  return [
    `🏋️ Antigravity — ${new Date().toLocaleDateString('ru-RU')}`,
    `👤 ${S.user?.name || ''} • ${S.planData?.plan?.name || ''} ${typeof dayLabelText==='function' ? dayLabelText(S.selectedDay) : ('День ' + (S.selectedDay||''))}`,
    `Тоннаж: ${tonnage.toFixed(1)} кг`,
    prLines,
    `Подходов: ${Object.values(S.workoutSets || {}).flat().filter(s=>s.done).length}`,
    `Antigravity 💜`
  ].filter(Boolean).join('\n');
}

async function shareWorkout(){
  const t = buildShareText();
  try{
    await navigator.clipboard.writeText(t);
    const b = document.getElementById('btn-share');
    if(b){ const o = b.innerHTML; b.textContent = 'Скопировано!'; setTimeout(()=>b.innerHTML = o, 1500); }
  }catch{ prompt('Скопируй отчет:', t); }
}
