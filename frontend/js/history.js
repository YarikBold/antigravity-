// history.js [1] — календарь истории тренировок + Read-Only детальный просмотр сессии

let histMonth = new Date().getMonth() + 1;
let histYear = new Date().getFullYear();
let histSelectedDate = null;
let histData = null;

const MONTH_NAMES_RU = [
  'Январь','Февраль','Март','Апрель','Май','Июнь',
  'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
];

const WEEKDAY_SHORT = ['вс','пн','вт','ср','чт','пт','сб'];

function shiftHistoryMonth(delta) {
  histMonth += delta;
  if (histMonth > 12) { histMonth = 1; histYear++; }
  if (histMonth < 1)  { histMonth = 12; histYear--; }
  histSelectedDate = null;
  loadHistoryCalendar();
}

function localDateKey(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

async function loadHistoryCalendar() {
  if (!S.userId) return;
  const label = document.getElementById('hist-month-label');
  if (label) label.textContent = MONTH_NAMES_RU[histMonth - 1] + ' ' + histYear;

  try {
    histData = await api('/api/history/calendar/' + S.userId + '?month=' + histMonth + '&year=' + histYear);
    histData.completed_dates = (histData.completed_dates || []).map(d => String(d).slice(0, 10));
    (histData.sessions || []).forEach(s => { s.date = String(s.date || '').slice(0, 10); });
  } catch (e) {
    console.error('history calendar failed', e);
    histData = { month: histMonth, year: histYear, completed_dates: [], sessions: [] };
  }

  renderHistoryGrid();
  renderHistorySessions();
  if (typeof refreshIcons === 'function') refreshIcons();
}

function renderHistoryGrid() {
  const grid = document.getElementById('hist-grid');
  if (!grid || !histData) return;
  grid.innerHTML = '';

  const year = histData.year;
  const month = histData.month;
  const completedSet = new Set(histData.completed_dates || []);

  const firstDay = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0);
  const daysInMonth = lastDay.getDate();

  // Offset: Monday=0 ... Sunday=6
  let startDow = firstDay.getDay(); // 0=Sun
  startDow = startDow === 0 ? 6 : startDow - 1; // convert to Mon-based

  const today = new Date();
  const todayStr = localDateKey(today);

  // Prev month filler
  const prevMonth = new Date(year, month - 1, 0);
  for (let i = startDow - 1; i >= 0; i--) {
    const d = prevMonth.getDate() - i;
    const div = document.createElement('div');
    div.className = 'hist-day other-month';
    div.textContent = d;
    grid.appendChild(div);
  }

  // Current month days
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = year + '-' + String(month).padStart(2, '0') + '-' + String(d).padStart(2, '0');
    const hasWorkout = completedSet.has(dateStr);
    const isToday = dateStr === todayStr;
    const isSelected = dateStr === histSelectedDate;

    const div = document.createElement('div');
    let cls = 'hist-day';
    if (hasWorkout) cls += ' has-workout';
    if (isToday) cls += ' today-marker';
    if (isSelected) cls += ' selected';
    div.className = cls;
    div.textContent = d;
    div.onclick = () => {
      histSelectedDate = dateStr;
      renderHistoryGrid();
      renderHistorySessions();
    };

    grid.appendChild(div);
  }

  // Next month filler
  const totalCells = startDow + daysInMonth;
  const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remaining; i++) {
    const div = document.createElement('div');
    div.className = 'hist-day other-month';
    div.textContent = i;
    grid.appendChild(div);
  }
}

