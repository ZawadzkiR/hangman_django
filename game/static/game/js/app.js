(() => {
  function formBody(payload) {
    const body = new URLSearchParams();
    Object.entries(payload).forEach(([k, v]) => body.append(k, v));
    return body;
  }

  async function post(url, payload, csrf) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body: formBody(payload || {}),
      credentials: 'same-origin',
    });
    let data = {};
    try {
      data = await response.json();
    } catch (e) {
      data = { ok: false };
    }
    data.__status = response.status;
    if (data.redirect) {
      window.location.href = data.redirect;
    }
    return data;
  }


  let audioCtx = null;
  function ensureAudio() {
    if (!audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      audioCtx = new Ctx();
    }
    if (audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
  }
  function beep(type = 'tap') {
    const ctx = ensureAudio();
    if (!ctx) return;
    const now = ctx.currentTime;
    const notes = {
      tap: [[620, 0.03, 0.02]],
      hit: [[740, 0.04, 0.04], [920, 0.06, 0.03]],
      miss: [[280, 0.05, 0.04], [220, 0.08, 0.02]],
      done: [[520, 0.06, 0.05], [660, 0.08, 0.04], [820, 0.12, 0.03]],
      next: [[460, 0.04, 0.03], [580, 0.05, 0.02]],
    };
    (notes[type] || notes.tap).forEach(([freq, dur, gain], idx) => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      g.gain.setValueAtTime(0.0001, now + idx * 0.06);
      g.gain.exponentialRampToValueAtTime(gain, now + idx * 0.06 + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.06 + dur);
      osc.connect(g).connect(ctx.destination);
      osc.start(now + idx * 0.06);
      osc.stop(now + idx * 0.06 + dur + 0.01);
    });
  }

  function updateHangman(selector, mistakes, maxMistakes = 6) {
    const parts = Array.from(document.querySelectorAll(selector));
    const total = parts.length || 1;
    const shown = Math.max(0, Math.min(total, Math.ceil((Number(mistakes || 0) / Math.max(1, Number(maxMistakes || 1))) * total)));
    parts.forEach((el, index) => {
      el.classList.toggle('visible', index < shown);
    });
  }

  const single = document.getElementById('game-app');
  if (single) {
    const csrf = single.dataset.csrf;
    const wordLine = document.getElementById('word-line');
    const usedLetters = document.getElementById('used-letters');
    const mistakesValue = document.getElementById('mistakes-value');
    const remainingValue = document.getElementById('remaining-value');
    const categoryText = document.getElementById('category-text');
    const liveMessage = document.getElementById('live-message');
    const runScore = document.getElementById('run-score');
    const streakValue = document.getElementById('streak-value');
    const modal = document.getElementById('game-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalText = document.getElementById('modal-text');
    const modalScore = document.getElementById('modal-score-value');
    const modalWord = document.getElementById('modal-word-value');
    const winActions = document.getElementById('modal-win-actions');
    const lossActions = document.getElementById('modal-loss-actions');
    const continueBtn = document.getElementById('continue-btn');
    const saveBtn = document.getElementById('save-score-btn');
    const skipBtn = document.getElementById('skip-save-btn');
    const playAgainBtn = document.getElementById('play-again-btn');
    const saveFeedback = document.getElementById('save-feedback');
    const usernameInput = document.getElementById('save-username');

    function updateKeyboard(used) {
      const usedSet = new Set((used || []).map((x) => x.toUpperCase()));
      document.querySelectorAll('.key-btn').forEach((btn) => {
        const isUsed = usedSet.has(btn.dataset.letter.toUpperCase());
        btn.disabled = isUsed;
        btn.classList.toggle('used', isUsed);
      });
    }
    function closeModal() { modal.classList.add('hidden'); modal.setAttribute('aria-hidden', 'true'); }
    function openModal(type, game) {
      modal.classList.remove('hidden');
      modal.setAttribute('aria-hidden', 'false');
      modalTitle.textContent = type === 'won' ? single.dataset.wonLabel : single.dataset.lostLabel;
      modalText.textContent = type === 'won' ? single.dataset.wonText : single.dataset.lostText;
      modalScore.textContent = game.run_score || 0;
      modalWord.textContent = game.word || '';
      winActions.classList.toggle('hidden', type !== 'won');
      lossActions.classList.toggle('hidden', type !== 'lost');
      saveFeedback.textContent = '';
      saveFeedback.className = 'save-feedback';
    }
    function renderGame(game, stats) {
      wordLine.textContent = stats.masked_word;
      usedLetters.textContent = stats.guessed_letters.length ? stats.guessed_letters.map((x) => x.toUpperCase()).join(', ') : single.dataset.noneLabel;
      mistakesValue.textContent = game.mistakes;
      remainingValue.textContent = stats.remaining;
      categoryText.textContent = game.category;
      runScore.textContent = game.run_score || 0;
      streakValue.textContent = game.streak || 0;
      updateHangman('.hang-part:not(.room-part)', game.mistakes, game.max_mistakes);
      updateKeyboard(stats.guessed_letters);
      if (game.status === 'playing') closeModal();
    }
    document.querySelectorAll('#keyboard .key-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        if (btn.disabled) return;
        const data = await post(single.dataset.guessUrl, { letter: btn.dataset.letter }, csrf);
        if (!data.ok) return;
        beep(data.already_used ? 'tap' : (data.hit ? 'hit' : 'miss'));
        liveMessage.textContent = data.already_used ? `${single.dataset.alreadyUsed}: ${btn.dataset.letter}` : `${data.hit ? single.dataset.hitMsg : single.dataset.missMsg}: ${btn.dataset.letter}`;
        liveMessage.className = `live-message ${data.hit ? 'hit' : 'miss'}`;
        renderGame(data.game, data.stats);
        if (data.modal) openModal(data.modal, data.game);
      });
    });
    continueBtn?.addEventListener('click', async () => {
      liveMessage.textContent = single.dataset.nextWord;
      closeModal();
      beep('next');
      const data = await post(single.dataset.newRoundUrl, {}, csrf);
      if (data.ok) renderGame(data.game, data.stats);
    });
    saveBtn?.addEventListener('click', async () => {
      const data = await post(single.dataset.saveUrl, { username: usernameInput.value.trim() }, csrf);
      if (data.ok) { saveFeedback.textContent = data.message; saveFeedback.className = 'save-feedback ok'; }
    });
    skipBtn?.addEventListener('click', async () => {
      const data = await post(single.dataset.saveUrl, { username: '' }, csrf);
      if (data.ok) { saveFeedback.textContent = data.message; saveFeedback.className = 'save-feedback skip'; }
    });
    playAgainBtn?.addEventListener('click', async () => {
      closeModal();
      beep('next');
      const data = await post(single.dataset.newRoundUrl, {}, csrf);
      if (data.ok) renderGame(data.game, data.stats);
    });
    updateHangman('.hang-part:not(.room-part)', Number(mistakesValue.textContent || 0), Number((document.getElementById('mistakes-value')?.parentElement?.textContent || '/6').split('/').pop() || 6));
  }

  const room = document.getElementById('room-app');
  if (room) {
    const csrf = room.dataset.csrf;
    const roomWord = document.getElementById('room-word-line');
    const roomCategory = document.getElementById('room-category-text');
    const roomUsed = document.getElementById('room-used-letters');
    const roomRemaining = document.getElementById('room-remaining-value');
    const roomStatus = document.getElementById('room-status-text');
    const roomRevealBanner = document.getElementById('room-reveal-banner');
    const roomRevealWord = document.getElementById('room-reveal-word');
    const roomTimer = document.getElementById('room-timer-value');
    const roomRound = document.getElementById('room-round-value');
    const roomScore = document.getElementById('room-score-value');
    const roomPlayers = document.getElementById('room-players-list');
    const roomKeyboard = document.getElementById('room-keyboard');
    const roomLive = document.getElementById('room-live-message');
    const roomReadyCount = document.getElementById('room-ready-count');
    const roomPlayerCount = document.getElementById('room-player-count');
    const roomPlayerCountHost = document.getElementById('room-player-count-host');
    const roomAnswerStat = document.getElementById('room-answer-stat');
    const roomModeText = document.getElementById('room-mode-text');
    const roomCurrentTurn = document.getElementById('room-current-turn');
    const roomLanguageLock = document.getElementById('room-language-lock');
    const roomUsedLabel = document.getElementById('room-used-label');
    const roomAnswerValue = document.getElementById('room-answer-value');
    const roomMaxMistakes = document.getElementById('room-max-mistakes');
    const startBtn = document.getElementById('room-start-btn');
    const nextBtn = document.getElementById('room-next-btn');
    const readyBtn = document.getElementById('room-ready-btn');
    const leaveBtn = document.getElementById('room-leave-btn');
    const modal = document.getElementById('room-modal');
    const modalTitle = document.getElementById('room-modal-title');
    const modalText = document.getElementById('room-modal-text');
    const finalTable = document.getElementById('room-final-table');
    const modalWord = document.getElementById('room-modal-word');
    const modalClose = document.getElementById('room-modal-close');
    const roundSummary = document.getElementById('room-round-summary');
    const summaryWord = document.getElementById('room-summary-word');
    const summaryLeader = document.getElementById('room-summary-leader');
    const summaryTitle = document.getElementById('room-summary-title');
    const statusLabels = {
      waiting: room.dataset.statusWaiting,
      playing: room.dataset.statusPlaying,
      round_over: room.dataset.statusRoundOver,
      finished: room.dataset.statusFinished,
    };
    let roomStateVersion = 0;
    let lastRoundPopupKey = null;
    let forcedRoundEndKey = null;
    let forcedRoundEndRound = null;
    let dismissedRoundPopupKey = null;
    const autoReloadStorageKey = `hangman-room-round-refresh:${window.location.pathname}`;

    function statusBadge(p, labels, state) {
      if (state?.room?.mode === 'coop' && p.status === 'playing') {
        if (p.is_current_turn) return `<span class="status-badge playing">👉 ${p.is_you ? room.dataset.yourTurnLabel : room.dataset.currentTurnLabel}</span>`;
        return `<span class="status-badge idle">⏳ ${room.dataset.waitingTurnLabel}</span>`;
      }
      const map = {
        playing: ['⏳', labels[p.status] || p.status, 'playing'],
        won: ['✅', labels[p.status] || p.status, 'won'],
        lost: ['❌', labels[p.status] || p.status, 'lost'],
        timeout: ['⌛', labels[p.status] || p.status, 'timeout'],
        idle: [p.is_ready ? '🟢' : '⚪', p.is_ready ? 'Ready' : 'Not ready', p.is_ready ? 'ready' : 'idle'],
      };
      const [icon, text, cls] = map[p.status] || ['•', labels[p.status] || p.status, 'idle'];
      return `<span class="status-badge ${cls}">${icon} ${text}</span>`;
    }
    function renderPlayers(players, labels, state) {
      roomPlayers.innerHTML = players.map((p, index) => `
        <div class="player-pill compact ${p.is_you ? 'you' : ''} status-${p.status}">
          <div class="player-pill-main">
            <strong>${index + 1}. ${p.nickname}${p.is_host ? ' ⭐' : ''}</strong>
            <span class="player-pill-score">${p.score}</span>
          </div>
          <div class="player-pill-meta">
            ${statusBadge(p, labels, state)}
            <small>${state?.room?.mode === 'coop' ? (p.is_current_turn ? (p.is_you ? room.dataset.yourTurnLabel : room.dataset.currentTurnLabel) : room.dataset.waitingTurnLabel) : (p.status === 'playing' ? 'Still solving…' : (p.is_ready ? 'Ready for next round' : 'Waiting'))}</small>
          </div>
        </div>`).join('');
    }
    function buildKeyboard(letters, used, disabled) {
      const usedSet = new Set((used || []).map((x) => x.toUpperCase()));
      roomKeyboard.innerHTML = letters.map((letter) => `
        <button type="button" class="key-btn ${usedSet.has(letter.toUpperCase()) ? 'used' : ''}" data-letter="${letter}" ${(usedSet.has(letter.toUpperCase()) || disabled) ? 'disabled' : ''}>${letter}</button>
      `).join('');
      roomKeyboard.querySelectorAll('.key-btn').forEach((btn) => btn.addEventListener('click', guessLetter));
    }
    async function guessLetter(ev) {
      const letter = ev.currentTarget.dataset.letter;
      const data = await post(room.dataset.guessUrl, { letter }, csrf);
      if (!data.ok) return;
      beep(data.already_used ? 'tap' : (data.hit ? 'hit' : 'miss'));
      roomLive.textContent = data.already_used ? `${room.dataset.alreadyUsed}: ${letter}` : `${data.hit ? room.dataset.hitMsg : room.dataset.missMsg}: ${letter}`;
      roomLive.className = `live-message ${data.hit ? 'hit' : 'miss'}`;
      renderState(data.state);
    }
    function renderRankingTable(state) {
      finalTable.innerHTML = state.final_ranking.map((p, i) => `<tr><td>${i + 1}</td><td>${p.nickname}</td><td>${p.score}</td></tr>`).join('');
    }
    function revealWord(state) {
      return state?.room?.revealed_word || state?.you?.current_word || state?.room?.current_word_text || '—';
    }
    function openModal(state, finished = false) {
      modal.classList.remove('hidden');
      modal.setAttribute('aria-hidden', 'false');
      document.body.classList.add('room-modal-open');
      const youStatus = state?.you?.status || '';
      const leader = (state.final_ranking || [])[0];
      if (finished) {
        modalTitle.textContent = room.dataset.statusFinished;
        modalText.textContent = state.room.winner_name ? `${room.dataset.winnerLabel}: ${state.room.winner_name}` : room.dataset.statusFinished;
      } else {
        if (youStatus === 'won') modalTitle.textContent = state.labels?.won || room.dataset.statusRoundOver;
        else if (youStatus === 'lost') modalTitle.textContent = state.labels?.lost || room.dataset.statusRoundOver;
        else if (youStatus === 'timeout') modalTitle.textContent = state.labels?.timeout || room.dataset.statusRoundOver;
        else modalTitle.textContent = room.dataset.statusRoundOver;
        modalText.textContent = leader ? `${room.dataset.finalTableLabel}: ${leader.nickname} (${leader.score})` : room.dataset.statusRoundOver;
      }
      if (modalWord) modalWord.textContent = revealWord(state);
      renderRankingTable(state);
      if (modalClose) modalClose.classList.toggle('hidden', finished);
    }
    function closeModal(force = false) {
      if (!force && modal?.dataset?.lockOpen === '1') return;
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('room-modal-open');
    }
    function effectiveRoomStatus(data) {
      const roomStatus = data?.room?.status || 'waiting';
      if (roomStatus === 'finished' || roomStatus === 'round_over') return roomStatus;
      const players = data?.players || [];
      if (players.length && players.every((p) => ['won', 'lost', 'timeout'].includes(p.status))) {
        return 'round_over';
      }
      if (['won', 'lost', 'timeout'].includes(data?.you?.status)) {
        return 'round_over';
      }
      return roomStatus;
    }
    function allPlayersFinished(data) {
      const players = data?.players || [];
      return !!players.length && players.every((p) => ['won', 'lost', 'timeout'].includes(p.status));
    }
    function shouldShowRoundPopup(data, effectiveStatus) {
      return effectiveStatus === 'finished' || effectiveStatus === 'round_over' || ['won', 'lost', 'timeout'].includes(data?.you?.status);
    }
    function shouldShowRoundWord(data) {
      const roomStatus = data?.room?.status || 'waiting';
      return roomStatus === 'finished' || roomStatus === 'round_over' || allPlayersFinished(data) || ['won', 'lost', 'timeout'].includes(data?.you?.status) || !!data?.room?.can_next;
    }
    function roundPopupKey(data, effectiveStatus) {
      const ranking = (data.final_ranking || []).map((p) => `${p.nickname}:${p.score}:${p.status}`).join('|');
      return `${data?.room?.round_number || 0}:${effectiveStatus}:${data?.you?.status || ''}:${revealWord(data)}:${ranking}`;
    }
    function detectRoundEndKey(data, effectiveStatus) {
      if (effectiveStatus === 'finished' || effectiveStatus === 'round_over' || ['won', 'lost', 'timeout'].includes(data?.you?.status) || !!data?.room?.can_next) {
        return roundPopupKey(data, effectiveStatus);
      }
      return null;
    }
    function maybeAutoReloadForRoundEnd(data, effectiveStatus) {
      const key = detectRoundEndKey(data, effectiveStatus);
      if (!key) {
        if (effectiveStatus === 'playing' && data?.you?.status === 'playing') {
          sessionStorage.removeItem(autoReloadStorageKey);
        }
        return false;
      }
      const lastReloadedKey = sessionStorage.getItem(autoReloadStorageKey);
      if (lastReloadedKey === key) return false;
      sessionStorage.setItem(autoReloadStorageKey, key);
      setTimeout(() => {
        window.location.replace(`${window.location.pathname}?r=${Date.now()}`);
      }, 80);
      return true;
    }
    function renderState(data, version = null) {
      if (version !== null && version < roomStateVersion) return;
      if (version !== null) roomStateVersion = version;
      const effectiveStatus = effectiveRoomStatus(data);
      const previousPopupKey = lastRoundPopupKey;
      if (maybeAutoReloadForRoundEnd(data, effectiveStatus)) return;
      roomWord.textContent = data.you.stats.masked_word;
      if (roomModeText) roomModeText.textContent = data.room.mode === 'coop' ? room.dataset.modeCoop : room.dataset.modeVs;
      if (roomCurrentTurn) roomCurrentTurn.textContent = data.room.current_turn_nickname || '—';
      if (roomLanguageLock) roomLanguageLock.classList.toggle('hidden', data.room.mode !== 'coop');
      if (roomUsedLabel) roomUsedLabel.textContent = (data.room.mode === 'coop' ? room.dataset.sharedLettersLabel : room.dataset.usedLettersLabel || 'Used') + ':';
      roomCategory.textContent = data.room.current_category || '—';
      const showRevealBanner = shouldShowRoundWord(data);
      if (roomRevealBanner) roomRevealBanner.classList.toggle('hidden', !showRevealBanner);
      if (roomRevealWord && showRevealBanner) roomRevealWord.textContent = revealWord(data);
      if (roomMaxMistakes) roomMaxMistakes.textContent = data.room.max_mistakes;
      roomUsed.textContent = data.you.stats.guessed_letters.length ? data.you.stats.guessed_letters.map((x) => x.toUpperCase()).join(', ') : room.dataset.noneLabel;
      roomRemaining.textContent = data.you.stats.remaining;
      roomStatus.textContent = data.room.mode === 'coop' && data.you.status === 'playing' ? (data.room.is_current_turn ? room.dataset.yourTurnLabel : room.dataset.waitingTurnLabel) : (data.labels[data.you.status] || data.you.status);
      roomTimer.textContent = data.room.seconds_left;
      roomRound.textContent = `${data.room.round_number}/${data.room.max_rounds}`;
      roomScore.textContent = data.you.score;
      roomReadyCount.textContent = `${data.room.ready_count}/${data.room.player_count}`;
      roomPlayerCount.textContent = `${data.room.player_count}`;
      if (roomPlayerCountHost) roomPlayerCountHost.textContent = `${data.room.player_count}`;
      const revealInline = ['won', 'lost', 'timeout'].includes(data.you.status) || ['round_over', 'finished'].includes(effectiveStatus) || !!data.room.can_next;
      if (roomAnswerStat) roomAnswerStat.classList.toggle('hidden', !revealInline);
      if (roomAnswerValue && revealInline) roomAnswerValue.textContent = revealWord(data);
      updateHangman('.room-part', data.room.mode === 'coop' ? data.room.shared_mistakes : data.you.mistakes, data.room.max_mistakes);
      buildKeyboard(data.you.stats.keyboard, data.you.stats.guessed_letters, effectiveStatus !== 'playing' || data.you.status !== 'playing' || (data.room.mode === 'coop' && !data.room.is_current_turn));
      renderPlayers(data.players, data.labels, data);
      if (roundSummary) {
        const showRoundSummary = showRevealBanner;
        roundSummary.classList.toggle('hidden', !showRoundSummary);
        if (showRoundSummary) {
          if (summaryTitle) summaryTitle.textContent = effectiveStatus === 'finished' ? room.dataset.statusFinished : room.dataset.statusRoundOver;
          if (summaryWord) summaryWord.textContent = revealWord(data);
          if (summaryLeader) {
            const leader = (data.final_ranking || [])[0];
            summaryLeader.textContent = leader ? `${leader.nickname} (${leader.score})` : '—';
          }
        }
      }
      if (readyBtn) {
        readyBtn.textContent = data.you.is_ready ? room.dataset.readyDone : room.dataset.readyLabel;
        readyBtn.classList.toggle('strong', data.you.is_ready);
        readyBtn.disabled = effectiveStatus === 'playing' || effectiveStatus === 'finished';
      }
      if (startBtn) startBtn.classList.toggle('hidden', !data.room.can_start && effectiveStatus !== 'round_over');
      if (nextBtn) nextBtn.classList.toggle('hidden', !(data.room.can_next || (data.room.is_host && effectiveStatus === 'round_over')));

      const detectedRoundEndKey = detectRoundEndKey(data, effectiveStatus);
      if (forcedRoundEndRound !== null && Number(data.room.round_number) !== Number(forcedRoundEndRound) && effectiveStatus === 'playing') {
        forcedRoundEndKey = null;
        forcedRoundEndRound = null;
        dismissedRoundPopupKey = null;
      }
      if (detectedRoundEndKey) {
        forcedRoundEndKey = detectedRoundEndKey;
        forcedRoundEndRound = Number(data.room.round_number || 0);
      }

      const popupKey = forcedRoundEndKey || roundPopupKey(data, effectiveStatus);
      const showPopup = (!!forcedRoundEndKey || shouldShowRoundPopup(data, effectiveStatus)) && popupKey !== dismissedRoundPopupKey;
      if (showPopup && popupKey !== lastRoundPopupKey) beep('done');
      modal.dataset.lockOpen = showPopup ? '1' : '0';
      if (showPopup) {
        if (popupKey !== lastRoundPopupKey || modal.classList.contains('hidden')) {
          openModal(data, effectiveStatus === 'finished');
          lastRoundPopupKey = popupKey;
        } else {
          openModal(data, effectiveStatus === 'finished');
        }
      } else {
        if (popupKey !== dismissedRoundPopupKey) lastRoundPopupKey = null;
        closeModal(true);
      }
    }
    async function pollState() {
      const version = roomStateVersion + 1;
      const sep = room.dataset.stateUrl.includes('?') ? '&' : '?';
      const url = `${room.dataset.stateUrl}${sep}_=${Date.now()}`;
      const response = await fetch(url, { cache: 'no-store', credentials: 'same-origin' });
      let data = {};
      try {
        data = await response.json();
      } catch (e) {
        data = { ok: false };
      }
      if (data.redirect) {
        window.location.href = data.redirect;
        return;
      }
      if (data.ok) renderState(data.state, version);
    }
    readyBtn?.addEventListener('click', async () => { beep('tap'); roomStateVersion += 1; const data = await post(room.dataset.readyUrl, {}, csrf); if (data.ok) renderState(data.state, roomStateVersion); });
    startBtn?.addEventListener('click', async () => { beep('next'); roomStateVersion += 1; const data = await post(room.dataset.startUrl, {}, csrf); if (data.ok) renderState(data.state, roomStateVersion); else if (data.message) roomLive.textContent = data.message; });
    nextBtn?.addEventListener('click', async () => { beep('next'); roomStateVersion += 1; const data = await post(room.dataset.nextRoundUrl, {}, csrf); if (data.ok) renderState(data.state, roomStateVersion); });
    leaveBtn?.addEventListener('click', async () => { const data = await post(room.dataset.leaveUrl, {}, csrf); if (data.ok && data.redirect) window.location.href = data.redirect; });
    modalClose?.addEventListener('click', () => {
      dismissedRoundPopupKey = forcedRoundEndKey || lastRoundPopupKey;
      modal.dataset.lockOpen = '0';
      closeModal(true);
    });
    setInterval(pollState, 1000);
    pollState();
  }

  const uiLangSwitch = document.getElementById('ui-language-switch');
  if (uiLangSwitch) {
    uiLangSwitch.addEventListener('change', async () => {
      await post(uiLangSwitch.dataset.url, { language: uiLangSwitch.value }, uiLangSwitch.dataset.csrf);
      window.location.reload();
    });
  }


  const openRoomsForm = document.getElementById('open-rooms-form');
  if (openRoomsForm) {
    const list = document.getElementById('open-rooms-list');
    const url = openRoomsForm.dataset.openRoomsUrl;
    async function loadOpenRooms() {
      const response = await fetch(`${url}?_=${Date.now()}`, { cache: 'no-store', credentials: 'same-origin' });
      let data = {};
      try { data = await response.json(); } catch (e) { data = { ok: false }; }
      if (!data.ok || !list) return;
      if (!(data.rooms || []).length) {
        list.innerHTML = '<p class="chalk-small">No free rooms right now.</p>';
        return;
      }
      list.innerHTML = data.rooms.map((r) => `
        <article class="open-room-card">
          <div class="open-room-head"><strong>${r.code}</strong><span>${r.player_count} players</span></div>
          <div class="open-room-meta">
            <span>Host: ${r.host_name}</span>
            <span>Ready: ${r.ready_count}/${r.player_count}</span>
            <span>Mode: ${r.mode === 'coop' ? 'Co-op' : 'VS'}</span>
            <span>Lang: ${r.language.toUpperCase()}</span>
            <span>Time: ${r.turn_seconds}s</span>
            <span>Rounds: ${r.max_rounds}</span>
          </div>
          <button type="submit" class="tray-btn open-room-join-btn" name="room_code" value="${r.code}">Join room</button>
        </article>
      `).join('');
    }
    setInterval(loadOpenRooms, 5000);
    loadOpenRooms();
  }

  document.querySelectorAll('.dynamic-category-form').forEach((form) => {
    const languageSelect = form.querySelector('select[name="language"]');
    const categorySelect = form.querySelector('.category-select');
    const url = form.dataset.categoriesUrl;
    if (!languageSelect || !categorySelect || !url) return;
    async function reloadCategories() {
      const response = await fetch(`${url}?language=${encodeURIComponent(languageSelect.value)}&_=${Date.now()}`, { cache: 'no-store', credentials: 'same-origin' });
      const data = await response.json();
      if (!data.ok) return;
      const current = categorySelect.value;
      categorySelect.innerHTML = data.categories.map((item) => `<option value="${item.value}">${item.value === 'random' ? categorySelect.dataset.randomLabel || 'Random' : item.label}</option>`).join('');
      if ([...categorySelect.options].some((o) => o.value === current)) categorySelect.value = current;
    }
    languageSelect.addEventListener('change', reloadCategories);
  });

})();


document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-tabs]').forEach((tabsRoot) => {
    const buttons = Array.from(tabsRoot.querySelectorAll('.tab-btn'));
    const panels = Array.from(tabsRoot.querySelectorAll('.tab-panel'));
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.tabTarget;
        buttons.forEach((b) => b.classList.toggle('active', b === btn));
        panels.forEach((panel) => panel.classList.toggle('active', panel.id === targetId));
      });
    });
  });
});
