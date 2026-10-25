(() => {
  const $ = (id) => document.getElementById(id);
  const audio = $('audio');
  const playPause = $('playPause');
  const stopButton = $('stopButton');
  const volume = $('volume');
  const sleepTimer = $('sleepTimer');
  const playbackStatus = $('playbackStatus');
  const timerStatus = $('timerStatus');
  const playerIcon = $('playerIcon');
  const playerTitle = $('playerTitle');
  const playerDescription = $('playerDescription');
  const trackList = $('trackList');
  const uploadInput = $('musicUpload');
  const uploadStatus = $('uploadStatus');
  const DB_NAME = 'rechers_sound_library';
  const STORE_NAME = 'tracks';
  const MAX_UPLOAD = 20 * 1024 * 1024;
  const state = {
    currentSrc: null,
    currentId: null,
    timerId: null,
    timerEnd: 0,
    dbPromise: null,
    idbWorking: null,
    memoryTracks: [],
    uploadUrls: new Map(),
  };

  function setPlaybackStatus(text) { playbackStatus.textContent = text || ''; }
  function setTimerStatus(text) { timerStatus.textContent = text || ''; }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  }

  function formatLeft(ms) {
    const total = Math.max(0, Math.ceil(ms / 1000));
    const minutes = Math.floor(total / 60);
    const seconds = String(total % 60).padStart(2, '0');
    return minutes + ':' + seconds;
  }

  function setCardLabels() {
    const playing = !audio.paused && Boolean(state.currentSrc);
    document.querySelectorAll('.sound-card').forEach((card) => {
      const active = card.dataset.src === state.currentSrc;
      card.classList.toggle('is-playing', active);
      const button = card.querySelector('.card-play');
      if (button) button.textContent = active && playing ? 'Pause' : 'Play';
    });
    playPause.textContent = playing ? 'Pause' : 'Play';
  }

  function loadTrack(info) {
    state.currentSrc = info.src;
    state.currentId = info.id || null;
    audio.src = info.src;
    audio.volume = Number(volume.value);
    playerIcon.textContent = info.icon || '🎧';
    playerTitle.textContent = info.title || 'Sound';
    playerDescription.textContent = info.description || '';
    playPause.disabled = false;
    stopButton.disabled = false;
    setCardLabels();
    setPlaybackStatus('Loading ' + (info.title || 'audio') + '…');
    audio.play().then(() => {
      setPlaybackStatus('Playing ' + (info.title || 'audio') + '.');
    }).catch(() => {
      setPlaybackStatus('This audio could not start. Try another track.');
    });
  }

  function clearPlayer(message) {
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    state.currentSrc = null;
    state.currentId = null;
    state.timerEnd = 0;
    if (state.timerId) window.clearInterval(state.timerId);
    state.timerId = null;
    sleepTimer.value = '0';
    playerIcon.textContent = '🎧';
    playerTitle.textContent = 'Choose a sound';
    playerDescription.textContent = 'Nothing is playing yet. Pick a card below or add your own track.';
    playPause.disabled = true;
    stopButton.disabled = true;
    setCardLabels();
    setPlaybackStatus(message || '');
    setTimerStatus('');
  }

  function updateSleepTimer() {
    if (!state.timerEnd) {
      setTimerStatus('');
      return;
    }
    const left = state.timerEnd - Date.now();
    if (left <= 0) {
      audio.pause();
      state.timerEnd = 0;
      if (state.timerId) window.clearInterval(state.timerId);
      state.timerId = null;
      sleepTimer.value = '0';
      setPlaybackStatus('Sleep timer finished. Sound paused.');
      setTimerStatus('');
      return;
    }
    setTimerStatus('Sound will pause in ' + formatLeft(left) + '.');
  }

  function startSleepTimer(minutes) {
    if (state.timerId) window.clearInterval(state.timerId);
    state.timerId = null;
    state.timerEnd = minutes ? Date.now() + minutes * 60 * 1000 : 0;
    if (!minutes) {
      setTimerStatus('');
      return;
    }
    updateSleepTimer();
    state.timerId = window.setInterval(updateSleepTimer, 1000);
  }

  document.querySelectorAll('.sound-card').forEach((card) => {
    const info = {
      src: card.dataset.src,
      title: card.dataset.title,
      description: card.dataset.description,
      icon: card.dataset.icon,
    };
    const start = () => {
      if (state.currentSrc === info.src) {
        if (audio.paused) {
          audio.play().then(() => setPlaybackStatus('Playing ' + info.title + '.')).catch(() => {
            setPlaybackStatus('This audio could not start. Try another track.');
          });
        } else {
          audio.pause();
        }
        return;
      }
      loadTrack(info);
    };
    const button = card.querySelector('.card-play');
    if (button) button.addEventListener('click', (event) => { event.stopPropagation(); start(); });
    card.addEventListener('click', (event) => {
      if (event.target.closest('.card-play')) return;
      start();
    });
  });

  playPause.addEventListener('click', () => {
    if (!state.currentSrc) return;
    if (audio.paused) {
      audio.play().catch(() => setPlaybackStatus('This audio could not start. Try another track.'));
    } else {
      audio.pause();
    }
  });

  stopButton.addEventListener('click', () => {
    if (!state.currentSrc) return;
    audio.pause();
    audio.currentTime = 0;
    setPlaybackStatus('Sound stopped.');
  });

  volume.addEventListener('input', () => { audio.volume = Number(volume.value); });

  sleepTimer.addEventListener('change', () => {
    startSleepTimer(Number(sleepTimer.value));
  });

  audio.addEventListener('play', () => {
    setPlaybackStatus('Playing ' + (playerTitle.textContent || 'audio') + '.');
    setCardLabels();
  });
  audio.addEventListener('pause', () => {
    setCardLabels();
    if (state.timerEnd) updateSleepTimer();
  });
  audio.addEventListener('error', () => {
    if (!state.currentSrc) return;
    setPlaybackStatus('This audio could not load. Try another track.');
  });

  const filterButtons = Array.from(document.querySelectorAll('.filter-chip'));
  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      filterButtons.forEach((item) => item.classList.toggle('is-active', item === button));
      const selected = button.dataset.filter;
      document.querySelectorAll('.sound-card').forEach((card) => {
        const show = selected === 'All' || card.dataset.category === selected;
        card.classList.toggle('is-hidden', !show);
      });
    });
  });

  function openDb() {
    if (!('indexedDB' in window)) return Promise.reject(new Error('IndexedDB unavailable'));
    if (state.dbPromise) return state.dbPromise;
    state.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      };
      request.onsuccess = () => { state.idbWorking = true; resolve(request.result); };
      request.onerror = () => { state.idbWorking = false; reject(request.error || new Error('Database unavailable')); };
    });
    return state.dbPromise;
  }

  async function getUploads() {
    try {
      const db = await openDb();
      return await new Promise((resolve, reject) => {
        const request = db.transaction(STORE_NAME, 'readonly').objectStore(STORE_NAME).getAll();
        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      state.idbWorking = false;
      return state.memoryTracks.slice();
    }
  }

  async function saveUpload(record) {
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).put(record);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      state.idbWorking = false;
      state.memoryTracks.push(record);
    }
  }

  async function removeUpload(id) {
    try {
      const db = await openDb();
      await new Promise((resolve, reject) => {
        const request = db.transaction(STORE_NAME, 'readwrite').objectStore(STORE_NAME).delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      state.idbWorking = false;
      state.memoryTracks = state.memoryTracks.filter((item) => item.id !== id);
    }
  }

  function titleFromFile(name) {
    return name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 60) || 'My audio';
  }

  function makeTrackCard(track, url) {
    const card = document.createElement('div');
    card.className = 'track-card';
    const icon = document.createElement('div');
    icon.className = 'track-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '🎵';
    const copy = document.createElement('div');
    copy.className = 'track-copy';
    const title = document.createElement('strong');
    title.textContent = track.title;
    const meta = document.createElement('span');
    meta.textContent = formatBytes(track.size) + (state.idbWorking === false ? ' · this session only' : ' · saved in this browser');
    copy.append(title, meta);
    const actions = document.createElement('div');
    actions.className = 'track-actions';
    const play = document.createElement('button');
    play.type = 'button';
    play.textContent = 'Play';
    play.addEventListener('click', () => {
      if (state.currentId === track.id && !audio.paused) {
        audio.pause();
        return;
      }
      if (state.currentId === track.id) {
        audio.play().catch(() => setPlaybackStatus('This audio could not start. Try another track.'));
        return;
      }
      loadTrack({
        src: url,
        title: track.title,
        description: 'Your audio · ' + formatBytes(track.size),
        icon: '🎵',
        id: track.id,
      });
    });
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'remove-track';
    remove.textContent = 'Remove';
    remove.addEventListener('click', async () => {
      if (!window.confirm('Remove this track from your browser?')) return;
      if (state.currentId === track.id) clearPlayer('Track removed.');
      await removeUpload(track.id);
      const objectUrl = state.uploadUrls.get(track.id);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      state.uploadUrls.delete(track.id);
      await refreshTracks();
      uploadStatus.textContent = 'Removed ' + track.title + '.';
    });
    actions.append(play, remove);
    card.append(icon, copy, actions);
    return card;
  }

  async function refreshTracks() {
    const items = await getUploads();
    trackList.replaceChildren();
    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'empty-tracks';
      empty.textContent = 'No music added yet. Choose an audio file to keep it in this browser.';
      trackList.appendChild(empty);
      return;
    }
    items.sort((a, b) => (b.addedAt || 0) - (a.addedAt || 0));
    items.forEach((track) => {
      let url = state.uploadUrls.get(track.id);
      if (!url) {
        url = URL.createObjectURL(track.blob);
        state.uploadUrls.set(track.id, url);
      }
      trackList.appendChild(makeTrackCard(track, url));
    });
  }

  uploadInput.addEventListener('change', async () => {
    const files = Array.from(uploadInput.files || []);
    if (!files.length) return;
    let saved = 0;
    const rejected = [];
    for (const file of files) {
      const looksAudio = (file.type && file.type.startsWith('audio/')) || /\.(mp3|wav|ogg|m4a|aac|flac|webm)$/i.test(file.name);
      if (!looksAudio) { rejected.push(file.name + ' is not an audio file'); continue; }
      if (file.size > MAX_UPLOAD) { rejected.push(file.name + ' is larger than 20 MB'); continue; }
      uploadStatus.textContent = 'Saving ' + file.name + '…';
      await saveUpload({
        id: (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : String(Date.now()) + '-' + Math.random().toString(16).slice(2),
        title: titleFromFile(file.name),
        size: file.size,
        type: file.type || 'audio',
        blob: file,
        addedAt: Date.now(),
      });
      saved += 1;
    }
    uploadInput.value = '';
    await refreshTracks();
    const lines = [];
    if (saved) lines.push('Added ' + saved + ' track' + (saved === 1 ? '' : 's') + '.');
    if (rejected.length) lines.push(rejected.join(' '));
    if (saved && state.idbWorking === false) lines.push('This browser could not keep files after a refresh, so they will last for this session only.');
    uploadStatus.textContent = lines.join(' ') || 'No tracks were added.';
  });

  window.addEventListener('beforeunload', () => {
    state.uploadUrls.forEach((url) => URL.revokeObjectURL(url));
  });

  audio.volume = Number(volume.value);
  refreshTracks();
  setCardLabels();
})();