function renderHistorySessions() {
  const cont = document.getElementById('hist-sessions');
  if (!cont || !histData) return;

  let sessions = histData.sessions || [];

  if (histSelectedDate) {
    sessions = sessions.filter(s => s.date === histSelectedDate);
  }

  if (!sessions.length) {
    if (histSelectedDate) {
      cont.innerHTML = '<div class="text-gray-500 text-sm text-center py-4">Нет тренировок за выбранную дату</div>';
    } else {
      cont.innerHTML = '<div class="text-gray-500 text-sm text-center py-4">Нет завершённых тренировок в этом месяце</div>';
    }
    return;
  }

  let html = '';

  // Group by date
  const grouped = {};
  sessions.forEach(s => {
    if (!grouped[s.date]) grouped[s.date] = [];
    grouped[s.date].push(s);
  });

  const dates = Object.keys(grouped).sort().reverse();

  dates.forEach(dateStr => {
    const d = new Date(dateStr + 'T00:00:00');
    const dayName = WEEKDAY_SHORT[d.getDay()];
    const dayNum = d.getDate();
    const monthName = MONTH_NAMES_RU[d.getMonth()].toLowerCase();

    html += `<div class="hist-date-label">${dayNum} ${monthName}, ${dayName}</div>`;

    grouped[dateStr].forEach(s => {
      const dayLabel = s.day_number ? getDayLetter(s.day_number) : '';
      const duration = s.total_duration_minutes ? formatDurationMinutes(s.total_duration_minutes) : '';
      const subtitle = [dayLabel, s.exercise_count + ' упр', s.set_count + ' подходов'].filter(Boolean).join(' • ');

      html += `
        <div class="hist-session-card" onclick="openHistoryDetail('${s.log_id}')">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-white font-bold text-sm">${s.plan_name || 'Тренировка'}</div>
              <div class="text-gray-400 text-xs mt-1">${subtitle}</div>
            </div>
            <div class="text-right flex-shrink-0">
              ${duration ? `<div class="text-white font-mono font-bold text-sm">${duration}</div>` : ''}
              <div class="text-gray-500 text-xs">${s.session_type === 'cardio' ? 'Кардио' : 'Силовая'}</div>
            </div>
          </div>
        </div>
      `;
    });
  });

  cont.innerHTML = html;
}

function getDayLetter(dayNum) {
  const letters = { 1: 'День А', 2: 'День Б', 3: 'День В', 4: 'День Г' };
  return letters[Number(dayNum)] || ('День ' + dayNum);
}

function sessionIntensity(dayNum, sessionType) {
  if (sessionType === 'cardio' || Number(dayNum) === 4) return 'Кардио';
  if (Number(dayNum) === 1) return 'Тяжёлый';
  if (Number(dayNum) === 2) return 'Объём';
  if (Number(dayNum) === 3) return 'Скоростной';
  return '';
}

function formatDurationMinutes(mins) {
  if (!mins || mins <= 0) return '';
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h > 0) return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':00';
  return '00:' + String(m).padStart(2, '0') + ':00';
}

