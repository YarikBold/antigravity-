// workout.js — логгер подходов и прогрессия
function renderWorkoutBadge(){
  const badge=document.getElementById('workout-badge'); if(!badge) return;
  const startDate=new Date(S.user.created_at||(Date.now()-30*24*60*60*1000));
  const today=new Date(); const diffWeeks=Math.floor((today-startDate)/(7*24*60*60*1000))+1; const weekNum=Math.max(1,diffWeeks);
  const muscles=S.dayExercises.map(e=>e.exercises.target_muscle);
  const isLower=muscles.some(m=>['quads','hamstrings','glutes'].includes(m));
  const isUpper=muscles.some(m=>['chest','back','shoulders','biceps','triceps'].includes(m));
  let dayType=isLower&&isUpper?'FULL BODY':(isLower?'LOWER':'UPPER');
  badge.innerHTML=`<span class="glass px-3 py-1 text-xs font-bold text-purple">Неделя ${weekNum}</span><span class="glass px-3 py-1 text-xs font-bold text-pink">${dayType}</span><span class="glass px-3 py-1 text-xs text-gray-400">День ${S.selectedDay}</span>`;
}

function renderExerciseCards(){
  const cont=document.getElementById('exercise-cards'); if(!cont) return; cont.innerHTML='';
  S.dayExercises.forEach(ex=>{
    let e=ex.exercises;
    const last=S.lastWeights[String(ex.exercise_id)]||S.lastWeights[ex.exercise_id];
    const tr=parseInt(ex.target_reps?.split('-')[1] || ex.reps_target?.split('-')[1] || ex.target_reps || ex.reps_target || '10');
    let lastHint='';
    if(last){
      const willProgress=last.rir>=1 && last.reps>=tr && last.weight>0;
      const isIso = e.mechanics==='isolation' || (e.cns_load||3)<=2;
      const inc = isIso?1.25:2.5;
      const suggested=willProgress?(parseFloat(last.weight)+inc).toFixed(1):last.weight;
      lastHint=`<div class="text-[11px] mb-2 px-2 py-1 rounded bg-black/20 flex items-center gap-2"><svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m15 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg><span class="text-gray-400">Прошлый раз:</span> <span class="text-white font-mono font-bold">${last.weight}кг ×${last.reps} RIR${last.rir}</span>${willProgress?`<span class="text-green-400">→ рекомендуем ${suggested}кг (+${inc})</span>`:`<span class="text-gray-500">· цель ${ex.target_reps||ex.reps_target}</span>`}</div>`;
    } else {
      lastHint=`<div class="text-[11px] mb-2 text-gray-500">Первый раз — введи вес, мы запомним для след. тренировки</div>`;
    }
    let setsHTML=S.workoutSets[ex.exercise_id].map((s,i)=>`
      <div class="set-row flex items-center gap-2 p-2 rounded-lg border border-transparent ${s.done?'done':''}">
        <span class="text-xs text-gray-500 w-4">#${i+1}</span>
        <input type="number" step="0.5" value="${s.weight!==''?s.weight:''}" placeholder="${last?last.weight:''}" class="input-dark py-1 text-center" onchange="upd('${ex.exercise_id}',${i},'weight',this.value)">
        <span class="text-xs">×</span>
        <input type="number" value="${s.reps!==''?s.reps:''}" placeholder="${last?last.reps:''}" class="input-dark py-1 text-center" onchange="upd('${ex.exercise_id}',${i},'reps',this.value)">
        <span class="text-xs">RIR</span>
        <input type="number" value="${s.rir!==''?s.rir:''}" placeholder="${last?last.rir:2}" class="input-dark py-1 text-center" onchange="upd('${ex.exercise_id}',${i},'rir',this.value)">
        <select onchange="upd('${ex.exercise_id}',${i},'set_type',this.value)" class="input-dark py-1 text-center text-xs w-20"><option value="normal" ${s.set_type==='normal'?'selected':''}>norm</option><option value="drop_set" ${s.set_type==='drop_set'?'selected':''}>drop</option><option value="rest_pause" ${s.set_type==='rest_pause'?'selected':''}>rest</option><option value="pyramid" ${s.set_type==='pyramid'?'selected':''}>pyr</option></select>
        <button onclick="done('${ex.exercise_id}',${i})" class="w-8 h-8 rounded bg-purple/20 text-purple flex items-center justify-center"><svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg></button>
      </div>`).join('');
    cont.innerHTML+=`<div class="glass p-4 border-l-4 border-purple"><div class="text-white font-bold mb-2">${e.name} <span class="text-xs text-gray-500 font-normal">(${ex.target_sets||ex.sets}×${ex.target_reps||ex.reps_target})</span> <span class="text-[10px] px-1.5 py-0.5 rounded bg-purple/20 text-purple">${e.movement_pattern|| e.mechanics||''}</span></div>${lastHint}${setsHTML}</div>`;
  });
  const hint=document.getElementById('progression-hint'); if(hint){ const dismissed=localStorage.getItem('prog_hint_dismissed')==='1'; hint.classList.toggle('hidden', dismissed); }
}
window.upd=(eid,idx,field,val)=>{
  if(field==='set_type'){ S.workoutSets[eid][idx][field]=val; return; }
  const num=parseFloat(val); S.workoutSets[eid][idx][field]=isNaN(num)?'':num;
};
function dismissProgressionHint(){ const h=document.getElementById('progression-hint'); if(h) h.classList.add('hidden'); localStorage.setItem('prog_hint_dismissed','1'); }
window.done=(eid,idx)=>{
  let s=S.workoutSets[eid][idx];
  if(s.weight===''||s.reps===''||s.reps<=0) return alert('Введи вес и повторения (>0)');
  s.done=true;
  let next=S.workoutSets[eid][idx+1];
  if(next && (next.weight===''||next.weight===0)){
    const ex=S.dayExercises.find(x=>String(x.exercise_id)===String(eid));
    const tr=ex?parseInt((ex.target_reps||ex.reps_target).split('-')[1]||ex.target_reps||ex.reps_target):0;
    const isIso=ex && (ex.exercises.mechanics==='isolation' || (ex.exercises.cns_load||3)<=2);
    const inc=isIso?1.25:2.5;
    if(s.rir>=1 && s.reps>=tr && s.weight>0) next.weight=parseFloat((parseFloat(s.weight)+inc).toFixed(2));
    else next.weight=s.weight;
  }
  renderExerciseCards();
  startRestTimer(90);
};

