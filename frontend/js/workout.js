// workout.js [6] — силовой экран: сеты, RIR-подсказки (suggest-next-set), калькулятор блинов, завершение

function startWorkout() {
  try{
    S.workoutSets = {};
    S.setHints = {};
    S._newPRs = [];
    S.dayExercises.forEach(ex => {
      let arr = [];
      let last = S.lastWeights[String(ex.exercise_id)] || S.lastWeights[ex.exercise_id];
      let defaultW = last ? last.weight : 0;
      if (last && last.weight > 0 && last.rir >= 1) {
        let repStr = ex.target_reps || ex.reps_target || '8-12';
        let tr = parseInt(String(repStr).split('-')[1] || repStr);
        if (last.reps >= tr) defaultW = parseFloat((parseFloat(last.weight) + 2.5).toFixed(2));
      }
      const sets = ex.target_sets || ex.sets || 3;
      for(let i=0; i<sets; i++) arr.push({ weight: defaultW, reps: 0, rir: 2, done: false, set_type: 'normal' });
      S.workoutSets[ex.exercise_id] = arr;
    });
    const dayLabel = document.getElementById('workout-day-label');
    if (dayLabel) dayLabel.textContent = dayLabelText(S.selectedDay);
    renderWorkoutBadge();
    renderExerciseCards();
    resetTimer();
    showSection('active-workout');
  }catch(e){ alert('Ошибка startWorkout: '+ e.message); console.error(e); }
}

function renderWorkoutBadge() {
  const badge = document.getElementById('workout-badge');
  if (!badge) return;

  const startDate = new Date(S.user.created_at || (Date.now() - 30*24*60*60*1000));
  const today = new Date();
  const diffWeeks = Math.floor((today - startDate) / (7 * 24 * 60 * 60 * 1000)) + 1;
  const weekNum = Math.max(1, diffWeeks);

  const muscles = S.dayExercises.map(e => e.exercises.target_muscle);
  const isLower = muscles.some(m => ['quads','hamstrings','glutes'].includes(m));
  const isUpper = muscles.some(m => ['chest','back','shoulders','biceps','triceps'].includes(m));
  let dayType = isLower && isUpper ? 'FULL BODY' : (isLower ? 'LOWER' : 'UPPER');

  badge.innerHTML = `
    <span class="glass px-3 py-1 text-xs font-bold text-purple">Неделя ${weekNum}</span>
    <span class="glass px-3 py-1 text-xs font-bold text-pink">${dayType}</span>
    <span class="glass px-3 py-1 text-xs text-gray-400">${dayLabelText(S.selectedDay)}</span>
  `;
}