async function openHistoryDetail(logId) {
  const cont = document.getElementById('ro-exercises');
  const badges = document.getElementById('ro-badges');
  const title = document.getElementById('ro-date-title');
  if (cont) cont.innerHTML = '<div class="text-center py-8"><div class="spinner mx-auto mb-3"></div><div class="text-gray-400 text-sm">Загрузка...</div></div>';

  showSection('history-detail');

  try {
    const data = await api('/api/history/session/' + logId);

    // Date title
    if (title) {
      const d = new Date(data.date + 'T00:00:00');
      const dayName = WEEKDAY_SHORT[d.getDay()];
      const dayNum = d.getDate();
      const monthName = MONTH_NAMES_RU[d.getMonth()];
      title.textContent = dayNum + ' ' + monthName + ', ' + dayName;
    }

    // Badges
    if (badges) {
      let badgesHtml = '';
      if (data.plan_name) badgesHtml += `<span class="ro-badge plan">${data.plan_name}</span>`;
      if (data.day_number) badgesHtml += `<span class="ro-badge day">${getDayLetter(data.day_number)}</span>`;
      const intensity = sessionIntensity(data.day_number, data.session_type);
      if (intensity) badgesHtml += `<span class="ro-badge">${intensity}</span>`;
      badges.innerHTML = badgesHtml;
    }

    // Exercises — СТРОГО Read-Only: никаких кнопок, инпутов, чекбоксов
    if (cont) {
      if (!data.exercises || !data.exercises.length) {
        cont.innerHTML = '<div class="text-gray-500 text-sm text-center py-4">Нет данных о подходах</div>';
      } else {
        let html = '';
        data.exercises.forEach(ex => {
          html += `<div class="ro-exercise">`;
          html += `<div class="ro-exercise-name">`;
          html += `<i data-lucide="${getExerciseIcon(ex.equipment)}" class="w-5 h-5 text-purple flex-shrink-0"></i>`;
          html += `${ex.name}`;
          if (ex.is_assisted) html += ` <span class="text-[10px] px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/25">гравитрон</span>`;
          html += `</div>`;

          ex.sets.forEach(s => {
            html += `<div class="ro-set">`;
            html += `<div class="ro-set-num">${s.set_number}</div>`;

            const isCardioMove = ex.movement_pattern === 'cardio' || (s.duration_seconds && !(s.reps > 0) && !ex.is_assisted);
            if (ex.is_assisted && s.weight !== null && s.weight !== undefined) {
              html += `<div class="ro-set-val">−${s.weight} кг <span class="text-gray-500 text-[11px]">(поддержка)</span></div>`;
            } else if (isCardioMove) {
              const km = (s.weight !== null && s.weight !== undefined && Number(s.weight) > 0) ? Number(s.weight) + ' км' : '';
              let timeLabel = '';
              if (s.duration_seconds) {
                const m = Math.round(s.duration_seconds / 60);
                timeLabel = m + ' мин';
              }
              html += `<div class="ro-set-val">${km || timeLabel || '—'}</div>`;
              html += `<div class="ro-set-val text-right">${km && timeLabel ? timeLabel : (s.reps != null ? s.reps + ' повт.' : '—')}</div>`;
              html += `</div>`;
              return;
            } else if (s.weight !== null && s.weight !== undefined) {
              html += `<div class="ro-set-val">${s.weight} кг</div>`;
            } else if (s.duration_seconds) {
              const m = Math.floor(s.duration_seconds / 60);
              const sec = s.duration_seconds % 60;
              html += `<div class="ro-set-val">${m > 0 ? m + ' мин ' : ''}${sec > 0 ? sec + ' сек' : ''}</div>`;
            } else {
              html += `<div class="ro-set-val">—</div>`;
            }

            if (s.reps !== null && s.reps !== undefined) {
              html += `<div class="ro-set-val text-right">${s.reps}</div>`;
            } else if (s.completed_rounds) {
              html += `<div class="ro-set-val text-right">${s.completed_rounds} кругов</div>`;
            } else {
              html += `<div class="ro-set-val text-right">—</div>`;
            }

            html += `</div>`;
          });

          html += `</div>`;
        });
        cont.innerHTML = html;
      }
    }
  } catch (e) {
    console.error('history detail failed', e);
    if (cont) cont.innerHTML = `<div class="text-red-400 text-sm text-center py-4">Ошибка: ${e.message}</div>`;
  }

  if (typeof refreshIcons === 'function') refreshIcons();
}

function getExerciseIcon(equipment) {
  const map = {
    'barbell': 'dumbbell',
    'dumbbell': 'dumbbell',
    'machine': 'cog',
    'cable': 'cable-car',
    'bodyweight': 'user',
    'band': 'link',
    'kettlebell': 'flame',
  };
  return map[equipment] || 'circle-dot';
}

function goBackToHistory() {
  showSection('history');
}

function goToHistory() {
  const now = new Date();
  histMonth = now.getMonth() + 1;
  histYear = now.getFullYear();
  histSelectedDate = localDateKey(now);
  showSection('history');
}