function startWorkout(){
  S.workoutSets={};
  S.dayExercises.forEach(ex=>{
    let arr=[];
    let last=S.lastWeights[String(ex.exercise_id)]||S.lastWeights[ex.exercise_id];
    let defaultW=last?last.weight:0;
    // AI не считает веса, только математика progression.py: +1.25 / +2.5
    if(last && last.weight>0 && last.rir>=1){
      let tr=parseInt((ex.target_reps||ex.reps_target).split('-')[1]||ex.target_reps||ex.reps_target);
      if(last.reps>=tr){
        const isIso=ex.exercises.mechanics==='isolation' || (ex.exercises.cns_load||3)<=2;
        const inc=isIso?1.25:2.5;
        defaultW=parseFloat((parseFloat(last.weight)+inc).toFixed(2));
      }
    }
    const sets = ex.target_sets||ex.sets||3;
    for(let i=0;i<sets;i++) arr.push({weight:defaultW, reps:0, rir:2, set_type: ex.suggested_method||'normal', done:false});
    S.workoutSets[ex.exercise_id]=arr;
  });
  const dayLabel=document.getElementById('workout-day-label'); if(dayLabel) dayLabel.textContent='День '+S.selectedDay;
  renderWorkoutBadge(); renderExerciseCards(); if(typeof resetTimer==='function') resetTimer();
  S._pendingSubs=[];
  showSection('active-workout');
}

async function finishWorkout(){
  let sets=[]; Object.keys(S.workoutSets).forEach(eid=>{
    S.workoutSets[eid].forEach((s,i)=>{
      if(s.done) sets.push({exercise_id:eid, set_number:i+1, set_type:s.set_type||'normal', weight:Number(s.weight), reps:Number(s.reps), rir:s.rir==='' ? 2 : Number(s.rir)});
    });
  });
  if(!sets.length) return alert('Нет завершённых подходов!');
  const btnFinish=document.getElementById('btn-finish'); if(btnFinish){ btnFinish.innerHTML='<span class="spinner w-4 h-4 border-2"></span> Сохранение...'; btnFinish.disabled=true; }
  try{
    // try new endpoint first
    let res;
    try{
      res=await api('/api/workouts/complete',{method:'POST',body:JSON.stringify({user_id:S.userId, plan_id:S.user.current_plan_id, day_number:S.selectedDay, sets})});
    }catch(e){
      // fallback legacy
      const legacySets=sets.map(s=>({exercise_id: parseInt(s.exercise_id)||s.exercise_id, set_number:s.set_number, weight:s.weight, reps:s.reps, rir:s.rir}));
      res=await api('/api/finish_workout',{method:'POST',body:JSON.stringify({user_id: parseInt(S.userId)||S.userId, day_number:S.selectedDay, sets:legacySets})});
    }
    S.lastWeights=await api('/api/last_weights/'+S.userId);
    const pCont=document.getElementById('progression-results'); if(pCont){
      pCont.innerHTML='';
      if(res.progressions && res.progressions.length){
        res.progressions.forEach(p=>{
          let eName=S.dayExercises.find(e=>String(e.exercise_id)===String(p.exercise_id))?.exercises.name||'Упражнение';
          pCont.innerHTML+=`<div class="glass p-3 mb-2 flex items-center gap-2"><svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"/></svg> ${eName}: <span class="text-gray-400">${p.old_weight} кг</span> → <span class="text-green-400 font-bold">${p.new_weight} кг</span></div>`;
        });
      }
      const stats=document.getElementById('complete-stats'); if(stats) stats.textContent=`Залогировано подходов: ${res.logged||sets.length}`;
    }
    showSection('workout-complete');
  }catch(e){ alert(e.message); }
  if(btnFinish){ btnFinish.innerHTML='<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> Завершить'; btnFinish.disabled=false; }
}