function renderExerciseCards() {
  const cont = document.getElementById('exercise-cards');
  if (!cont) return;
  cont.innerHTML = '';
  S.dayExercises.forEach(ex => {
    let e = ex.exercises;
    const last = S.lastWeights[String(ex.exercise_id)] || S.lastWeights[ex.exercise_id];
    const repStr = ex.target_reps || ex.reps_target || '8-12';
    const tr = parseInt(String(repStr).split('-')[1] || repStr);
    let lastHint = '';
    if(last){
      const willProgress = last.rir >= 1 && last.reps >= tr && last.weight > 0;
      const suggested = willProgress ? (parseFloat(last.weight) + 2.5).toFixed(1) : last.weight;
      lastHint = `<div class="text-[11px] mb-2 px-2 py-1 rounded bg-black/20 flex items-center gap-2">
        <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m15 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
        <span class="text-gray-400">Прошлый раз:</span> <span class="text-white font-mono font-bold">${last.weight}кг ×${last.reps} RIR${last.rir}</span>
        ${willProgress ? `<span class="text-green-400">→ рекомендуем ${suggested}кг</span>` : `<span class="text-gray-500">· цель ${repStr}</span>`}
      </div>`;
    } else {
      lastHint = `<div class="text-[11px] mb-2 text-gray-500">Первый раз — введи вес, мы запомним для след. тренировки</div>`;
    }
    if(!S.workoutSets[ex.exercise_id]) S.workoutSets[ex.exercise_id]=[];
    const methodBadge = (ex.suggested_method && ex.suggested_method!=='normal') ? `<span class="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-pink/20 text-pink border border-pink/30">${ex.suggested_method}</span>` : '';
    const methodHint = (ex.suggested_method && ex.suggested_method!=='normal') ? `<div class="text-[10px] text-pink/80 mb-2">Метод: ${ex.suggested_method} — ${ex.suggested_method==='drop_set'?'дроп-сет: снизь вес после отказа':ex.suggested_method==='rest_pause'?'rest-pause: 15с пауза и ещё подход':ex.suggested_method==='pyramid'?'пирамида: наращивай вес':ex.suggested_method==='amrap'?'AMRAP: максимум за время':ex.suggested_method==='emom'?'EMOM: каждую минуту':''}</div>` : '';
    let setsHTML = S.workoutSets[ex.exercise_id].map((s,i) => {
      const hintKey = String(ex.exercise_id)+':'+i;
      const hint = S.setHints[hintKey] ? `<div class="w-full text-[10px] text-green-400 font-bold px-2">${S.setHints[hintKey]}</div>` : '';
      return `
      <div class="set-row flex flex-wrap items-center gap-2 p-2 rounded-lg border border-transparent ${s.done?'done':''}">
        <span class="text-xs text-gray-500 w-4">#${i+1}</span>
        <input type="number" step="0.5" value="${s.weight !== '' ? s.weight : ''}" placeholder="${last ? last.weight : ''}" class="input-dark py-1 text-center w-20" onchange="upd('${ex.exercise_id}',${i},'weight',this.value)">
        <span class="text-xs">×</span>
        <input type="number" value="${s.reps !== '' ? s.reps : ''}" placeholder="${last ? last.reps : ''}" class="input-dark py-1 text-center w-16" onchange="upd('${ex.exercise_id}',${i},'reps',this.value)">
        <span class="text-xs">RIR</span>
        <input type="number" value="${s.rir !== '' ? s.rir : ''}" placeholder="${last ? last.rir : 2}" class="input-dark py-1 text-center w-12" onchange="upd('${ex.exercise_id}',${i},'rir',this.value)">
        <select onchange="upd('${ex.exercise_id}',${i},'set_type',this.value)" class="input-dark py-1 text-center text-xs w-20"><option value="normal" ${s.set_type==='normal'?'selected':''}>norm</option><option value="drop_set" ${s.set_type==='drop_set'?'selected':''}>drop</option><option value="rest_pause" ${s.set_type==='rest_pause'?'selected':''}>rest</option><option value="pyramid" ${s.set_type==='pyramid'?'selected':''}>pyr</option></select>
        <button onclick="done('${ex.exercise_id}',${i})" class="w-8 h-8 rounded bg-purple/20 text-purple flex items-center justify-center"><svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg></button>
        ${hint}
      </div>`;
    }).join('');

    cont.innerHTML += `<div class="glass p-4 border-l-4 border-purple"><div class="text-white font-bold mb-2 flex flex-wrap items-center gap-1">${e.name} <span class="text-xs text-gray-500 font-normal">(${ex.target_sets||ex.sets||3}×${repStr})</span>${methodBadge}<button onclick="swapExercise('${ex.exercise_id}')" class="ml-auto text-[10px] px-2 py-1 rounded bg-white/10 text-purple border border-purple/20 hover:bg-purple/20">Тренажер занят → Заменить</button></div>${methodHint}${lastHint}<div id="plates-${ex.exercise_id}" class="flex flex-wrap gap-1 my-1"></div>${setsHTML}</div>`;
    setTimeout(()=>{ try{ const w=parseFloat(S.workoutSets[ex.exercise_id]?.[0]?.weight||0); if(w>=20 && typeof renderPlates==='function') renderPlates(w, 'plates-'+ex.exercise_id); }catch{} }, 0);
  });
  const hint = document.getElementById('progression-hint');
  if(hint){
    const dismissed = localStorage.getItem('prog_hint_dismissed') === '1';
    hint.classList.toggle('hidden', dismissed);
  }
}

window.upd = (eid, idx, field, val) => {
  if(field==='set_type'){ S.workoutSets[eid][idx][field]=val; return; }
  const num = parseFloat(val);
  S.workoutSets[eid][idx][field] = isNaN(num) ? '' : num;
  if(field==='weight'){
    try{ const w=parseFloat(val); if(w>=20) renderPlates(w, 'plates-'+eid); }catch{}
  }
};

function dismissProgressionHint(){
  const h = document.getElementById('progression-hint');
  if(h) h.classList.add('hidden');
  localStorage.setItem('prog_hint_dismissed','1');
}

// Локальный fallback RIR-авторегуляции (если API недоступен)
function localSuggest(rir, reps, repStr, weight, mechanics){
  const tr = parseInt(String(repStr).split('-')[1] || repStr) || 10;
  const isIso = mechanics === 'isolation';
  if(rir >= 3) return { action:'increase', next_weight: weight + (isIso ? 2.5 : 5), badge: `+${isIso?2.5:5}кг — легко (RIR ${rir})` };
  if(rir === 2 && reps >= tr) return { action:'increase', next_weight: weight + (isIso ? 1.25 : 2.5), badge: `+${isIso?1.25:2.5}кг — цель выполнена` };
  if(rir === 1 && reps >= tr) return { action:'hold', next_weight: weight, badge: 'фиксируй — идеальная нагрузка' };
  if(rir === 1) return { action:'hold', next_weight: weight, badge: `сделай +${tr-reps} повт. на этом же весе` };
  const dec = Math.max(1.25, Math.round(weight*0.07*4)/4);
  return { action:'decrease', next_weight: Math.max(0, weight-dec), badge: `-${dec}кг — техника (RIR ${rir})` };
}

