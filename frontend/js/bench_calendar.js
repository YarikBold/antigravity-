// bench_calendar.js [6] — вкладка «Жим-календарь»: сетка Пн-Пт, модалка «Записать факт», AMRAP авто-буст (+5 кг при >=3 повт. на 88%)

let BC_STATE = { base: 82.5, month: null, data: null };

function bcLocalStorageBase(){ return parseFloat(localStorage.getItem('bc_base_1rm') || '0') || 0; }

async function loadBench(){
  try{
    const today = new Date();
    const qs = new URLSearchParams({ year: today.getFullYear(), month: today.getMonth()+1 });
    if(S.userId) qs.set('user_id', S.userId);
    const lsBase = bcLocalStorageBase();
    if(lsBase > 0) qs.set('base_1rm', lsBase);
    const data = await api('/api/bench/calendar?' + qs.toString());
    BC_STATE.data = data;
    BC_STATE.base = data.base_1rm;
    localStorage.setItem('bc_base_1rm', String(data.base_1rm));
    renderBench();
  }catch(e){
    const cont = document.getElementById('bench-body');
    if(cont) cont.innerHTML = `<div class="glass p-4 text-red-400">Ошибка загрузки: ${e.message}</div>`;
  }
}

function renderBench(){
  const d = BC_STATE.data;
  if(!d) return;
  const el = document.getElementById('bench-body');
  if(!el) return;

  const inTarget = d.base_1rm >= d.target.min;
  el.innerHTML = `
    <div class="glass p-4 mb-4 grad-border">
      <div class="flex items-center justify-between mb-2">
        <div>
          <div class="text-gray-400 text-xs uppercase font-bold">База 1ПМ</div>
          <div class="text-3xl font-black grad-text">${d.base_1rm} кг</div>
        </div>
        <div class="text-right">
          <div class="text-gray-400 text-xs">Цель цикла</div>
          <div class="text-white font-bold">${d.target.min}–${d.target.max} кг</div>
          <div class="text-xs ${inTarget ? 'text-green-400' : 'text-yellow-400'}">${inTarget ? '🎯 Цель достигнута!' : `${(d.target.min - d.base_1rm).toFixed(1)} кг до цели`}</div>
        </div>
      </div>
      <div class="text-xs text-gray-500">Старт от рекорда 75×3 → e1RM 82.5 кг. AMRAP: ${d.amrap.rule}</div>
    </div>
    <div class="flex items-center justify-between mb-3">
      <div class="text-white font-bold">${monthName(d.month.month)} ${d.month.year}</div>
      <div class="text-xs text-gray-500">${d.base_source === 'server' ? 'база синхронизирована' : 'база с устройства'}</div>
    </div>
    <div class="bc-grid mb-1">${['ПН','ВТ','СР','ЧТ','ПТ'].map(x=>`<div class="text-center text-[10px] font-black text-gray-500">${x}</div>`).join('')}</div>
    ${d.weeks.map((week, wi) => `
      <div class="bc-week-label">Неделя ${wi+1}${wi===2 ? ' • AMRAP' : ''}</div>
      <div class="bc-grid">
        ${week.map(cell => cell ? bcCellHTML(cell) : '<div class="bc-cell empty"></div>').join('')}
      </div>
    `).join('')}
  `;
}

function monthName(m){ return ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'][m-1]; }

function bcCellHTML(cell){
  if(cell.type === 'info'){
    return `<div class="bc-card info"><div class="bc-dnum">${cell.day} (${cell.dow})</div><div class="bc-ofp">${cell.title}</div></div>`;
  }
  const amrapBadge = cell.amrap ? '<span class="bc-amrap">AMRAP 🔥</span>' : '';
  const delta = cell.percent_delta > 0 ? `<span class="text-[9px] text-yellow-400">+${cell.percent_delta}%</span>` : '';
  return `
    <div class="bc-card ${cell.type} ${cell.logged ? 'done-day' : ''}">
      <div class="bc-title">${cell.day}-е (${cell.dow}) — ${cell.title}</div>
      <div><span class="bc-badge ${cell.type}">${cell.percent}%</span> ${delta}</div>
      <div class="bc-weight">${cell.weight} кг <span class="text-[10px] text-gray-400 font-normal">${cell.sets}×${cell.reps}</span></div>
      <div class="bc-plates">${cell.plates.map(p=>`<span class="plate-chip" style="background:${PLATE_COLORS[p]};color:${p===5?'#000':'#fff'}">${p}</span>`).join('')}</div>
      ${amrapBadge}
      <button class="bc-log-btn" onclick="bcOpenModal('${cell.date}', '${cell.type}', ${cell.weight}, ${cell.amrap ? 1 : 0})">${cell.logged ? '✓ Записано' : 'Записать факт'}</button>
    </div>`;
}

let bcModal = { date: null, type: 'heavy', weight: 0, amrap: false };

function bcOpenModal(date, type, weight, amrap){
  bcModal = { date, type, weight, amrap };
  document.getElementById('bm-title').textContent = `${date} — ${type === 'heavy' ? 'Тяжелый жим' : 'Скоростной жим'}`;
  document.getElementById('bm-planned').textContent = weight + ' кг';
  document.getElementById('bm-weight').value = weight;
  document.getElementById('bm-reps').value = type === 'heavy' ? 4 : 7;
  document.getElementById('bm-sets').value = 4;
  document.getElementById('bm-amrap-row').style.display = (type === 'heavy' && amrap) ? 'block' : 'none';
  document.getElementById('bm-result').innerHTML = '';
  document.getElementById('bench-modal').classList.add('active');
}

function bcCloseModal(){ document.getElementById('bench-modal').classList.remove('active'); }

async function bcSave(){
  const btn = document.getElementById('bm-save');
  btn.innerHTML = '<span class="spinner"></span> Сохранение...'; btn.disabled = true;
  const payload = {
    user_id: S.userId,
    date: bcModal.date,
    day_type: bcModal.type,
    planned_weight: bcModal.weight,
    actual_weight: parseFloat(document.getElementById('bm-weight').value) || bcModal.weight,
    reps: parseInt(document.getElementById('bm-reps').value) || 0,
    sets_done: parseInt(document.getElementById('bm-sets').value) || 0,
    amrap_reps: bcModal.amrap ? (parseInt(document.getElementById('bm-amrap-reps').value) || 0) : null
  };
  try{
    const r = await api('/api/bench/log-day', { method: 'POST', body: JSON.stringify(payload) });
    const res = document.getElementById('bm-result');
    if(r.boosted){
      BC_STATE.base = r.new_base;
      localStorage.setItem('bc_base_1rm', String(r.new_base));
      res.innerHTML = `<div class="text-green-400 font-bold text-sm">🚀 ${r.message}</div><div class="text-gray-400 text-xs mt-1">Календарь пересчитан под новые рабочие веса</div>`;
      setTimeout(async ()=>{ bcCloseModal(); await loadBench(); }, 1600);
    } else {
      res.innerHTML = `<div class="text-green-400 text-sm">✓ ${r.message}</div>`;
      setTimeout(async ()=>{ bcCloseModal(); await loadBench(); }, 900);
    }
  }catch(e){
    document.getElementById('bm-result').innerHTML = `<div class="text-red-400 text-sm">${e.message}</div>`;
  }
  btn.innerHTML = 'Сохранить'; btn.disabled = false;
}
