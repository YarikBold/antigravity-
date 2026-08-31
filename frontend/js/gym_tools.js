// gym_tools.js [18] — Plate Visualizer, Tempo Metronome, Share Card
const BAR_WEIGHT = 20;
const PLATE_COLORS = {25:'#DC2626',20:'#2563EB',15:'#EAB308',10:'#16A34A',5:'#FFFFFF',2.5:'#1F2937',1.25:'#EC4899'};
const PLATE_ORDER = [25,20,15,10,5,2.5,1.25];

function plateBreakdown(total){
  if(total <= BAR_WEIGHT) return [];
  let perSide=(total-BAR_WEIGHT)/2;
  let out=[];
  for(let p of PLATE_ORDER){
    while(perSide>=p-0.001){
      out.push(p);
      perSide=Math.round((perSide-p)*100)/100;
    }
  }
  return out;
}
function renderPlates(totalWeight, containerId){
  const cont=document.getElementById(containerId);
  if(!cont) return;
  const plates=plateBreakdown(totalWeight);
  if(!plates.length){ cont.innerHTML=`<span class="text-xs text-gray-500">Гриф 20кг — диски не нужны</span>`; return; }
  cont.innerHTML = plates.map(p=> `<span class="inline-flex items-center justify-center w-8 h-12 rounded text-[10px] font-bold border" style="background:${PLATE_COLORS[p]};color:${p===5?'#000':'#fff'};border-color:#000">${p}</span>`).join('<span class="mx-0.5 text-gray-600">|</span>') + `<span class="ml-2 text-xs text-gray-400">x2 стороны</span>`;
}

// Tempo metronome 3-0-1-0
let metronomeCtx=null, metroInterval=null, metroBeat=0;
function startMetronome(tempo="3-0-1-0", bpm=60){
  stopMetronome();
  const parts=tempo.split('-').map(Number);
  const phases=['Эксцентрика','Пауза внизу','Концентрика','Пауза вверху'];
  let phaseIdx=0, tick=0;
  const circle=document.getElementById('metronome-circle');
  try{
    metronomeCtx=new (window.AudioContext||window.webkitAudioContext)();
  }catch{}
  const totalBeats=parts.reduce((a,b)=>a+b,0) || 4;
  metroInterval=setInterval(()=>{
    tick++;
    // visual pulse
    if(circle){
      circle.classList.add('active');
      setTimeout(()=>circle.classList.remove('active'), 200);
      const label=document.getElementById('metronome-phase');
      if(label) label.textContent=phases[phaseIdx];
    }
    // click sound on phase change
    if(tick >= parts[phaseIdx]){
      tick=0;
      phaseIdx=(phaseIdx+1)%parts.length;
      try{
        const o=metronomeCtx.createOscillator();
        o.frequency.value = phaseIdx===2 ? 880 : 440;
        o.connect(metronomeCtx.destination);
        o.start(); setTimeout(()=>o.stop(), 80);
      }catch{}
    }
  }, 60000/bpm);
}
function stopMetronome(){
  if(metroInterval){ clearInterval(metroInterval); metroInterval=null; }
  if(metronomeCtx){ try{ metronomeCtx.close(); }catch{} metronomeCtx=null; }
}

// Workout Share Card — итоги + тоннаж + PR + copy for Telegram
function buildShareText(){
  const tonnage = Object.values(S.workoutSets||{}).flat().filter(s=>s.done).reduce((a,s)=>a + (s.weight * s.reps), 0);
  const prLines = (S._newPRs||[]).map(p=> `🏆 Рекорд e1RM ${p.name}: ${p.e1rm}кг`).join('\n');
  const lines = [
    `🏋️ Antigravity — Тренировка ${new Date().toLocaleDateString('ru-RU')}`,
    `👤 ${S.user?.name||''} • План ${S.planData?.plan?.name||''} День ${S.selectedDay||''}`,
    `Тоннаж: ${tonnage.toFixed(1)} кг`,
    prLines,
    `Подходы: ${Object.values(S.workoutSets||{}).flat().filter(s=>s.done).length}`,
    `Сгенерировано в Antigravity 💜`,
  ].filter(Boolean).join('\n');
  return lines;
}
async function shareWorkout(){
  const text=buildShareText();
  try{
    await navigator.clipboard.writeText(text);
    const btn=document.getElementById('btn-share');
    if(btn){ const old=btn.textContent; btn.textContent='Скопировано!'; setTimeout(()=>btn.textContent=old,1500); }
  }catch{
    prompt('Скопируй отчет:', text);
  }
}