// RIR-авторегуляция: расчёт веса следующего подхода на лету через /api/workouts/suggest-next-set
async function suggestNextSet(ex, doneSet){
  const repStr = ex.target_reps || ex.reps_target || '8-12';
  const payload = {
    exercise_id: String(ex.exercise_id),
    plan_id: String(S.user.current_plan_id || ''),
    weight: Number(doneSet.weight),
    reps: Number(doneSet.reps),
    rir: Number(doneSet.rir),
    target_reps: repStr,
    mechanics: ex.exercises?.mechanics || 'compound',
    cns_load: ex.exercises?.cns_load || 3,
    target_muscle: ex.exercises?.target_muscle || ''
  };
  try{
    return await api('/api/workouts/suggest-next-set', { method:'POST', body: JSON.stringify(payload) });
  }catch(e){
    console.warn('suggest-next-set failed, local fallback:', e.message);
    return localSuggest(Number(doneSet.rir), Number(doneSet.reps), repStr, Number(doneSet.weight), payload.mechanics);
  }
}

window.done = async (eid, idx) => {
  let s = S.workoutSets[eid]?.[idx];
  if(!s) return alert('Ошибка: подход не найден');
  if(s.weight === '' || s.weight === undefined || s.reps === '' || s.reps === undefined || s.reps <= 0) return alert('Введи вес и повторения (>0)');
  s.done = true;

  const ex = S.dayExercises.find(x=>String(x.exercise_id)===String(eid));
  const mechanics = ex?.exercises?.mechanics || 'compound';

  // Следующий подход: RIR-авторегуляция + подсказка над строкой сета
  const next = S.workoutSets[eid][idx+1];
  if(next && !next.done && (next.weight === '' || next.weight === 0 || next.weight === undefined)){
    const sug = await suggestNextSet(ex || {exercise_id: eid, target_reps:'8-12', exercises:{}}, s);
    if(sug && sug.next_weight){
      next.weight = parseFloat(Number(sug.next_weight).toFixed(2));
      if(sug.badge) S.setHints[String(eid)+':'+(idx+1)] = '💡 ' + sug.badge;
    }
  }

  renderExerciseCards();
  // Динамический отдых: RIR-sensitive (изоляция 60-90с, база RIR<=1 180с / RIR>=2 120с)
  startRestTimer(null, Number(s.rir), mechanics);
};

async function swapExercise(exerciseId){
  const ex=S.dayExercises.find(x=>String(x.exercise_id)===String(exerciseId));
  if(!ex) return alert('Упражнение не найдено');
  const btn=event?.target; const old=btn?btn.textContent:'';
  if(btn) btn.textContent='Подбираю...';
  try{
    const exclude=S.dayExercises.map(x=>x.exercise_id);
    const alt=await api('/api/workouts/swap-exercise',{method:'POST', body:JSON.stringify({exercise_id: exerciseId, exclude_ids: exclude})});
    const oldSets=S.workoutSets[exerciseId];
    ex.exercise_id=alt.id; ex.exercises=alt;
    if(oldSets){ S.workoutSets[alt.id]=oldSets; delete S.workoutSets[exerciseId]; }
    renderExerciseCards();
  }catch(e){ alert('Замена: '+e.message); } finally{ if(btn) btn.textContent=old||'Тренажер занят → Заменить'; }
}

async function finishWorkout() {
  let sets = [];
  Object.keys(S.workoutSets).forEach(eid => {
    S.workoutSets[eid].forEach((s, i) => {
      if(s.done) {
        sets.push({
          exercise_id: eid,
          set_number: i+1,
          set_type: s.set_type||'normal',
          weight: Number(s.weight),
          reps: Number(s.reps),
          rir: s.rir === '' ? 2 : Number(s.rir)
        });
      }
    });
  });

  if(!sets.length) return alert('Нет завершённых подходов!');
  const btnFinish = document.getElementById('btn-finish');
  if (btnFinish) { btnFinish.innerHTML = '<span class="spinner"></span> Сохранение...'; btnFinish.disabled=true; }

  try {
    let res;
    try{
      res = await api('/api/workouts/complete', { method: 'POST', body: JSON.stringify({ user_id: String(S.userId), plan_id: String(S.user.current_plan_id||''), day_number: S.selectedDay, sets }) });
    }catch(e){
      const legacySets = sets.map(s=>({exercise_id: s.exercise_id, set_number: s.set_number, weight: s.weight, reps: s.reps, rir: s.rir}));
      res = await api('/api/finish_workout', { method: 'POST', body: JSON.stringify({ user_id: S.userId, day_number: S.selectedDay, sets: legacySets }) });
    }
    S.lastWeights = await api('/api/last_weights/' + S.userId);

    const pCont = document.getElementById('progression-results');
    if (pCont) {
      pCont.innerHTML = '';
      if(res.progressions && res.progressions.length) {
        res.progressions.forEach(p => {
          let eName = S.dayExercises.find(e => String(e.exercise_id)===String(p.exercise_id))?.exercises.name || 'Упражнение';
          pCont.innerHTML += `<div class="glass p-3 mb-2 flex items-center gap-2"><svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"/></svg> ${eName}: <span class="text-gray-400">${p.old_weight} кг</span> → <span class="text-green-400 font-bold">${p.new_weight} кг</span></div>`;
        });
      }
    }
    showSection('workout-complete');
  } catch(e) { alert(e.message); }
  if (btnFinish) { btnFinish.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> Завершить'; btnFinish.disabled=false; }
}
