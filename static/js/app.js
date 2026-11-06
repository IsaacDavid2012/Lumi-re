// Lumière — TMDB-powered streaming catalog
window.__APP_LOADED__ = true;

const $ = (id) => document.getElementById(id);

const heroBg = $("heroBg");
const heroTitle = $("heroTitle");
const heroType = $("heroType");
const heroMeta = $("heroMeta");
const heroOverview = $("heroOverview");
const heroPlay = $("heroPlay");
const heroWatchlist = $("heroWatchlist");
const heroWatchlistIcon = $("heroWatchlistIcon");
const heroWatchlistLabel = $("heroWatchlistLabel");
const heroInfo = $("heroInfo");
const heroDots = $("heroDots");
const rowsContainer = $("rowsContainer");
const siteHeader = $("siteHeader");

const profileSwitchBtn = $("profileSwitchBtn");
const headerProfileAvatar = $("headerProfileAvatar");
const headerProfileName = $("headerProfileName");
const headerKidsBadge = $("headerKidsBadge");
const profileDialog = $("profileDialog");
const profileDialogTitle = $("profileDialogTitle");
const profileDialogClose = $("profileDialogClose");
const nfProfilePicker = $("nfProfilePicker");
const profileCardsGrid = $("profileCardsGrid");
const nfManageProfilesBtn = $("nfManageProfilesBtn");
const profileCreateForm = $("profileCreateForm");
const editProfileIdInput = $("editProfileId");
const nfEditorTitle = $("nfEditorTitle");
const nfEditorSub = $("nfEditorSub");
const nfEditorAvatarPreview = $("nfEditorAvatarPreview");
const newProfileName = $("newProfileName");
const newProfileKids = $("newProfileKids");
const profileColorSwatches = $("profileColorSwatches");
const createProfileBtn = $("createProfileBtn");
const nfEditorCancelBtn = $("nfEditorCancelBtn");
const nfEditorDeleteBtn = $("nfEditorDeleteBtn");

const homeView = $("homeView");
const browseView = $("browseView");
const searchView = $("searchView");

const browseEyebrow = $("browseEyebrow");
const browseTitle = $("browseTitle");
const browseFilters = $("browseFilters");
const browseGrid = $("browseGrid");
const browseMoreBtn = $("browseMoreBtn");
const browseStatus = $("browseStatus");

const searchForm = $("searchForm");
const searchInput = $("searchInput");
const searchClear = $("searchClear");
const searchTitle = $("searchTitle");
const searchCount = $("searchCount");
const searchGrid = $("searchGrid");
const searchMoreBtn = $("searchMoreBtn");
const searchStatus = $("searchStatus");

const detailDialog = $("detailDialog");
const detailHeroBg = $("detailHeroBg");
const detailType = $("detailType");
const detailTitle = $("detailTitle");
const detailMeta = $("detailMeta");
const detailPlay = $("detailPlay");
const detailWatchlist = $("detailWatchlist");
const detailWatchlistIcon = $("detailWatchlistIcon");
const detailWatchlistLabel = $("detailWatchlistLabel");
const detailTrailerBtn = $("detailTrailerBtn");
const detailTrailerLabel = $("detailTrailerLabel");
const detailTrailerWrap = $("detailTrailerWrap");
const detailTrailerFrame = $("detailTrailerFrame");
const detailTrailer = $("detailTrailer");
const detailTmdb = $("detailTmdb");
const detailOverview = $("detailOverview");
const detailGenres = $("detailGenres");
const detailCastSection = $("detailCastSection");
const detailCast = $("detailCast");
const detailRecSection = $("detailRecSection");
const detailRecommendations = $("detailRecommendations");
const detailPoster = $("detailPoster");
const detailFacts = $("detailFacts");
const episodePanel = $("episodePanel");
const seasonSelect = $("seasonSelect");
const episodeSelect = $("episodeSelect");
const episodeCaption = $("episodeCaption");
const episodeGrid = $("episodeGrid");
const detailClose = $("detailClose");

const playerDialog = $("playerDialog");
const playerTitle = $("playerTitle");
const playerSub = $("playerSub");
const player = $("moviePlayer");
const playerFrameWrap = $("playerFrameWrap");
const playerServer = $("playerServer");
const nativeStreamOption = $("nativeStreamOption");
const playerEpisodeControls = $("playerEpisodeControls");
const playerSeason = $("playerSeason");
const playerEpisode = $("playerEpisode");
const prevEpisodeBtn = $("prevEpisodeBtn");
const nextEpisodeBtn = $("nextEpisodeBtn");
const fullscreenBtn = $("fullscreenBtn");
const playerSource = $("playerSource");
const playerClose = $("playerClose");
const toastEl = $("toast");

const lumiereNativeStage = $("lumiereNativeStage");
const lumiereVideo = $("lumiereVideo");
const lumiereCenterPlay = $("lumiereCenterPlay");
const lumiereTimeline = $("lumiereTimeline");
const lumierePlayBtn = $("lumierePlayBtn");
const lumiereRewBtn = $("lumiereRewBtn");
const lumiereFwdBtn = $("lumiereFwdBtn");
const lumiereMuteBtn = $("lumiereMuteBtn");
const lumiereVolumeSlider = $("lumiereVolumeSlider");
const lumiereTimeLabel = $("lumiereTimeLabel");
const lumiereQualityBadge = $("lumiereQualityBadge");
const lumiereSpeedSelect = $("lumiereSpeedSelect");
const lumierePipBtn = $("lumierePipBtn");

const adminStreamBtn = $("adminStreamBtn");
const adminStreamBar = $("adminStreamBar");
const adminStreamInput = $("adminStreamInput");
const adminStreamClearBtn = $("adminStreamClearBtn");

const subtitleMenuBtn = $("subtitleMenuBtn");
const subtitleCountBadge = $("subtitleCountBadge");
const subtitlePopover = $("subtitlePopover");
const subtitleUploadBtn = $("subtitleUploadBtn");
const subtitleFileInput = $("subtitleFileInput");
const subtitleTrackList = $("subtitleTrackList");
const subtitleOffsetValue = $("subtitleOffsetValue");
const subtitleClockDisplay = $("subtitleClockDisplay");
const subtitleClockToggle = $("subtitleClockToggle");
const subtitleClockBack = $("subtitleClockBack");
const subtitleClockFwd = $("subtitleClockFwd");
const subtitleSizeGroup = $("subtitleSizeGroup");
const subtitleColorGroup = $("subtitleColorGroup");
const subtitleBgToggle = $("subtitleBgToggle");
const lumiereSubtitleOverlay = $("lumiereSubtitleOverlay");
const lumiereSubtitleText = $("lumiereSubtitleText");

const streamLimitOverlay = $("streamLimitOverlay");
const streamLimitMessage = $("streamLimitMessage");
const streamLimitList = $("streamLimitList");
const streamTakeoverBtn = $("streamTakeoverBtn");
const streamLimitCloseBtn = $("streamLimitCloseBtn");

const VIDEO_BASE = "https://vidfast.vc";
const PLAYER_THEME = "E50914";

function generateStreamToken() {
  const bytes = new Uint8Array(12);
  if (window.crypto && window.crypto.getRandomValues) {
    window.crypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  }
  return `st_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}
const TAB_STREAM_TOKEN = generateStreamToken();

const state = {
  view: "home",
  lastView: "home",
  heroItems: [],
  heroIndex: 0,
  heroTimer: null,
  heroPaused: false,
  homeLoaded: false,
  watchlistKeys: new Set(),
  watchlistItems: [],
  activeProfile: null,
  profiles: [],
  profileGateActive: false,
  profileManageMode: false,
  editingProfile: null,
  selectedProfileColor: "#e50914",
  detail: null,
  detailRequestId: 0,
  seasonCache: {},
  search: { query: "", page: 1, totalPages: 1, items: [], requestId: 0 },
  browse: { view: "movies", type: "movie", category: "popular", page: 1, totalPages: 1, items: [], requestId: 0 },
  player: {
    item: null,
    server: "s1",
    directStream: null,
    seasons: [],
    episodes: [],
    season: 1,
    episode: 1,
    startAt: 0,
    currentTime: 0,
    duration: 0,
    requestId: 0,
    heartbeatTimer: null,
  },
  subtitles: {
    tracks: [],
    activeTrackId: "off",
    cues: [],
    offset: 0,
    clockRunning: true,
    lastExternalSync: 0,
    size: "md",
    color: "#ffffff",
    bgMode: "glass",
  },
};

const BROWSE_CONFIG = {
  movies: {
    eyebrow: "Browse movies",
    filters: [
      ["popular", "Popular"],
      ["top_rated", "Top Rated"],
      ["now_playing", "In Theaters"],
      ["upcoming", "Coming Soon"],
      ["trending", "Trending"],
      ["genre_28", "Action"],
      ["genre_878", "Sci-Fi"],
      ["genre_27", "Horror"],
      ["genre_53", "Thriller"],
      ["genre_35", "Comedy"],
      ["genre_18", "Drama"],
      ["genre_16", "Animation & Anime"],
      ["genre_80", "Crime"],
      ["genre_10749", "Romance"],
      ["genre_99", "Documentary"],
      ["genre_10751", "Family"],
    ],
    type: "movie",
    category: "popular",
  },
  tv: {
    eyebrow: "Browse series",
    filters: [
      ["popular", "Popular"],
      ["top_rated", "Top Rated"],
      ["airing_today", "Airing Today"],
      ["on_the_air", "On The Air"],
      ["trending", "Trending"],
      ["genre_10759", "Action & Adventure"],
      ["genre_10765", "Sci-Fi & Fantasy"],
      ["genre_35", "Comedy"],
      ["genre_18", "Drama"],
      ["genre_16", "Animation & Anime"],
      ["genre_80", "Crime & Mystery"],
      ["genre_99", "Docuseries"],
      ["genre_10762", "Kids"],
    ],
    type: "tv",
    category: "popular",
  },
  top: {
    eyebrow: "Highest rated",
    filters: [
      ["top_movies", "Movies"],
      ["top_tv", "TV Shows"],
    ],
    type: "movie",
    category: "top_rated",
  },
  mylist: {
    eyebrow: "Personal collection",
    filters: [
      ["all", "All Saved"],
      ["movie", "Movies"],
      ["tv", "Series"],
    ],
    type: "multi",
    category: "all",
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function showToast(message) {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.classList.add("show");
  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => toastEl.classList.remove("show"), 2400);
}

async function apiFetch(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (res.status === 401) {
    window.location.href = "/login";
    throw new Error("Authentication required");
  }
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || "";
}

let historySaveTimer = null;

function queueHistorySave() {
  clearTimeout(historySaveTimer);
  historySaveTimer = setTimeout(() => saveHistory(false), 900);
}

function getNextTvEpisode() {
  const item = state.player.item;
  if (!item || item.media_type !== "tv") return null;

  const currentSeason = Number(state.player.season) || 1;
  const currentEpNum = Number(state.player.episode) || 1;
  const episodes = state.player.episodes || [];

  // 1. Check if there is another episode in the current season
  const nextInSeason = episodes.find(
    (ep) => Number(ep.episode_number) === currentEpNum + 1
  );
  if (nextInSeason) {
    return {
      season: currentSeason,
      episode: Number(nextInSeason.episode_number),
      episode_name: nextInSeason.name || `Episode ${nextInSeason.episode_number}`,
      is_series_end: false,
    };
  }

  // 2. If at the end of the season, check if a next season exists on the TV show
  const seasons = (item.seasons || []).filter(
    (s) => Number(s.season_number) > 0
  );
  const nextSeasonObj = seasons.find(
    (s) => Number(s.season_number) === currentSeason + 1
  );
  if (nextSeasonObj) {
    return {
      season: currentSeason + 1,
      episode: 1,
      episode_name: `S${currentSeason + 1} E1`,
      is_series_end: false,
    };
  }

  // If episodes array is not loaded, advance to next episode number
  if (!episodes.length) {
    return {
      season: currentSeason,
      episode: currentEpNum + 1,
      episode_name: `Episode ${currentEpNum + 1}`,
      is_series_end: false,
    };
  }

  // 3. Reached end of series
  return {
    season: currentSeason,
    episode: currentEpNum,
    episode_name: "",
    is_series_end: true,
  };
}

async function saveHistory(shouldRefresh = true, isEnded = false) {
  clearTimeout(historySaveTimer);
  const item = state.player.item;
  if (!item || !item.id) return;
  const episode = currentPlayerEpisode();

  const duration = Number(state.player.duration) || 0;
  const currentTime = Number(state.player.currentTime) || 0;
  const isOver = isEnded || (duration > 0 && currentTime >= duration * 0.90);

  let seasonToSave = state.player.season || 1;
  let episodeToSave = state.player.episode || 1;
  let episodeNameToSave = episode?.name || "";
  let progressToSave = currentTime;
  let durationToSave = duration;

  let nextPayload = {};
  if (item.media_type === "tv" && isOver) {
    const next = getNextTvEpisode();
    if (next && !next.is_series_end) {
      seasonToSave = next.season;
      episodeToSave = next.episode;
      episodeNameToSave = next.episode_name || `Episode ${next.episode}`;
      progressToSave = 0;
      durationToSave = 0;
      nextPayload = {
        is_ended: true,
        next_season: next.season,
        next_episode: next.episode,
        next_episode_name: episodeNameToSave,
      };
    } else {
      nextPayload = {
        is_ended: true,
        is_series_end: true,
      };
      progressToSave = duration || 100;
      durationToSave = duration || 100;
    }
  }

  const payload = {
    id: item.id,
    media_type: item.media_type,
    title: displayTitle(item),
    poster_url: item.poster_url || null,
    backdrop_url: item.backdrop_url || null,
    year: item.year || "",
    vote_average: item.vote_average || 0,
    overview: item.overview || "",
    season: seasonToSave,
    episode: episodeToSave,
    episode_name: episodeNameToSave,
    progress_seconds: progressToSave,
    duration_seconds: durationToSave,
    ...nextPayload,
  };
  try {
    const res = await fetch("/api/history", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (res.ok && shouldRefresh) refreshContinueRow();
  } catch (error) {
    console.error(error);
  }
}

let continueRowEl = null;
let watchlistRowEl = null;

function watchlistKey(item) {
  if (!item || !item.id) return "";
  return `${item.media_type === "tv" ? "tv" : "movie"}:${item.id}`;
}

function isInWatchlist(item) {
  return state.watchlistKeys.has(watchlistKey(item));
}

function syncWatchlistState(items) {
  state.watchlistItems = (items || []).filter((item) => item && item.id);
  state.watchlistKeys = new Set(state.watchlistItems.map(watchlistKey));
  syncWatchlistButtons();
}

function syncWatchlistButtons() {
  if (state.currentHero && heroWatchlist) {
    const saved = isInWatchlist(state.currentHero);
    heroWatchlist.classList.toggle("active", saved);
    if (heroWatchlistIcon) heroWatchlistIcon.textContent = saved ? "✓" : "+";
    if (heroWatchlistLabel) heroWatchlistLabel.textContent = saved ? "In My List" : "My List";
  }
  if (state.detail && detailWatchlist) {
    const saved = isInWatchlist(state.detail);
    detailWatchlist.classList.toggle("active", saved);
    if (detailWatchlistIcon) detailWatchlistIcon.textContent = saved ? "✓" : "+";
    if (detailWatchlistLabel) detailWatchlistLabel.textContent = saved ? "In My List" : "My List";
  }
  document.querySelectorAll(".card-watchlist-btn").forEach((btn) => {
    const key = btn.dataset.wlKey || "";
    const saved = state.watchlistKeys.has(key);
    btn.classList.toggle("active", saved);
    btn.textContent = saved ? "✓" : "+";
    btn.title = saved ? "Remove from My List" : "Add to My List";
  });
}

function renderWatchlistRow() {
  if (watchlistRowEl) {
    watchlistRowEl.remove();
    watchlistRowEl = null;
  }
  if (!state.watchlistItems.length) return;
  watchlistRowEl = buildRow({ key: "mylist", title: "My List", items: state.watchlistItems });
  if (continueRowEl && continueRowEl.parentNode === rowsContainer) {
    continueRowEl.insertAdjacentElement("afterend", watchlistRowEl);
  } else {
    rowsContainer.prepend(watchlistRowEl);
  }
}

async function refreshWatchlist() {
  try {
    const data = await apiFetch("/api/watchlist");
    syncWatchlistState(data.items || []);
    if (state.homeLoaded) renderWatchlistRow();
    if (state.view === "browse" && state.browse.view === "mylist") {
      renderMyListBrowse();
    }
  } catch (error) {
    console.error(error);
  }
}

async function toggleWatchlist(item) {
  if (!item || !item.id) return;
  const mediaType = item.media_type === "tv" ? "tv" : "movie";
  const currentlySaved = isInWatchlist(item);
  try {
    if (currentlySaved) {
      const res = await fetch(`/api/watchlist/${mediaType}/${item.id}`, {
        method: "DELETE",
        headers: {
          "X-CSRF-Token": getCsrfToken(),
          Accept: "application/json",
        },
      });
      if (res.ok) {
        showToast(`Removed “${displayTitle(item)}” from My List`);
        await refreshWatchlist();
      }
    } else {
      const res = await fetch("/api/watchlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCsrfToken(),
          Accept: "application/json",
        },
        body: JSON.stringify({
          id: item.id,
          media_type: mediaType,
          title: displayTitle(item),
          poster_url: item.poster_url || null,
          backdrop_url: item.backdrop_url || null,
          year: item.year || "",
          vote_average: item.vote_average || 0,
          overview: item.overview || "",
        }),
      });
      if (res.ok) {
        showToast(`Added “${displayTitle(item)}” to My List`);
        await refreshWatchlist();
      }
    }
  } catch (error) {
    console.error(error);
    showToast("Could not update My List");
  }
}

async function refreshContinueRow() {
  try {
    const data = await apiFetch("/api/history?limit=20");
    if (continueRowEl) {
      continueRowEl.remove();
      continueRowEl = null;
    }
    const items = (data.items || []).filter((item) => item && item.id);
    if (!items.length) return;
    continueRowEl = buildRow({ title: "Continue Watching", items, continue: true });
    rowsContainer.prepend(continueRowEl);
  } catch (error) {
    console.error(error);
  }
}

function makeEl(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function formatRating(value) {
  const num = Number(value);
  return Number.isFinite(num) && num > 0 ? num.toFixed(1) : null;
}

function formatRuntime(minutes) {
  const num = Number(minutes);
  if (!Number.isFinite(num) || num <= 0) return null;
  const hours = Math.floor(num / 60);
  const mins = num % 60;
  return hours ? `${hours}h ${mins}m` : `${mins}m`;
}

function displayTitle(item) {
  return item?.title || item?.name || "Untitled";
}

function mediaLabel(item) {
  return item?.media_type === "tv" ? "Series" : "Movie";
}

function setView(view) {
  state.view = view;
  if (view !== "search") state.lastView = view;
  homeView.hidden = view !== "home";
  browseView.hidden = view !== "browse";
  searchView.hidden = view !== "search";

  document.querySelectorAll(".nav-link").forEach((link) => {
    const navView = link.dataset.view;
    const active =
      (view === "home" && navView === "home") ||
      (view === "browse" && navView === state.browse.view) ||
      (view === "search" && navView === state.lastView);
    link.classList.toggle("active", active);
  });

  window.scrollTo({ top: 0 });
}

function enableLightDismiss(dialog) {
  let pressedOutside = false;
  dialog.addEventListener("pointerdown", (event) => {
    pressedOutside = event.target === dialog;
  });
  dialog.addEventListener("click", (event) => {
    if (dialog === profileDialog && state.profileGateActive) {
      pressedOutside = false;
      return;
    }
    if (pressedOutside && event.target === dialog) dialog.close();
    pressedOutside = false;
  });
}

function isYouTubeTrailer(key) {
  return typeof key === "string" && /^[A-Za-z0-9_-]{6,20}$/.test(key);
}

function safeCssUrl(url) {
  if (typeof url !== "string" || !/^https:\/\//i.test(url)) return "none";
  const cleaned = url.replace(/["'()\\\r\n]/g, "");
  return `url("${cleaned}")`;
}

// ---------------------------------------------------------------------------
// Cards
// ---------------------------------------------------------------------------

function createCard(item, options = {}) {
  const card = makeEl("article", "card");
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  card.setAttribute("aria-label", `${displayTitle(item)} — ${mediaLabel(item)}`);

  if (options.rank) {
    card.classList.add("ranked");
    card.appendChild(makeEl("span", "rank-number", String(options.rank)));
  }

  const posterWrap = makeEl("div", "card-poster");

  if (item.poster_url) {
    const img = document.createElement("img");
    img.src = item.poster_url;
    img.alt = displayTitle(item);
    img.loading = "lazy";
    img.decoding = "async";
    img.addEventListener("error", () => {
      img.remove();
      posterWrap.appendChild(makeEl("div", "poster-fallback", displayTitle(item)));
    });
    posterWrap.appendChild(img);
  } else {
    posterWrap.appendChild(makeEl("div", "poster-fallback", displayTitle(item)));
  }

  const typeBadge = makeEl("span", "card-type", item.media_type === "tv" ? "SERIES" : "MOVIE");
  posterWrap.appendChild(typeBadge);

  if (!options.resumeAt && item.id) {
    const saved = isInWatchlist(item);
    const wlBtn = makeEl("button", `card-watchlist-btn${saved ? " active" : ""}`, saved ? "✓" : "+");
    wlBtn.type = "button";
    wlBtn.dataset.wlKey = watchlistKey(item);
    wlBtn.title = saved ? "Remove from My List" : "Add to My List";
    wlBtn.setAttribute("aria-label", `${saved ? "Remove" : "Add"} ${displayTitle(item)} ${saved ? "from" : "to"} My List`);
    wlBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleWatchlist(item);
    });
    posterWrap.appendChild(wlBtn);
  }

  if (options.resumeAt) {
    const removeBtn = makeEl("button", "card-remove");
    removeBtn.type = "button";
    removeBtn.title = "Remove from Continue Watching";
    removeBtn.setAttribute("aria-label", `Remove ${displayTitle(item)} from Continue Watching`);
    removeBtn.innerHTML =
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    removeBtn.addEventListener("click", async (event) => {
      event.stopPropagation();
      try {
        const res = await fetch(`/api/history/${item.media_type}/${item.id}`, {
          method: "DELETE",
          headers: {
            "X-CSRF-Token": getCsrfToken(),
            Accept: "application/json",
          },
        });
        if (res.ok) {
          showToast("Removed from Continue Watching");
          refreshContinueRow();
        }
      } catch (err) {
        console.error(err);
      }
    });
    posterWrap.appendChild(removeBtn);
  }

  if (options.resumeLabel) {
    posterWrap.appendChild(makeEl("span", "resume-tag", options.resumeLabel));
  }

  if (options.progress > 0) {
    const progressBar = makeEl("div", "card-progress");
    const fill = makeEl("span", "card-progress-fill");
    fill.style.width = `${Math.max(1, Math.min(100, options.progress))}%`;
    progressBar.appendChild(fill);
    posterWrap.appendChild(progressBar);
  }

  const play = () => {
    if (options.resumeAt) {
      openPlayer(
        item,
        options.resumeAt.season || 1,
        options.resumeAt.episode || 1,
        options.resumeAt.startAt || 0
      );
    } else {
      openPlayer(item, 1, 1);
    }
  };

  const overlay = makeEl("div", "card-overlay");
  overlay.innerHTML =
    '<span class="play-circle"><svg width="19" height="19" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 3 21 12 6 21 6 3"></polygon></svg></span>';
  posterWrap.appendChild(overlay);

  overlay.addEventListener("click", (event) => {
    event.stopPropagation();
    play();
  });

  const body = makeEl("div", "card-body");
  body.appendChild(makeEl("h3", "card-title", displayTitle(item)));

  const meta = makeEl("div", "card-meta");
  meta.appendChild(makeEl("span", "card-year", item.year || "TBA"));
  const rating = formatRating(item.vote_average);
  if (rating) meta.appendChild(makeEl("span", "card-rating", `★ ${rating}`));
  body.appendChild(meta);

  card.append(posterWrap, body);

  const open = () => {
    if (options.resumeAt) {
      play();
    } else {
      openDetail(item);
    }
  };
  card.addEventListener("click", open);
  card.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      open();
    }
  });

  return card;
}

// ---------------------------------------------------------------------------
// Home + hero carousel
// ---------------------------------------------------------------------------

function updateHero(item) {
  if (!item) return;
  state.currentHero = item;

  heroType.textContent = item.media_type === "tv" ? "SERIES" : "FILM";
  heroTitle.textContent = displayTitle(item);
  heroOverview.textContent =
    item.overview ||
    "Stream instantly in the Lumière player, or open the details panel for full metadata and artwork.";

  heroMeta.replaceChildren();
  if (item.year) heroMeta.appendChild(makeEl("span", "hero-chip", item.year));
  const rating = formatRating(item.vote_average);
  if (rating) heroMeta.appendChild(makeEl("span", "hero-chip gold", `★ ${rating}`));
  if (item.media_type === "tv") heroMeta.appendChild(makeEl("span", "hero-chip", "Series"));
  heroMeta.appendChild(makeEl("span", "hero-chip subtle", "HD"));

  const backdrop = item.backdrop_url || item.poster_url;
  if (backdrop) {
    heroBg.style.opacity = "0";
    setTimeout(() => {
      heroBg.style.backgroundImage = safeCssUrl(backdrop);
      heroBg.style.opacity = "1";
    }, 120);
  }

  heroDots.querySelectorAll(".hero-dot").forEach((dot, index) => {
    dot.classList.toggle("active", index === state.heroIndex);
    dot.setAttribute("aria-selected", index === state.heroIndex ? "true" : "false");
  });
  syncWatchlistButtons();
}

function setupHero(items) {
  state.heroItems = (items || []).slice(0, 6);
  state.heroIndex = 0;
  heroDots.replaceChildren();

  if (!state.heroItems.length) {
    heroTitle.textContent = "Explore the catalog";
    heroOverview.textContent = "Search millions of movies and series, then stream them instantly.";
    return;
  }

  state.heroItems.forEach((item, index) => {
    const dot = makeEl("button", "hero-dot");
    dot.type = "button";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-label", `Featured ${index + 1}: ${displayTitle(item)}`);
    if (index === 0) dot.classList.add("active");
    dot.addEventListener("click", () => {
      state.heroIndex = index;
      updateHero(state.heroItems[index]);
      restartHeroTimer();
    });
    heroDots.appendChild(dot);
  });

  updateHero(state.heroItems[0]);
  restartHeroTimer();
}

function restartHeroTimer() {
  clearInterval(state.heroTimer);
  if (state.heroItems.length < 2) return;
  state.heroTimer = setInterval(() => {
    if (state.heroPaused || state.view !== "home") return;
    state.heroIndex = (state.heroIndex + 1) % state.heroItems.length;
    updateHero(state.heroItems[state.heroIndex]);
  }, 9000);
}

function buildRow(row) {
  const section = makeEl("section", "row");
  const head = makeEl("div", "row-head");
  const heading = makeEl("h2", "row-title", row.title);
  head.appendChild(heading);
  section.appendChild(head);

  const scroller = makeEl("div", "row-scroller");
  const track = makeEl("div", "row-track");

  row.items.forEach((item, index) => {
    const isTv = item.media_type === "tv";
    const duration = Number(item.duration_seconds) || 0;
    const progressSeconds = Number(item.progress_seconds) || 0;
    const progress = duration > 0 ? (progressSeconds / duration) * 100 : 0;
    let resumeLabel = null;
    if (row.continue && isTv) {
      if (progressSeconds === 0) {
        resumeLabel = `Next: S${item.season || 1} E${item.episode || 1}`;
      } else {
        resumeLabel = `Resume S${item.season || 1} E${item.episode || 1}`;
      }
    }
    const card = createCard(item, {
      rank: row.rank ? index + 1 : null,
      resumeAt: row.continue
        ? {
            season: item.season || 1,
            episode: item.episode || 1,
            startAt: progressSeconds,
          }
        : null,
      resumeLabel: resumeLabel || (row.continue ? "Continue watching" : null),
      progress: row.continue ? progress : 0,
    });
    track.appendChild(card);
  });

  const prev = makeEl("button", "row-nav prev");
  prev.type = "button";
  prev.setAttribute("aria-label", "Scroll left");
  prev.innerHTML =
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"></polyline></svg>';

  const next = makeEl("button", "row-nav next");
  next.type = "button";
  next.setAttribute("aria-label", "Scroll right");
  next.innerHTML =
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>';

  const scrollAmount = () => Math.max(320, track.clientWidth * 0.82);
  prev.addEventListener("click", () => track.scrollBy({ left: -scrollAmount(), behavior: "smooth" }));
  next.addEventListener("click", () => track.scrollBy({ left: scrollAmount(), behavior: "smooth" }));

  const syncButtons = () => {
    const maxScroll = track.scrollWidth - track.clientWidth - 4;
    prev.classList.toggle("visible", track.scrollLeft > 8);
    next.classList.toggle("visible", track.scrollLeft < maxScroll);
  };

  track.addEventListener("scroll", syncButtons, { passive: true });
  window.addEventListener("resize", syncButtons);
  requestAnimationFrame(syncButtons);

  scroller.append(prev, track, next);
  section.appendChild(scroller);
  return section;
}

function consumeInitialHomePayload() {
  const el = document.getElementById("initialHomeData");
  if (!el) return null;
  try {
    const parsed = JSON.parse(el.textContent || "{}");
    el.remove();
    if (parsed && Array.isArray(parsed.rows) && parsed.rows.length) {
      return parsed;
    }
  } catch (err) {
    console.error(err);
  }
  return null;
}

function applyHomePayload(data) {
  if (data.active_profile) {
    updateActiveProfileUI(data.active_profile, data.profiles || []);
  }
  if (data.needs_profile_selection) {
    openProfileDialog(true);
  }
  syncWatchlistState(data.watchlist || []);
  setupHero(data.hero);
  rowsContainer.replaceChildren();
  (data.rows || []).forEach((row) => {
    if (row.items && row.items.length) rowsContainer.appendChild(buildRow(row));
  });
  if (!rowsContainer.children.length) {
    rowsContainer.appendChild(makeEl("p", "empty-state", "No titles available right now. Try again shortly."));
  }
  state.homeLoaded = true;
  renderWatchlistRow();
  if (Array.isArray(data.continue_watching)) {
    if (continueRowEl) {
      continueRowEl.remove();
      continueRowEl = null;
    }
    const items = data.continue_watching.filter((item) => item && item.id);
    if (items.length) {
      continueRowEl = buildRow({ title: "Continue Watching", items, continue: true });
      rowsContainer.prepend(continueRowEl);
    }
    if (watchlistRowEl && continueRowEl && continueRowEl.parentNode === rowsContainer) {
      continueRowEl.insertAdjacentElement("afterend", watchlistRowEl);
    }
  } else {
    refreshContinueRow().then(() => {
      if (watchlistRowEl && continueRowEl && continueRowEl.parentNode === rowsContainer) {
        continueRowEl.insertAdjacentElement("afterend", watchlistRowEl);
      }
    });
  }
}

async function loadHome() {
  if (state.homeLoaded) return;
  continueRowEl = null;
  watchlistRowEl = null;

  const preloaded = consumeInitialHomePayload();
  if (preloaded) {
    applyHomePayload(preloaded);
    return;
  }

  rowsContainer.replaceChildren();
  for (let i = 0; i < 2; i++) rowsContainer.appendChild(makeEl("div", "row-skeleton"));

  try {
    const data = await apiFetch("/api/home");
    applyHomePayload(data);
  } catch (error) {
    console.error(error);
    rowsContainer.replaceChildren();
    rowsContainer.appendChild(makeEl("p", "empty-state", "Unable to load the catalog. Please refresh."));
  }
}

// ---------------------------------------------------------------------------
// Browse
// ---------------------------------------------------------------------------

function renderBrowseFilters() {
  const config = BROWSE_CONFIG[state.browse.view];
  browseFilters.replaceChildren();
  config.filters.forEach(([value, label]) => {
    const chip = makeEl("button", "filter-chip", label);
    chip.type = "button";
    chip.dataset.value = value;

    let active = false;
    if (state.browse.view === "top") {
      active =
        (value === "top_movies" && state.browse.type === "movie") ||
        (value === "top_tv" && state.browse.type === "tv");
    } else {
      active = value === state.browse.category;
    }
    chip.classList.toggle("active", active);

    chip.addEventListener("click", () => {
      if (state.browse.view === "top") {
        state.browse.type = value === "top_tv" ? "tv" : "movie";
        state.browse.category = "top_rated";
      } else {
        state.browse.category = value;
      }
      renderBrowseFilters();
      loadBrowse(1, false);
    });

    browseFilters.appendChild(chip);
  });
}

function renderGrid(container, items) {
  container.replaceChildren();
  items.forEach((item) => container.appendChild(createCard(item)));
}

function renderMyListBrowse() {
  browseEyebrow.textContent = "Personal collection";
  browseTitle.textContent = "My List";
  browseMoreBtn.hidden = true;

  const filterVal = state.browse.category || "all";
  const items = state.watchlistItems.filter((item) => {
    if (filterVal === "movie") return item.media_type === "movie";
    if (filterVal === "tv") return item.media_type === "tv";
    return true;
  });

  browseGrid.replaceChildren();
  renderGrid(browseGrid, items);
  if (!items.length) {
    browseGrid.appendChild(
      makeEl(
        "p",
        "empty-state",
        "Your Watchlist is empty. Click “+ My List” on any movie or series to save it here."
      )
    );
  }
  browseStatus.textContent = `${items.length.toLocaleString()} saved title${items.length === 1 ? "" : "s"}`;
}

async function loadBrowse(page = 1, append = false) {
  const requestId = ++state.browse.requestId;
  const { view, type, category } = state.browse;
  browseEyebrow.textContent = BROWSE_CONFIG[view].eyebrow;
  browseStatus.textContent = "Loading…";
  browseMoreBtn.hidden = true;

  if (view === "mylist") {
    try {
      const data = await apiFetch("/api/watchlist");
      if (requestId !== state.browse.requestId) return;
      syncWatchlistState(data.items || []);
      renderMyListBrowse();
    } catch (error) {
      console.error(error);
      renderMyListBrowse();
    }
    return;
  }

  if (!append) {
    browseGrid.replaceChildren();
    for (let i = 0; i < 8; i++) browseGrid.appendChild(makeEl("div", "card-skeleton"));
  }

  try {
    const params = new URLSearchParams({ type, category, page: String(page) });
    const data = await apiFetch(`/api/catalog?${params.toString()}`);
    if (requestId !== state.browse.requestId) return;

    state.browse.page = data.page;
    state.browse.totalPages = data.total_pages || 1;
    state.browse.items = append ? [...state.browse.items, ...data.items] : data.items;

    browseTitle.textContent = data.title || "Browse";
    browseGrid.replaceChildren();
    renderGrid(browseGrid, state.browse.items);

    if (!state.browse.items.length) {
      browseGrid.appendChild(makeEl("p", "empty-state", "No titles found."));
    }

    browseStatus.textContent = `${Number(data.total_results || 0).toLocaleString()} titles`;
    browseMoreBtn.hidden = state.browse.page >= state.browse.totalPages;
  } catch (error) {
    console.error(error);
    browseGrid.replaceChildren(makeEl("p", "empty-state", "Unable to load titles."));
    browseStatus.textContent = "";
  }
}

function openBrowse(viewName) {
  const config = BROWSE_CONFIG[viewName];
  if (!config) return;
  state.browse.view = viewName;
  state.browse.type = config.type;
  state.browse.category = config.category;
  state.browse.page = 1;
  state.browse.totalPages = 1;
  state.browse.items = [];
  searchInput.value = "";
  searchClear.hidden = true;
  setView("browse");
  renderBrowseFilters();
  loadBrowse(1, false);
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

function renderSearchResults(items) {
  searchGrid.replaceChildren();
  items.forEach((item) => searchGrid.appendChild(createCard(item)));
  if (!items.length) {
    searchGrid.appendChild(makeEl("p", "empty-state", "No results. Try a different title or TMDB ID."));
  }
}

async function runSearch(query, page = 1, append = false) {
  if (!query) return;
  const requestId = ++state.search.requestId;
  state.search.query = query;
  setView("search");

  searchTitle.textContent = `Results for “${query}”`;
  searchStatus.textContent = "Searching…";
  searchMoreBtn.hidden = true;

  if (!append) {
    searchGrid.replaceChildren();
    for (let i = 0; i < 8; i++) searchGrid.appendChild(makeEl("div", "card-skeleton"));
  }

  try {
    const params = new URLSearchParams({ q: query, type: "multi", page: String(page) });
    const data = await apiFetch(`/api/search?${params.toString()}`);
    if (requestId !== state.search.requestId) return;

    state.search.page = data.page || page;
    state.search.totalPages = data.total_pages || 1;
    state.search.items = append ? [...state.search.items, ...(data.items || [])] : data.items || [];

    renderSearchResults(state.search.items);
    searchCount.textContent = `${Number(data.total_results || state.search.items.length).toLocaleString()} results`;
    searchStatus.textContent = "";
    searchMoreBtn.hidden = state.search.page >= state.search.totalPages || !state.search.items.length;
  } catch (error) {
    if (requestId !== state.search.requestId) return;
    console.error(error);
    searchGrid.replaceChildren(makeEl("p", "empty-state", "Search failed. Please try again."));
    searchStatus.textContent = "";
    searchCount.textContent = "";
  }
}

function clearSearch() {
  clearTimeout(state.search._timer);
  state.search.requestId++;
  searchInput.value = "";
  searchClear.hidden = true;
  state.search.query = "";
  state.search.page = 1;
  state.search.items = [];
  if (state.lastView === "browse") {
    setView("browse");
  } else {
    setView("home");
    loadHome();
  }
}

// ---------------------------------------------------------------------------
// Details
// ---------------------------------------------------------------------------

function metaPill(text, extraClass) {
  if (!text) return null;
  const node = makeEl("span", `meta-pill${extraClass ? ` ${extraClass}` : ""}`, text);
  return node;
}

function stopInlineTrailer() {
  if (detailTrailerFrame) detailTrailerFrame.src = "about:blank";
  if (detailTrailerWrap) detailTrailerWrap.hidden = true;
  if (detailTrailerLabel) detailTrailerLabel.textContent = "Watch Trailer";
  if (detailTrailerBtn) detailTrailerBtn.classList.remove("active");
}

function toggleInlineTrailer() {
  const key = state.detail?.trailer_key;
  if (!isYouTubeTrailer(key) || !detailTrailerWrap || !detailTrailerFrame) return;
  const isOpen = !detailTrailerWrap.hidden;
  if (isOpen) {
    stopInlineTrailer();
  } else {
    detailTrailerFrame.src = `https://www.youtube-nocookie.com/embed/${key}?autoplay=1&rel=0&modestbranding=1`;
    detailTrailerWrap.hidden = false;
    if (detailTrailerLabel) detailTrailerLabel.textContent = "Hide Trailer";
    if (detailTrailerBtn) detailTrailerBtn.classList.add("active");
    detailTrailerWrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function renderDetailBasics(item) {
  detailType.textContent = item.media_type === "tv" ? "SERIES" : "MOVIE";
  detailTitle.textContent = displayTitle(item);
  detailOverview.textContent = item.overview || "No overview available.";
  detailType.classList.toggle("is-series", item.media_type === "tv");

  detailMeta.replaceChildren();
  const pills = [
    metaPill(item.year),
    metaPill(formatRuntime(item.runtime)),
    metaPill(item.media_type === "tv" && item.number_of_seasons ? `${item.number_of_seasons} season${item.number_of_seasons > 1 ? "s" : ""}` : null),
    metaPill(formatRating(item.vote_average) ? `★ ${formatRating(item.vote_average)}` : null, "rating"),
  ];
  pills.forEach((pill) => pill && detailMeta.appendChild(pill));

  const backdrop = item.backdrop_url || item.poster_url;
  detailHeroBg.style.backgroundImage = backdrop ? safeCssUrl(backdrop) : "none";

  if (item.poster_url) {
    detailPoster.hidden = false;
    detailPoster.onerror = () => {
      detailPoster.hidden = true;
    };
    detailPoster.src = item.poster_url;
  } else {
    detailPoster.hidden = true;
  }

  detailTmdb.href = item.tmdb_url || `https://www.themoviedb.org/${item.media_type}/${item.id}`;

  if (isYouTubeTrailer(item.trailer_key)) {
    detailTrailer.href = `https://www.youtube.com/watch?v=${item.trailer_key}`;
    detailTrailer.hidden = false;
    if (detailTrailerBtn) detailTrailerBtn.hidden = false;
  } else {
    detailTrailer.hidden = true;
    if (detailTrailerBtn) detailTrailerBtn.hidden = true;
    stopInlineTrailer();
  }
  syncWatchlistButtons();
}

const GENRE_NAME_TO_FILTER = {
  Action: ["movies", "genre_28"],
  "Science Fiction": ["movies", "genre_878"],
  Horror: ["movies", "genre_27"],
  Thriller: ["movies", "genre_53"],
  Comedy: ["movies", "genre_35"],
  Drama: ["movies", "genre_18"],
  Animation: ["movies", "genre_16"],
  Crime: ["movies", "genre_80"],
  Romance: ["movies", "genre_10749"],
  Documentary: ["movies", "genre_99"],
  Family: ["movies", "genre_10751"],
  "Action & Adventure": ["tv", "genre_10759"],
  "Sci-Fi & Fantasy": ["tv", "genre_10765"],
  Kids: ["tv", "genre_10762"],
};

function renderGenres(genres) {
  detailGenres.replaceChildren();
  (genres || []).forEach((genre) => {
    const mapped = GENRE_NAME_TO_FILTER[genre];
    if (mapped) {
      const btn = makeEl("button", "chip chip-clickable", genre);
      btn.type = "button";
      btn.title = `Browse ${genre}`;
      btn.addEventListener("click", () => {
        const [viewName, category] = mapped;
        detailDialog.close();
        state.browse.view = viewName;
        state.browse.type = BROWSE_CONFIG[viewName].type;
        state.browse.category = category;
        state.browse.page = 1;
        setView("browse");
        renderBrowseFilters();
        loadBrowse(1, false);
      });
      detailGenres.appendChild(btn);
    } else {
      detailGenres.appendChild(makeEl("span", "chip", genre));
    }
  });
  if (!genres || !genres.length) {
    detailGenres.appendChild(makeEl("span", "chip muted", "Uncategorized"));
  }
}

async function openPerson(personId, personName) {
  if (!personId) return;
  detailDialog.close();
  const requestId = ++state.search.requestId;
  setView("search");
  searchTitle.textContent = personName || "Filmography";
  searchCount.textContent = "Loading filmography…";
  searchStatus.textContent = "";
  searchMoreBtn.hidden = true;
  searchGrid.replaceChildren();
  for (let i = 0; i < 8; i++) searchGrid.appendChild(makeEl("div", "card-skeleton"));

  try {
    const data = await apiFetch(`/api/person/${personId}`);
    if (requestId !== state.search.requestId) return;
    const items = data.items || [];
    searchTitle.textContent = data.name || personName || "Filmography";
    const metaParts = [data.known_for_department, data.place_of_birth].filter(Boolean);
    searchCount.textContent = `${items.length} titles${metaParts.length ? ` · ${metaParts.join(" · ")}` : ""}`;
    renderSearchResults(items);
  } catch (error) {
    console.error(error);
    searchGrid.replaceChildren(makeEl("p", "empty-state", "Unable to load filmography right now."));
    searchCount.textContent = "";
  }
}

function renderCast(cast) {
  detailCast.replaceChildren();
  if (!cast || !cast.length) {
    detailCastSection.hidden = true;
    return;
  }
  detailCastSection.hidden = false;
  cast.slice(0, 10).forEach((person) => {
    const member = makeEl(person.id ? "button" : "div", `cast-member${person.id ? " clickable" : ""}`);
    if (person.id) {
      member.type = "button";
      member.title = `View all titles featuring ${person.name || "this actor"}`;
      member.addEventListener("click", () => openPerson(person.id, person.name));
    }
    if (person.profile_url) {
      const img = document.createElement("img");
      img.src = person.profile_url;
      img.alt = person.name || "";
      img.loading = "lazy";
      img.addEventListener("error", () => {
        img.replaceWith(makeEl("div", "cast-avatar", (person.name || "?").slice(0, 1)));
      });
      member.appendChild(img);
    } else {
      member.appendChild(makeEl("div", "cast-avatar", (person.name || "?").slice(0, 1)));
    }
    const copy = makeEl("div", "cast-copy");
    copy.appendChild(makeEl("strong", null, person.name || "Unknown"));
    if (person.character) copy.appendChild(makeEl("span", null, person.character));
    member.appendChild(copy);
    detailCast.appendChild(member);
  });
}

function renderFacts(item) {
  detailFacts.replaceChildren();

  const directorItems = (item.director_items || []).slice(0, 2);
  if (directorItems.length) {
    const row = makeEl("div", "fact-row");
    row.appendChild(makeEl("dt", null, "Director"));
    const dd = makeEl("dd", "fact-links");
    directorItems.forEach((dir, idx) => {
      if (idx > 0) dd.appendChild(document.createTextNode(", "));
      if (dir.id) {
        const link = makeEl("button", "fact-person-btn", dir.name);
        link.type = "button";
        link.addEventListener("click", () => openPerson(dir.id, dir.name));
        dd.appendChild(link);
      } else {
        dd.appendChild(document.createTextNode(dir.name));
      }
    });
    row.appendChild(dd);
    detailFacts.appendChild(row);
  } else if ((item.directors || []).length) {
    const row = makeEl("div", "fact-row");
    row.appendChild(makeEl("dt", null, "Director"));
    row.appendChild(makeEl("dd", null, (item.directors || []).slice(0, 2).join(", ")));
    detailFacts.appendChild(row);
  }

  const facts = [
    ["Status", item.status],
    ["Release", item.release_date],
    ["Language", item.original_language ? item.original_language.toUpperCase() : null],
    ["Seasons", item.number_of_seasons],
    ["Episodes", item.number_of_episodes],
    ["Votes", item.vote_count ? Number(item.vote_count).toLocaleString() : null],
  ].filter(([, value]) => value);

  facts.forEach(([label, value]) => {
    const row = makeEl("div", "fact-row");
    row.appendChild(makeEl("dt", null, label));
    row.appendChild(makeEl("dd", null, String(value)));
    detailFacts.appendChild(row);
  });
}

function renderRecommendations(items) {
  detailRecommendations.replaceChildren();
  const filtered = (items || []).filter((item) => item.poster_url).slice(0, 10);
  if (!filtered.length) {
    detailRecSection.hidden = true;
    return;
  }
  detailRecSection.hidden = false;
  filtered.forEach((item) => detailRecommendations.appendChild(createCard(item)));
}

function renderEpisodeGrid(episodes, selectedEpisode = 1) {
  if (!episodeGrid) return;
  episodeGrid.replaceChildren();
  const seasonNum = Number(seasonSelect.value) || 1;

  episodes.forEach((ep) => {
    const card = makeEl(
      "div",
      `episode-card${ep.episode_number === Number(selectedEpisode) ? " active" : ""}`
    );
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Play Episode ${ep.episode_number}: ${ep.name}`);

    const thumb = makeEl("div", "episode-thumb");
    if (ep.still_url) {
      const img = document.createElement("img");
      img.src = ep.still_url;
      img.alt = ep.name || `Episode ${ep.episode_number}`;
      img.loading = "lazy";
      img.addEventListener("error", () => {
        img.remove();
        thumb.appendChild(makeEl("div", "episode-thumb-fallback", `E${ep.episode_number}`));
      });
      thumb.appendChild(img);
    } else {
      thumb.appendChild(makeEl("div", "episode-thumb-fallback", `E${ep.episode_number}`));
    }
    const playBadge = makeEl("span", "episode-play-badge");
    playBadge.innerHTML =
      '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 3 21 12 6 21 6 3"></polygon></svg>';
    thumb.appendChild(playBadge);
    if (ep.runtime) {
      thumb.appendChild(makeEl("span", "episode-runtime", formatRuntime(ep.runtime) || `${ep.runtime}m`));
    }

    const info = makeEl("div", "episode-info");
    const head = makeEl("div", "episode-head");
    head.appendChild(makeEl("strong", "episode-title", `${ep.episode_number}. ${ep.name}`));
    if (ep.air_date) head.appendChild(makeEl("span", "episode-date", ep.air_date));
    info.appendChild(head);
    if (ep.overview) {
      info.appendChild(makeEl("p", "episode-desc", ep.overview));
    }

    card.append(thumb, info);

    const playThisEpisode = () => {
      if (!state.detail) return;
      episodeSelect.value = String(ep.episode_number);
      detailDialog.close();
      openPlayer(state.detail, seasonNum, ep.episode_number);
    };
    card.addEventListener("click", playThisEpisode);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        playThisEpisode();
      }
    });
    episodeGrid.appendChild(card);
  });
}

function populateEpisodeSelect(episodes, selectedEpisode = 1) {
  episodeSelect.replaceChildren();
  episodes.forEach((episode) => {
    const option = document.createElement("option");
    option.value = String(episode.episode_number);
    option.textContent = `${episode.episode_number}. ${episode.name}`;
    episodeSelect.appendChild(option);
  });
  episodeSelect.value = String(selectedEpisode);

  const current = episodes.find((episode) => episode.episode_number === Number(selectedEpisode));
  episodeCaption.textContent = current
    ? [current.air_date, formatRuntime(current.runtime), current.overview].filter(Boolean).join(" · ")
    : "";
  renderEpisodeGrid(episodes, selectedEpisode);
}

async function loadDetailSeason(seasonNumber, selectedEpisode = 1) {
  const item = state.detail;
  if (!item || item.media_type !== "tv") return [];

  const cacheKey = `${item.id}:${seasonNumber}`;
  if (state.seasonCache[cacheKey]) {
    const episodes = state.seasonCache[cacheKey];
    populateEpisodeSelect(episodes, selectedEpisode);
    return episodes;
  }

  try {
    const data = await apiFetch(`/api/tv/${item.id}/season/${seasonNumber}`);
    const episodes = data.episodes || [];
    state.seasonCache[cacheKey] = episodes;
    populateEpisodeSelect(episodes, selectedEpisode);
    return episodes;
  } catch (error) {
    console.error(error);
    episodeSelect.replaceChildren();
    episodeCaption.textContent = "Episodes unavailable for this season.";
    return [];
  }
}

async function openDetail(item) {
  if (!item) return;
  stopInlineTrailer();
  state.detail = { ...item };
  state.seasonCache = {};
  const requestId = ++state.detailRequestId;

  renderDetailBasics(item);
  renderGenres(item.genres);
  renderCast(item.cast);
  renderFacts(item);
  renderRecommendations(item.recommendations);

  episodePanel.hidden = item.media_type !== "tv";
  seasonSelect.replaceChildren();
  episodeSelect.replaceChildren();
  if (episodeGrid) episodeGrid.replaceChildren();
  episodeCaption.textContent = "Loading episodes…";

  if (!detailDialog.open) detailDialog.showModal();
  detailDialog.scrollTop = 0;

  try {
    const data = await apiFetch(`/api/title/${item.media_type}/${item.id}`);
    if (requestId !== state.detailRequestId) return;

    state.detail = { ...state.detail, ...data };
    renderDetailBasics(state.detail);
    renderGenres(state.detail.genres);
    renderCast(state.detail.cast);
    renderFacts(state.detail);
    renderRecommendations(state.detail.recommendations);

    if (state.detail.media_type === "tv") {
      episodePanel.hidden = false;
      const seasons = (state.detail.seasons || []).filter((s) => s.season_number > 0);
      const usable = seasons.length ? seasons : state.detail.seasons || [];
      seasonSelect.replaceChildren();
      usable.forEach((season) => {
        const option = document.createElement("option");
        option.value = String(season.season_number);
        option.textContent = `${season.name}${season.episode_count ? ` (${season.episode_count} eps)` : ""}`;
        seasonSelect.appendChild(option);
      });
      if (usable.length) {
        seasonSelect.value = String(usable[0].season_number);
        await loadDetailSeason(usable[0].season_number, 1);
      } else {
        episodeCaption.textContent = "No seasons available.";
      }
    }
  } catch (error) {
    console.error(error);
    if (requestId !== state.detailRequestId) return;
    detailOverview.textContent = item.overview || "No overview available.";
    if (item.media_type === "tv") episodeCaption.textContent = "Episode data unavailable.";
  }
}

function ensureSeasonOptions(seasons) {
  playerSeason.replaceChildren();
  seasons.forEach((season) => {
    const option = document.createElement("option");
    option.value = String(season.season_number);
    option.textContent = season.name || `Season ${season.season_number}`;
    playerSeason.appendChild(option);
  });
}

function playerUrl(item, season, episode, startAt = 0) {
  if (!item) return "about:blank";
  const server = state.player.server || (playerServer ? playerServer.value : "s1") || "s1";
  const s = Number(season) || 1;
  const e = Number(episode) || 1;
  const start = Number(startAt) > 1 ? `&startAt=${Math.floor(startAt)}` : "";

  if (server === "s2") {
    if (item.media_type === "tv") {
      return `https://vidlink.pro/tv/${item.id}/${s}/${e}?autoplay=true&primaryColor=e50914&nextbutton=true`;
    }
    return `https://vidlink.pro/movie/${item.id}?autoplay=true&primaryColor=e50914`;
  }
  if (server === "s3") {
    if (item.media_type === "tv") {
      return `https://vidsrc.cc/v2/embed/tv/${item.id}/${s}/${e}`;
    }
    return `https://vidsrc.cc/v2/embed/movie/${item.id}`;
  }
  if (server === "s4") {
    if (item.media_type === "tv") {
      return `https://multiembed.mov/directstream.php?video_id=${item.id}&tmdb=1&s=${s}&e=${e}`;
    }
    return `https://multiembed.mov/directstream.php?video_id=${item.id}&tmdb=1`;
  }

  if (item.media_type === "tv") {
    return `${VIDEO_BASE}/tv/${item.id}/${s}/${e}?autoPlay=true&title=true&poster=true&nextButton=true&autoNext=true&theme=${PLAYER_THEME}${start}`;
  }
  return `${VIDEO_BASE}/movie/${item.id}?autoPlay=true&title=true&theme=${PLAYER_THEME}${start}`;
}

function currentPlayerEpisode() {
  const episodes = state.player.episodes || [];
  return episodes.find((episode) => episode.episode_number === Number(state.player.episode));
}

function formatTimestamp(sec) {
  const s = Math.max(0, Math.floor(Number(sec) || 0));
  const hrs = Math.floor(s / 3600);
  const mins = Math.floor((s % 3600) / 60);
  const rem = s % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return hrs > 0 ? `${hrs}:${pad(mins)}:${pad(rem)}` : `${pad(mins)}:${pad(rem)}`;
}

function stopNativeVideo() {
  if (window.lumiereDashPlayer) {
    try {
      window.lumiereDashPlayer.destroy();
    } catch (e) {}
    window.lumiereDashPlayer = null;
  }
  if (!lumiereVideo) return;
  try {
    lumiereVideo.pause();
    lumiereVideo.removeAttribute("src");
    lumiereVideo.load();
  } catch (err) {
    // ignore
  }
}

function syncNativePlayButton() {
  if (!lumiereVideo || !lumierePlayBtn) return;
  const paused = lumiereVideo.paused;
  lumierePlayBtn.innerHTML = paused
    ? '<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="6 3 21 12 6 21 6 3"></polygon></svg>'
    : '<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="4" width="4" height="16" rx="1"></rect><rect x="14" y="4" width="4" height="16" rx="1"></rect></svg>';
  if (lumiereCenterPlay) {
    lumiereCenterPlay.classList.toggle("visible", paused);
  }
}

// ---------------------------------------------------------------------------
// Universal Lumière Subtitles Studio
// ---------------------------------------------------------------------------

let subtitleClockInterval = null;

function applySubtitleAppearance() {
  if (!lumiereSubtitleText || !lumiereSubtitleOverlay) return;
  const { size, color, bgMode } = state.subtitles;
  lumiereSubtitleText.dataset.size = size || "md";
  lumiereSubtitleText.style.color = color || "#ffffff";
  lumiereSubtitleText.dataset.bg = bgMode || "glass";
  if (subtitleBgToggle) {
    const labelMap = { glass: "Box: Glass", solid: "Box: Solid", shadow: "Box: Shadow" };
    subtitleBgToggle.textContent = labelMap[bgMode] || "Box: Glass";
  }
}

function renderActiveSubtitleCue() {
  if (!lumiereSubtitleOverlay || !lumiereSubtitleText) return;
  const cues = state.subtitles.cues || [];
  if (state.subtitles.activeTrackId === "off" || !cues.length) {
    lumiereSubtitleOverlay.hidden = true;
    lumiereSubtitleText.textContent = "";
    return;
  }

  const effectiveTime = (Number(state.player.currentTime) || 0) - (Number(state.subtitles.offset) || 0);
  if (subtitleClockDisplay) {
    subtitleClockDisplay.textContent = formatTimestamp(state.player.currentTime);
  }

  const active = cues.find((c) => effectiveTime >= c.start && effectiveTime <= c.end);
  if (active && active.text) {
    lumiereSubtitleText.textContent = active.text;
    lumiereSubtitleOverlay.hidden = false;
  } else {
    lumiereSubtitleOverlay.hidden = true;
    lumiereSubtitleText.textContent = "";
  }
}

function startSubtitleClock() {
  clearInterval(subtitleClockInterval);
  state.subtitles.clockRunning = true;
  if (subtitleClockToggle) subtitleClockToggle.textContent = "Pause Clock";
  subtitleClockInterval = setInterval(() => {
    if (!playerDialog.open) return;
    const isNative = state.player.server === "native" && lumiereNativeStage && !lumiereNativeStage.hidden;
    if (isNative && lumiereVideo) {
      state.player.currentTime = Number(lumiereVideo.currentTime) || 0;
      state.player.duration = Number(lumiereVideo.duration) || 0;
    } else if (state.subtitles.clockRunning) {
      const sinceExternal = Date.now() - (state.subtitles.lastExternalSync || 0);
      if (sinceExternal > 1200) {
        state.player.currentTime = Math.max(0, (Number(state.player.currentTime) || 0) + 0.2);
      }
    }
    if (subtitleClockDisplay) {
      subtitleClockDisplay.textContent = formatTimestamp(state.player.currentTime);
    }
    renderActiveSubtitleCue();
  }, 200);
}

function stopSubtitleClock() {
  clearInterval(subtitleClockInterval);
  subtitleClockInterval = null;
}

function parseClientSubtitleText(rawText) {
  const cleaned = (rawText || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
  if (!cleaned) return [];
  const blocks = cleaned.split(/\n\s*\n/);
  const timeRe = /(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(?:(\d{1,2}):)?(\d{2}):(\d{2})[.,](\d{3})/;
  const toSec = (h, m, s, ms) => Number(h || 0) * 3600 + Number(m || 0) * 60 + Number(s || 0) + Number(ms || 0) / 1000;
  const cues = [];
  for (const block of blocks) {
    const lines = block
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (!lines.length || lines[0].startsWith("WEBVTT") || lines[0].startsWith("NOTE")) continue;
    let match = null;
    let startIdx = 0;
    for (let i = 0; i < Math.min(2, lines.length); i++) {
      const m = timeRe.exec(lines[i]);
      if (m) {
        match = m;
        startIdx = i + 1;
        break;
      }
    }
    if (!match) continue;
    const start = toSec(match[1], match[2], match[3], match[4]);
    const end = toSec(match[5], match[6], match[7], match[8]);
    const text = lines
      .slice(startIdx)
      .join("\n")
      .replace(/\{[^}]*\}/g, "")
      .replace(/<[^>]+>/g, "")
      .trim();
    if (text && end > start) cues.push({ start, end, text });
  }
  return cues;
}

async function selectSubtitleTrack(trackId) {
  state.subtitles.activeTrackId = trackId;
  if (subtitleTrackList) {
    subtitleTrackList.querySelectorAll(".subtitle-track-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.trackId === trackId);
    });
  }
  if (subtitleMenuBtn) {
    subtitleMenuBtn.classList.toggle("active", trackId !== "off");
  }

  if (trackId === "off") {
    state.subtitles.cues = [];
    renderActiveSubtitleCue();
    return;
  }

  const track = (state.subtitles.tracks || []).find((t) => String(t.id) === String(trackId));
  if (!track) return;

  if (Array.isArray(track.cues)) {
    state.subtitles.cues = track.cues;
    renderActiveSubtitleCue();
    showToast(`Subtitles: ${track.label} (${track.cues.length} cues)`);
    return;
  }

  if (track.cues_url) {
    try {
      const data = await apiFetch(track.cues_url);
      track.cues = data.cues || [];
      if (state.subtitles.activeTrackId === trackId) {
        state.subtitles.cues = track.cues;
        renderActiveSubtitleCue();
        showToast(`Subtitles: ${track.label}`);
      }
    } catch (error) {
      console.error(error);
      showToast("Unable to load that subtitle track");
    }
  }
}

function renderSubtitleTracksList() {
  if (!subtitleTrackList) return;
  subtitleTrackList.replaceChildren();

  const offBtn = makeEl(
    "button",
    `subtitle-track-item${state.subtitles.activeTrackId === "off" ? " active" : ""}`,
    "Off"
  );
  offBtn.type = "button";
  offBtn.dataset.trackId = "off";
  offBtn.addEventListener("click", () => selectSubtitleTrack("off"));
  subtitleTrackList.appendChild(offBtn);

  (state.subtitles.tracks || []).forEach((track) => {
    const btn = makeEl(
      "button",
      `subtitle-track-item${String(state.subtitles.activeTrackId) === String(track.id) ? " active" : ""}`,
      `${track.label}${track.hi ? " [CC]" : ""}`
    );
    btn.type = "button";
    btn.dataset.trackId = String(track.id);
    btn.addEventListener("click", () => selectSubtitleTrack(String(track.id)));
    subtitleTrackList.appendChild(btn);
  });

  if (subtitleCountBadge) {
    const count = (state.subtitles.tracks || []).length;
    subtitleCountBadge.textContent = String(count);
    subtitleCountBadge.hidden = count === 0;
  }
}

async function loadSubtitlesForCurrentTitle() {
  const item = state.player.item;
  state.subtitles.tracks = [];
  state.subtitles.activeTrackId = "off";
  state.subtitles.cues = [];
  state.subtitles.offset = 0;
  if (subtitleOffsetValue) subtitleOffsetValue.textContent = "0.0s";
  renderSubtitleTracksList();
  renderActiveSubtitleCue();

  if (!item || !item.id) return;
  const s = Number(state.player.season) || 1;
  const e = Number(state.player.episode) || 1;
  try {
    const data = await apiFetch(`/api/subtitles/${item.media_type}/${item.id}?season=${s}&episode=${e}`);
    if (!state.player.item || state.player.item.id !== item.id) return;
    state.subtitles.tracks = data.tracks || [];
    renderSubtitleTracksList();
  } catch (error) {
    console.error(error);
  }
}

async function checkDirectStreamForCurrentTitle() {
  const item = state.player.item;
  state.player.directStream = null;
  if (!item || !item.id) return null;

  const s = Number(state.player.season) || 1;
  const e = Number(state.player.episode) || 1;
  try {
    const data = await apiFetch(`/api/stream/${item.media_type}/${item.id}?season=${s}&episode=${e}`);
    if (data.has_direct_stream && data.stream && data.stream.url) {
      state.player.directStream = data.stream;
      if (nativeStreamOption) {
        nativeStreamOption.hidden = false;
        nativeStreamOption.textContent = `Lumière Cinema Engine (${data.stream.quality_label || "1080p Ad-Free"})`;
      }
      if (adminStreamInput) adminStreamInput.value = data.stream.url;
      return data.stream;
    } else if (adminStreamInput) {
      adminStreamInput.value = "";
    }
  } catch (error) {
    console.error(error);
  }
  return null;
}

function stopStreamHeartbeat() {
  if (state.player.heartbeatTimer) {
    clearInterval(state.player.heartbeatTimer);
    state.player.heartbeatTimer = null;
  }
}

async function releaseStreamSlot() {
  stopStreamHeartbeat();
  try {
    await fetch("/api/stream/release", {
      method: "POST",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
        Accept: "application/json",
      },
      body: JSON.stringify({ stream_token: TAB_STREAM_TOKEN }),
    });
  } catch (error) {
    // ignore release errors on close
  }
}

function showStreamLimitScreen(data) {
  stopStreamHeartbeat();
  stopNativeVideo();
  if (lumiereNativeStage) lumiereNativeStage.hidden = true;
  player.src = "about:blank";
  player.hidden = true;
  if (!streamLimitOverlay) return;

  if (streamLimitMessage) {
    streamLimitMessage.textContent =
      data.error ||
      "Your account is already streaming on 3 screens. Close playback on another device or transfer playback to this screen.";
  }

  if (streamLimitList) {
    streamLimitList.replaceChildren();
    const active = data.active_streams || [];
    active.forEach((entry, idx) => {
      const row = makeEl("div", "stream-limit-item");
      const badge = makeEl("span", "stream-limit-badge", `Screen ${idx + 1}`);
      const info = makeEl("div", "stream-limit-info");
      info.appendChild(makeEl("strong", "stream-limit-item-title", entry.title || "Playing now"));
      info.appendChild(
        makeEl("span", "stream-limit-item-profile", `Profile: ${entry.profile_name || "Main"}`)
      );
      row.appendChild(badge);
      row.appendChild(info);
      streamLimitList.appendChild(row);
    });
  }

  streamLimitOverlay.hidden = false;
}

function startStreamHeartbeat() {
  stopStreamHeartbeat();
  state.player.heartbeatTimer = setInterval(async () => {
    if (!playerDialog.open || !state.player.item) {
      stopStreamHeartbeat();
      return;
    }
    try {
      const res = await fetch("/api/stream/heartbeat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCsrfToken(),
          Accept: "application/json",
        },
        body: JSON.stringify({
          stream_token: TAB_STREAM_TOKEN,
          title: displayTitle(state.player.item),
          media_type: state.player.item.media_type || "movie",
          tmdb_id: state.player.item.id || 0,
        }),
      });
      const data = await res.json();
      if (data && data.terminated) {
        showStreamLimitScreen({
          error:
            data.reason ||
            "Playback was transferred to another screen because your account reached the 3-screen limit.",
          active_streams: [],
        });
      }
    } catch (error) {
      // ignore transient network errors
    }
  }, 20000);
}

async function acquireStreamSlot(forceTakeover = false) {
  const item = state.player.item;
  if (!item) return false;
  try {
    const res = await fetch("/api/stream/acquire", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
        Accept: "application/json",
      },
      body: JSON.stringify({
        stream_token: TAB_STREAM_TOKEN,
        title: displayTitle(item),
        media_type: item.media_type || "movie",
        tmdb_id: item.id || 0,
        force_takeover: Boolean(forceTakeover),
      }),
    });
    const data = await res.json();
    if (res.status === 429 || data.stream_limit_reached) {
      showStreamLimitScreen(data);
      return false;
    }
    if (streamLimitOverlay) streamLimitOverlay.hidden = true;
    startStreamHeartbeat();
    return true;
  } catch (error) {
    console.error(error);
    return true;
  }
}

async function updatePlayerSource(forceTakeover = false) {
  const item = state.player.item;
  if (!item) return;

  if (item.media_type === "tv") {
    playerSub.textContent = `Season ${state.player.season} · Episode ${state.player.episode}`;
    const episode = currentPlayerEpisode();
    if (episode) {
      playerSub.textContent += ` · ${episode.name}`;
      episodeSelect.value = String(episode.episode_number);
    }
  } else {
    playerSub.textContent = [item.year, formatRuntime(item.runtime)].filter(Boolean).join(" · ");
  }

  const startAt = state.player.startAt || 0;
  state.player.currentTime = startAt;
  state.player.duration = 0;

  const allowed = await acquireStreamSlot(forceTakeover);
  if (!allowed) {
    syncPlayerNav();
    return;
  }

  await checkDirectStreamForCurrentTitle();
  loadSubtitlesForCurrentTitle();
  startSubtitleClock();

  const useNative =
    state.player.directStream &&
    state.player.server === "native";

  function fallbackToIframe() {
    stopNativeVideo();
    if (lumiereNativeStage) lumiereNativeStage.hidden = true;
    player.hidden = false;
    state.player.server = "s1";
    if (playerServer) playerServer.value = "s1";
    player.src = playerUrl(item, state.player.season, state.player.episode, startAt);
  }

  function canBrowserPlayHevc() {
    const v = document.createElement("video");
    return Boolean(
      v.canPlayType('video/mp4; codecs="hev1.1.6.L93.90"') ||
      v.canPlayType('video/mp4; codecs="hevc"')
    );
  }

  if (useNative && lumiereNativeStage && lumiereVideo) {
    state.player.server = "native";
    if (playerServer) playerServer.value = "native";

    const stream = state.player.directStream;
    if (stream.type === "dash" && !canBrowserPlayHevc()) {
      showToast("Your browser does not support HEVC hardware playback. Streaming via Server 1...");
      fallbackToIframe();
      state.player.startAt = 0;
      syncPlayerNav();
      queueHistorySave();
      return;
    }

    player.src = "about:blank";
    player.hidden = true;
    lumiereNativeStage.hidden = false;
    if (lumiereQualityBadge) {
      lumiereQualityBadge.textContent = (state.player.directStream.quality_label || "1080p FULL HD").toUpperCase();
    }
    stopNativeVideo();

    let played = false;
    if (stream.type === "dash" && window.dashjs && typeof dashjs.supportsMediaSource === "function" && dashjs.supportsMediaSource()) {
      try {
        const dp = dashjs.MediaPlayer().create();
        dp.initialize(lumiereVideo, stream.url, true);
        window.lumiereDashPlayer = dp;
        dp.on(dashjs.MediaPlayer.events.ERROR, (e) => {
          console.warn("DASH player error, fallback to mirror:", e);
          fallbackToIframe();
        });
        if (startAt > 1) {
          dp.on(dashjs.MediaPlayer.events.STREAM_INITIALIZED, () => {
            dp.seek(startAt);
          });
        }
        played = true;
      } catch (err) {
        console.error("DASH init error:", err);
      }
    } else if (stream.type === "mp4" || (stream.url && stream.url.endsWith(".mp4"))) {
      lumiereVideo.src = stream.url;
      if (startAt > 1) lumiereVideo.currentTime = startAt;
      lumiereVideo.play().catch(() => {});
      played = true;
    }

    if (!played) {
      fallbackToIframe();
    } else {
      syncNativePlayButton();
    }
  } else {
    fallbackToIframe();
  }

  state.player.startAt = 0;
  syncPlayerNav();
  queueHistorySave();
}

function syncPlayerNav() {
  if (!state.player.item || state.player.item.media_type !== "tv") return;
  const episodes = state.player.episodes || [];
  const index = episodes.findIndex((episode) => episode.episode_number === Number(state.player.episode));
  prevEpisodeBtn.disabled = index <= 0;
  nextEpisodeBtn.disabled = index < 0 || index >= episodes.length - 1;
}

async function loadPlayerSeason(seasonNumber, episodeToSelect = 1) {
  const item = state.player.item;
  if (!item) return;
  const requestId = ++state.player.requestId;
  playerEpisode.replaceChildren();

  const cacheKey = `${item.id}:${seasonNumber}`;
  let episodes = state.seasonCache[cacheKey];

  if (!episodes) {
    try {
      const data = await apiFetch(`/api/tv/${item.id}/season/${seasonNumber}`);
      if (requestId !== state.player.requestId) return;
      episodes = data.episodes || [];
      state.seasonCache[cacheKey] = episodes;
    } catch (error) {
      if (requestId !== state.player.requestId) return;
      console.error(error);
      episodes = [];
    }
  }

  state.player.season = seasonNumber;
  state.player.episodes = episodes;

  episodes.forEach((episode) => {
    const option = document.createElement("option");
    option.value = String(episode.episode_number);
    option.textContent = `${episode.episode_number}. ${episode.name}`;
    playerEpisode.appendChild(option);
  });

  const validEpisode = episodes.some((episode) => episode.episode_number === Number(episodeToSelect))
    ? Number(episodeToSelect)
    : episodes[0]?.episode_number || 1;
  state.player.episode = validEpisode;
  playerEpisode.value = String(validEpisode);
  updatePlayerSource();
}

async function openPlayer(item, season = 1, episode = 1, startAt = 0) {
  if (!item) return;
  let title = { ...item };

  if (title.media_type === "tv" && (!title.seasons || !title.seasons.length)) {
    try {
      const data = await apiFetch(`/api/title/tv/${title.id}`);
      title = { ...title, ...data };
    } catch (error) {
      console.error(error);
    }
  }

  state.detail = state.detail && state.detail.id === title.id ? { ...state.detail, ...title } : title;
  state.player = {
    item: title,
    server: playerServer && playerServer.value ? playerServer.value : "s1",
    seasons: title.seasons || [],
    episodes: [],
    season,
    episode,
    startAt: Number(startAt) || 0,
    currentTime: Number(startAt) || 0,
    duration: 0,
    requestId: state.player.requestId + 1,
  };

  playerTitle.textContent = displayTitle(title);

  if (title.media_type === "tv") {
    playerEpisodeControls.hidden = false;
    const usableSeasons = (title.seasons || []).filter((s) => s.season_number > 0);
    const seasons = usableSeasons.length ? usableSeasons : title.seasons || [];
    if (!seasons.length) {
      const fallback = [{ season_number: season, name: `Season ${season}` }];
      ensureSeasonOptions(fallback);
    } else {
      ensureSeasonOptions(seasons);
    }
    playerSeason.value = String(season);
    await loadPlayerSeason(season, episode);
  } else {
    playerEpisodeControls.hidden = true;
    state.player.seasons = [];
    state.player.episodes = [];
    updatePlayerSource();
  }

  if (!playerDialog.open) playerDialog.showModal();
}

// ---------------------------------------------------------------------------
// Household Profiles ("Who's Watching?" — Authentic Netflix Experience)
// ---------------------------------------------------------------------------

const NF_AVATAR_GRADIENTS = {
  "#e50914": "linear-gradient(155deg, #f8222d 0%, #c10710 65%, #8a040a 100%)",
  "#2563eb": "linear-gradient(155deg, #3b82f6 0%, #1d4ed8 65%, #172554 100%)",
  "#10b981": "linear-gradient(155deg, #34d399 0%, #059669 65%, #064e3b 100%)",
  "#f59e0b": "linear-gradient(155deg, #fbbf24 0%, #d97706 65%, #78350f 100%)",
  "#8b5cf6": "linear-gradient(155deg, #a78bfa 0%, #6d28d9 65%, #3b0764 100%)",
  "#ec4899": "linear-gradient(155deg, #f472b6 0%, #db2777 65%, #831843 100%)",
};

function createNetflixFaceSvg(isKids = false) {
  return `
    <svg class="nf-face-svg" viewBox="0 0 120 120" fill="none" aria-hidden="true">
      <circle cx="38" cy="48" r="${isKids ? 6.5 : 5.8}" fill="#ffffff"/>
      <circle cx="82" cy="48" r="${isKids ? 6.5 : 5.8}" fill="#ffffff"/>
      ${
        isKids
          ? '<circle cx="26" cy="60" r="6" fill="rgba(255,255,255,0.22)"/><circle cx="94" cy="60" r="6" fill="rgba(255,255,255,0.22)"/>'
          : ""
      }
      <path d="M 35 72 Q 62 93 87 69" stroke="#ffffff" stroke-width="6.5" stroke-linecap="round" fill="none"/>
    </svg>
  `;
}

function paintNetflixAvatar(el, colorHex, isKids = false) {
  if (!el) return;
  const bg = NF_AVATAR_GRADIENTS[colorHex] || NF_AVATAR_GRADIENTS["#e50914"];
  el.style.background = bg;
  el.innerHTML = createNetflixFaceSvg(isKids);
  if (isKids) {
    const kidsTag = makeEl("span", "nf-tile-kids-ribbon", "KIDS");
    el.appendChild(kidsTag);
  }
}

function updateActiveProfileUI(activeProfile, profiles) {
  if (!activeProfile) return;
  state.activeProfile = activeProfile;
  if (Array.isArray(profiles) && profiles.length) {
    state.profiles = profiles;
  }
  if (headerProfileAvatar) {
    const bg = NF_AVATAR_GRADIENTS[activeProfile.avatar_color] || activeProfile.avatar_color || "#e50914";
    headerProfileAvatar.style.background = bg;
    headerProfileAvatar.innerHTML = `
      <svg viewBox="0 0 120 120" width="22" height="22" fill="none" aria-hidden="true">
        <circle cx="38" cy="48" r="7" fill="#fff"/>
        <circle cx="82" cy="48" r="7" fill="#fff"/>
        <path d="M 34 73 Q 62 94 88 70" stroke="#fff" stroke-width="8" stroke-linecap="round" fill="none"/>
      </svg>
    `;
  }
  if (headerProfileName) {
    headerProfileName.textContent = activeProfile.name || "Profile";
  }
  if (headerKidsBadge) {
    headerKidsBadge.hidden = !activeProfile.is_kids;
  }
  if (profileDialog && profileDialog.open) {
    renderProfileCards();
  }
}

function renderProfileCards() {
  if (!profileCardsGrid) return;
  profileCardsGrid.replaceChildren();
  const profiles = state.profiles || [];
  const activeId = state.activeProfile?.id;
  const managing = Boolean(state.profileManageMode);

  if (profileDialogTitle) {
    profileDialogTitle.textContent = managing ? "Manage Profiles:" : "Who's watching?";
  }
  if (nfManageProfilesBtn) {
    nfManageProfilesBtn.textContent = managing ? "Done" : "Manage Profiles";
    nfManageProfilesBtn.classList.toggle("done-mode", managing);
  }

  profiles.forEach((prof, index) => {
    const item = makeEl("div", `nf-profile-item${prof.id === activeId ? " is-current" : ""}${managing ? " is-managing" : ""}`);
    item.setAttribute("role", "listitem");

    const btn = makeEl("button", "nf-profile-btn");
    btn.type = "button";
    btn.setAttribute(
      "aria-label",
      managing
        ? `Edit profile ${prof.name}`
        : `Watch as ${prof.name}${prof.is_kids ? " (Kids)" : ""}`
    );

    const tile = makeEl("div", "nf-avatar-tile");
    paintNetflixAvatar(tile, prof.avatar_color || "#e50914", Boolean(prof.is_kids));

    if (managing) {
      const editVeil = makeEl("div", "nf-avatar-edit-veil");
      editVeil.innerHTML = `
        <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 20h9"></path>
          <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
        </svg>
      `;
      tile.appendChild(editVeil);
    }

    const nameEl = makeEl("span", "nf-profile-name", prof.name);
    btn.appendChild(tile);
    btn.appendChild(nameEl);

    btn.addEventListener("click", () => {
      if (state.profileManageMode) {
        openProfileEditor(prof, index === 0 || profiles.length <= 1);
      } else {
        selectHouseholdProfile(prof.id);
      }
    });

    item.appendChild(btn);
    profileCardsGrid.appendChild(item);
  });

  if (profiles.length < 4) {
    const addItem = makeEl("div", "nf-profile-item nf-add-item");
    addItem.setAttribute("role", "listitem");
    const addBtn = makeEl("button", "nf-profile-btn nf-add-profile-btn");
    addBtn.type = "button";
    addBtn.setAttribute("aria-label", "Add Profile");

    const addTile = makeEl("div", "nf-avatar-tile nf-add-tile");
    addTile.innerHTML = `
      <span class="nf-add-circle" aria-hidden="true">
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </span>
    `;
    const addName = makeEl("span", "nf-profile-name", "Add Profile");
    addBtn.appendChild(addTile);
    addBtn.appendChild(addName);
    addBtn.addEventListener("click", () => openProfileEditor(null, false));
    addItem.appendChild(addBtn);
    profileCardsGrid.appendChild(addItem);
  }
}

function openProfileEditor(profile = null, isPrimary = false) {
  state.editingProfile = profile;
  if (nfProfilePicker) nfProfilePicker.hidden = true;
  if (profileCreateForm) profileCreateForm.hidden = false;

  const defaultColors = ["#e50914", "#2563eb", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899"];
  const usedColors = (state.profiles || []).map((p) => p.avatar_color);
  const nextFreeColor = defaultColors.find((c) => !usedColors.includes(c)) || "#2563eb";

  if (profile) {
    if (editProfileIdInput) editProfileIdInput.value = String(profile.id);
    if (nfEditorTitle) nfEditorTitle.textContent = "Edit Profile";
    if (nfEditorSub) nfEditorSub.textContent = "Update profile name, look, or Kids settings.";
    if (newProfileName) newProfileName.value = profile.name || "";
    if (newProfileKids) newProfileKids.checked = Boolean(profile.is_kids);
    if (createProfileBtn) createProfileBtn.textContent = "Save";
    state.selectedProfileColor = profile.avatar_color || "#e50914";
    if (nfEditorDeleteBtn) {
      nfEditorDeleteBtn.hidden = Boolean(isPrimary);
    }
  } else {
    if (editProfileIdInput) editProfileIdInput.value = "";
    if (nfEditorTitle) nfEditorTitle.textContent = "Add Profile";
    if (nfEditorSub) nfEditorSub.textContent = "Add a profile for another person watching Lumière.";
    if (newProfileName) newProfileName.value = "";
    if (newProfileKids) newProfileKids.checked = false;
    if (createProfileBtn) createProfileBtn.textContent = "Continue";
    state.selectedProfileColor = nextFreeColor;
    if (nfEditorDeleteBtn) nfEditorDeleteBtn.hidden = true;
  }

  if (profileColorSwatches) {
    profileColorSwatches.querySelectorAll(".nf-swatch").forEach((b) => {
      b.classList.toggle("active", b.dataset.color === state.selectedProfileColor);
    });
  }
  paintNetflixAvatar(
    nfEditorAvatarPreview,
    state.selectedProfileColor,
    Boolean(newProfileKids?.checked)
  );
  setTimeout(() => newProfileName?.focus(), 40);
}

function closeProfileEditor() {
  state.editingProfile = null;
  if (profileCreateForm) profileCreateForm.hidden = true;
  if (nfProfilePicker) nfProfilePicker.hidden = false;
  renderProfileCards();
}

async function openProfileDialog(isGate = false) {
  if (!profileDialog) return;
  state.profileGateActive = Boolean(isGate);
  state.profileManageMode = false;
  state.editingProfile = null;
  if (profileCreateForm) profileCreateForm.hidden = true;
  if (nfProfilePicker) nfProfilePicker.hidden = false;
  profileDialog.classList.toggle("gate-mode", state.profileGateActive);
  if (profileDialogClose) {
    profileDialogClose.hidden = state.profileGateActive;
  }
  try {
    const data = await apiFetch("/api/profiles");
    updateActiveProfileUI(data.active_profile, data.profiles || []);
  } catch (error) {
    console.error(error);
  }
  renderProfileCards();
  if (!profileDialog.open) profileDialog.showModal();
}

async function selectHouseholdProfile(profileId) {
  const wasGate = state.profileGateActive;
  const unchangedProfile = state.activeProfile && Number(state.activeProfile.id) === Number(profileId);
  try {
    const res = await fetch("/api/profiles/select", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": getCsrfToken(),
        Accept: "application/json",
      },
      body: JSON.stringify({ profile_id: profileId }),
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || "Unable to switch profile");
      return;
    }
    state.profileGateActive = false;
    state.profileManageMode = false;
    if (profileDialog) profileDialog.classList.remove("gate-mode");
    if (profileDialogClose) profileDialogClose.hidden = false;
    updateActiveProfileUI(data.active_profile, data.profiles || []);
    if (profileDialog && profileDialog.open) profileDialog.close();
    if (!wasGate) {
      showToast(`Switched to ${data.active_profile.name}${data.active_profile.is_kids ? " (Kids)" : ""}`);
    }
    if (!wasGate || !unchangedProfile) {
      state.homeLoaded = false;
      setView("home");
      loadHome();
    }
  } catch (error) {
    console.error(error);
    showToast("Unable to switch profile");
  }
}

async function deleteHouseholdProfile(profileId, name) {
  try {
    const res = await fetch(`/api/profiles/${profileId}`, {
      method: "DELETE",
      headers: {
        "X-CSRF-Token": getCsrfToken(),
        Accept: "application/json",
      },
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.error || "Could not remove profile");
      return;
    }
    updateActiveProfileUI(data.active_profile, data.profiles || []);
    closeProfileEditor();
    showToast(`Deleted profile “${name}”`);
    state.homeLoaded = false;
    loadHome();
  } catch (error) {
    console.error(error);
    showToast("Could not remove profile");
  }
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

document.querySelectorAll(".nav-link").forEach((link) => {
  link.addEventListener("click", () => {
    const view = link.dataset.view;
    clearTimeout(state.search._timer);
    state.search.requestId++;
    searchInput.value = "";
    searchClear.hidden = true;
    if (view === "home") {
      setView("home");
      loadHome();
    } else {
      openBrowse(view);
    }
  });
});

$("brandHome").addEventListener("click", (event) => {
  event.preventDefault();
  document.querySelector('.nav-link[data-view="home"]').click();
});

heroPlay.addEventListener("click", () => {
  if (state.currentHero) openPlayer(state.currentHero, 1, 1);
});

if (heroWatchlist) {
  heroWatchlist.addEventListener("click", () => {
    if (state.currentHero) toggleWatchlist(state.currentHero);
  });
}

heroInfo.addEventListener("click", () => {
  if (state.currentHero) openDetail(state.currentHero);
});

if (profileSwitchBtn) {
  profileSwitchBtn.addEventListener("click", () => openProfileDialog());
}

if (profileDialog) {
  profileDialog.addEventListener("cancel", (event) => {
    if (profileCreateForm && !profileCreateForm.hidden) {
      event.preventDefault();
      closeProfileEditor();
      return;
    }
    if (state.profileGateActive) {
      event.preventDefault();
    }
  });
}

if (profileDialogClose) {
  profileDialogClose.addEventListener("click", () => {
    if (!state.profileGateActive) profileDialog.close();
  });
}

if (nfManageProfilesBtn) {
  nfManageProfilesBtn.addEventListener("click", () => {
    state.profileManageMode = !state.profileManageMode;
    renderProfileCards();
  });
}

if (nfEditorCancelBtn) {
  nfEditorCancelBtn.addEventListener("click", () => {
    closeProfileEditor();
  });
}

if (nfEditorDeleteBtn) {
  nfEditorDeleteBtn.addEventListener("click", () => {
    if (state.editingProfile) {
      deleteHouseholdProfile(state.editingProfile.id, state.editingProfile.name);
    }
  });
}

if (newProfileKids) {
  newProfileKids.addEventListener("change", () => {
    paintNetflixAvatar(
      nfEditorAvatarPreview,
      state.selectedProfileColor || "#e50914",
      Boolean(newProfileKids.checked)
    );
  });
}

if (profileColorSwatches) {
  profileColorSwatches.querySelectorAll(".nf-swatch").forEach((btn) => {
    btn.addEventListener("click", () => {
      profileColorSwatches.querySelectorAll(".nf-swatch").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.selectedProfileColor = btn.dataset.color || "#e50914";
      paintNetflixAvatar(
        nfEditorAvatarPreview,
        state.selectedProfileColor,
        Boolean(newProfileKids?.checked)
      );
    });
  });
}

if (profileCreateForm) {
  profileCreateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = (newProfileName?.value || "").trim();
    if (!name) return;
    const editingId = editProfileIdInput?.value ? Number(editProfileIdInput.value) : 0;
    try {
      const url = editingId ? `/api/profiles/${editingId}` : "/api/profiles";
      const method = editingId ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCsrfToken(),
          Accept: "application/json",
        },
        body: JSON.stringify({
          name,
          avatar_color: state.selectedProfileColor || "#e50914",
          is_kids: Boolean(newProfileKids?.checked),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || "Could not save profile");
        return;
      }
      if (newProfileName) newProfileName.value = "";
      if (newProfileKids) newProfileKids.checked = false;
      updateActiveProfileUI(data.active_profile, data.profiles || []);
      if (editingId) {
        closeProfileEditor();
        showToast(`Saved profile “${name}”`);
        if (state.activeProfile && Number(state.activeProfile.id) === editingId) {
          state.homeLoaded = false;
          loadHome();
        }
      } else {
        state.profileGateActive = false;
        state.profileManageMode = false;
        closeProfileEditor();
        if (profileDialog) profileDialog.classList.remove("gate-mode");
        if (profileDialogClose) profileDialogClose.hidden = false;
        if (profileDialog && profileDialog.open) profileDialog.close();
        showToast(`Created profile “${data.active_profile.name}”`);
        state.homeLoaded = false;
        setView("home");
        loadHome();
      }
    } catch (error) {
      console.error(error);
      showToast("Could not save profile");
    }
  });
}

heroBg.addEventListener("animationend", () => {});

document.querySelector(".hero").addEventListener("mouseenter", () => {
  state.heroPaused = true;
});
document.querySelector(".hero").addEventListener("mouseleave", () => {
  state.heroPaused = false;
});

// Search interactions
searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = searchInput.value.trim();
  if (query) runSearch(query, 1, false);
});

searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim();
  searchClear.hidden = !query;
  clearTimeout(state.search._timer);
  if (!query) {
    clearSearch();
    return;
  }
  state.search._timer = setTimeout(() => runSearch(query, 1, false), 350);
});

searchClear.addEventListener("click", () => {
  searchInput.focus();
  clearSearch();
});

searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    clearSearch();
    searchInput.blur();
  }
});

document.addEventListener("keydown", (event) => {
  if (
    event.key === "/" &&
    document.activeElement !== searchInput &&
    !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName || "") &&
    !detailDialog.open &&
    !playerDialog.open &&
    !(profileDialog && profileDialog.open)
  ) {
    event.preventDefault();
    searchInput.focus();
    searchInput.select();
  }
});

browseMoreBtn.addEventListener("click", () => loadBrowse(state.browse.page + 1, true));
searchMoreBtn.addEventListener("click", () => runSearch(state.search.query, state.search.page + 1, true));

// Details
detailClose.addEventListener("click", () => detailDialog.close());
detailDialog.addEventListener("close", () => stopInlineTrailer());

if (detailWatchlist) {
  detailWatchlist.addEventListener("click", () => {
    if (state.detail) toggleWatchlist(state.detail);
  });
}

if (detailTrailerBtn) {
  detailTrailerBtn.addEventListener("click", () => toggleInlineTrailer());
}

detailPlay.addEventListener("click", () => {
  const item = state.detail;
  if (!item) return;
  const season = Number(seasonSelect.value) || 1;
  const episode = Number(episodeSelect.value) || 1;
  stopInlineTrailer();
  detailDialog.close();
  openPlayer(item, season, episode);
});

seasonSelect.addEventListener("change", () => {
  loadDetailSeason(Number(seasonSelect.value) || 1, 1);
});

episodeSelect.addEventListener("change", () => {
  const episodeNumber = Number(episodeSelect.value) || 1;
  const item = state.detail;
  if (!item) return;
  const key = `${item.id}:${Number(seasonSelect.value)}`;
  populateEpisodeSelect(state.seasonCache[key] || [], episodeNumber);
});

// Player
playerClose.addEventListener("click", () => playerDialog.close());
playerDialog.addEventListener("close", () => {
  saveHistory();
  releaseStreamSlot();
  stopSubtitleClock();
  stopNativeVideo();
  if (streamLimitOverlay) streamLimitOverlay.hidden = true;
  if (subtitlePopover) subtitlePopover.hidden = true;
  if (adminStreamBar) adminStreamBar.hidden = true;
  player.src = "about:blank";
});

if (streamTakeoverBtn) {
  streamTakeoverBtn.addEventListener("click", () => {
    updatePlayerSource(true);
  });
}

if (streamLimitCloseBtn) {
  streamLimitCloseBtn.addEventListener("click", () => {
    playerDialog.close();
  });
}

window.addEventListener("pagehide", () => {
  if (playerDialog && playerDialog.open) {
    releaseStreamSlot();
  }
});

// Native Lumière Video Controls
if (lumiereVideo) {
  const togglePlay = () => {
    if (lumiereVideo.paused) {
      lumiereVideo.play().catch(() => {});
    } else {
      lumiereVideo.pause();
    }
    syncNativePlayButton();
  };
  lumiereVideo.addEventListener("click", togglePlay);
  if (lumiereCenterPlay) lumiereCenterPlay.addEventListener("click", togglePlay);
  if (lumierePlayBtn) lumierePlayBtn.addEventListener("click", togglePlay);
  lumiereVideo.addEventListener("play", syncNativePlayButton);
  lumiereVideo.addEventListener("pause", () => {
    syncNativePlayButton();
    saveHistory(false);
  });
  lumiereVideo.addEventListener("ended", () => {
    syncNativePlayButton();
    saveHistory(true, true);
    if (state.player.item && state.player.item.media_type === "tv") {
      const episodes = state.player.episodes || [];
      const index = episodes.findIndex((ep) => ep.episode_number === Number(state.player.episode));
      if (index >= 0 && index < episodes.length - 1) {
        state.player.episode = episodes[index + 1].episode_number;
        if (playerEpisode) playerEpisode.value = String(state.player.episode);
        showToast(`Next Episode: S${state.player.season} E${state.player.episode}`);
        updatePlayerSource();
      }
    }
  });
  lumiereVideo.addEventListener("timeupdate", () => {
    const cur = Number(lumiereVideo.currentTime) || 0;
    const dur = Number(lumiereVideo.duration) || 0;
    state.player.currentTime = cur;
    state.player.duration = dur;
    if (lumiereTimeline && dur > 0) {
      lumiereTimeline.value = String(Math.round((cur / dur) * 1000));
    }
    if (lumiereTimeLabel) {
      lumiereTimeLabel.textContent = `${formatTimestamp(cur)} / ${formatTimestamp(dur)}`;
    }
    renderActiveSubtitleCue();
  });
  if (lumiereTimeline) {
    lumiereTimeline.addEventListener("input", () => {
      const dur = Number(lumiereVideo.duration) || 0;
      if (dur > 0) {
        lumiereVideo.currentTime = (Number(lumiereTimeline.value) / 1000) * dur;
      }
    });
  }
  if (lumiereRewBtn) {
    lumiereRewBtn.addEventListener("click", () => {
      lumiereVideo.currentTime = Math.max(0, (Number(lumiereVideo.currentTime) || 0) - 10);
    });
  }
  if (lumiereFwdBtn) {
    lumiereFwdBtn.addEventListener("click", () => {
      lumiereVideo.currentTime = (Number(lumiereVideo.currentTime) || 0) + 10;
    });
  }
  if (lumiereMuteBtn) {
    lumiereMuteBtn.addEventListener("click", () => {
      lumiereVideo.muted = !lumiereVideo.muted;
      lumiereMuteBtn.classList.toggle("active", lumiereVideo.muted);
    });
  }
  if (lumiereVolumeSlider) {
    lumiereVolumeSlider.addEventListener("input", () => {
      lumiereVideo.volume = Number(lumiereVolumeSlider.value);
      lumiereVideo.muted = lumiereVideo.volume === 0;
    });
  }
  if (lumiereSpeedSelect) {
    lumiereSpeedSelect.addEventListener("change", () => {
      lumiereVideo.playbackRate = Number(lumiereSpeedSelect.value) || 1;
    });
  }
  if (lumierePipBtn) {
    lumierePipBtn.addEventListener("click", async () => {
      try {
        if (document.pictureInPictureElement) {
          await document.exitPictureInPicture();
        } else if (lumiereVideo.requestPictureInPicture) {
          await lumiereVideo.requestPictureInPicture();
        }
      } catch (err) {
        showToast("Picture-in-Picture unavailable");
      }
    });
  }
}

// Admin Direct Stream Bar
if (adminStreamBtn && adminStreamBar) {
  adminStreamBtn.addEventListener("click", () => {
    adminStreamBar.hidden = !adminStreamBar.hidden;
    if (!adminStreamBar.hidden && adminStreamInput) adminStreamInput.focus();
  });
  adminStreamBar.addEventListener("submit", async (event) => {
    event.preventDefault();
    const item = state.player.item;
    const url = (adminStreamInput?.value || "").trim();
    if (!item || !url) return;
    try {
      const res = await fetch(`/api/stream/${item.media_type}/${item.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": getCsrfToken(),
          Accept: "application/json",
        },
        body: JSON.stringify({
          season: state.player.season || 1,
          episode: state.player.episode || 1,
          stream_url: url,
          quality_label: "1080p Full HD",
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        showToast(data.error || "Could not attach stream");
        return;
      }
      adminStreamBar.hidden = true;
      state.player.server = "native";
      showToast("Switched to Lumière Native Player");
      updatePlayerSource();
    } catch (err) {
      console.error(err);
      showToast("Could not save direct stream");
    }
  });
  if (adminStreamClearBtn) {
    adminStreamClearBtn.addEventListener("click", async () => {
      const item = state.player.item;
      if (!item) return;
      await fetch(
        `/api/stream/${item.media_type}/${item.id}?season=${state.player.season || 1}&episode=${state.player.episode || 1}`,
        {
          method: "DELETE",
          headers: { "X-CSRF-Token": getCsrfToken(), Accept: "application/json" },
        }
      );
      if (adminStreamInput) adminStreamInput.value = "";
      adminStreamBar.hidden = true;
      state.player.server = "s1";
      showToast("Cleared custom stream");
      updatePlayerSource();
    });
  }
}

// Subtitles Studio Popover & Controls
if (subtitleMenuBtn && subtitlePopover) {
  subtitleMenuBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    const willOpen = subtitlePopover.hidden;
    subtitlePopover.hidden = !willOpen;
    subtitleMenuBtn.setAttribute("aria-expanded", willOpen ? "true" : "false");
  });
  subtitlePopover.addEventListener("click", (event) => event.stopPropagation());
  document.addEventListener("click", () => {
    if (subtitlePopover && !subtitlePopover.hidden) {
      subtitlePopover.hidden = true;
      subtitleMenuBtn.setAttribute("aria-expanded", "false");
    }
  });
}

if (subtitleUploadBtn && subtitleFileInput) {
  subtitleUploadBtn.addEventListener("click", () => subtitleFileInput.click());
  subtitleFileInput.addEventListener("change", async () => {
    const file = subtitleFileInput.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const cues = parseClientSubtitleText(text);
      if (!cues.length) {
        showToast("No valid subtitle timestamps found in file");
        return;
      }
      const customId = `custom_${Date.now()}`;
      const label = `Custom: ${file.name.replace(/\.(srt|vtt)$/i, "").slice(0, 22)}`;
      state.subtitles.tracks.unshift({ id: customId, label, lang: "custom", cues });
      renderSubtitleTracksList();
      selectSubtitleTrack(customId);
      subtitleFileInput.value = "";
    } catch (err) {
      console.error(err);
      showToast("Failed to read subtitle file");
    }
  });
}

if (subtitlePopover) {
  subtitlePopover.querySelectorAll("[data-offset-delta]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const delta = Number(btn.dataset.offsetDelta) || 0;
      state.subtitles.offset = Math.round((state.subtitles.offset + delta) * 100) / 100;
      if (subtitleOffsetValue) {
        const sign = state.subtitles.offset > 0 ? "+" : "";
        subtitleOffsetValue.textContent = `${sign}${state.subtitles.offset.toFixed(2)}s`;
      }
      renderActiveSubtitleCue();
    });
  });
  const resetBtn = subtitlePopover.querySelector("[data-offset-reset]");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      state.subtitles.offset = 0;
      if (subtitleOffsetValue) subtitleOffsetValue.textContent = "0.0s";
      renderActiveSubtitleCue();
    });
  }
}

if (subtitleClockToggle) {
  subtitleClockToggle.addEventListener("click", () => {
    state.subtitles.clockRunning = !state.subtitles.clockRunning;
    subtitleClockToggle.textContent = state.subtitles.clockRunning ? "Pause Clock" : "Resume Clock";
  });
}
if (subtitleClockBack) {
  subtitleClockBack.addEventListener("click", () => {
    state.player.currentTime = Math.max(0, (Number(state.player.currentTime) || 0) - 10);
    renderActiveSubtitleCue();
  });
}
if (subtitleClockFwd) {
  subtitleClockFwd.addEventListener("click", () => {
    state.player.currentTime = (Number(state.player.currentTime) || 0) + 10;
    renderActiveSubtitleCue();
  });
}

if (subtitleSizeGroup) {
  subtitleSizeGroup.querySelectorAll("[data-sub-size]").forEach((btn) => {
    btn.addEventListener("click", () => {
      subtitleSizeGroup.querySelectorAll("[data-sub-size]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.subtitles.size = btn.dataset.subSize || "md";
      applySubtitleAppearance();
    });
  });
}

if (subtitleColorGroup) {
  subtitleColorGroup.querySelectorAll("[data-sub-color]").forEach((btn) => {
    btn.addEventListener("click", () => {
      subtitleColorGroup.querySelectorAll("[data-sub-color]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.subtitles.color = btn.dataset.subColor || "#ffffff";
      applySubtitleAppearance();
    });
  });
}

if (subtitleBgToggle) {
  subtitleBgToggle.addEventListener("click", () => {
    const order = ["glass", "solid", "shadow"];
    const next = order[(order.indexOf(state.subtitles.bgMode) + 1) % order.length];
    state.subtitles.bgMode = next;
    applySubtitleAppearance();
  });
}

applySubtitleAppearance();

if (playerServer) {
  playerServer.addEventListener("change", () => {
    state.player.server = playerServer.value || "s1";
    updatePlayerSource();
    showToast(`Switched stream to ${playerServer.options[playerServer.selectedIndex]?.text || "Backup Server"}`);
  });
}

playerSeason.addEventListener("change", () => {
  loadPlayerSeason(Number(playerSeason.value) || 1, 1);
});

playerEpisode.addEventListener("change", () => {
  state.player.episode = Number(playerEpisode.value) || 1;
  updatePlayerSource();
});

prevEpisodeBtn.addEventListener("click", () => {
  const episodes = state.player.episodes || [];
  const index = episodes.findIndex((episode) => episode.episode_number === Number(state.player.episode));
  if (index > 0) {
    state.player.episode = episodes[index - 1].episode_number;
    playerEpisode.value = String(state.player.episode);
    updatePlayerSource();
  }
});

nextEpisodeBtn.addEventListener("click", () => {
  const episodes = state.player.episodes || [];
  const index = episodes.findIndex((episode) => episode.episode_number === Number(state.player.episode));
  if (index >= 0 && index < episodes.length - 1) {
    state.player.episode = episodes[index + 1].episode_number;
    playerEpisode.value = String(state.player.episode);
    updatePlayerSource();
  }
});

fullscreenBtn.addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else if (playerFrameWrap.requestFullscreen) {
      await playerFrameWrap.requestFullscreen();
    }
  } catch (error) {
    showToast("Fullscreen is not available in this browser.");
  }
});

// VidFast playback progress (postMessage events)
const VIDFAST_HOST_RE = /(^|\.)vidfast\.(vc|pro|in|io|me|net|pm|xyz|bz)$/i;
let lastProgressPersist = 0;

window.addEventListener("message", (event) => {
  if (!playerDialog.open || !state.player.item) return;
  let host;
  try {
    host = new URL(event.origin).hostname;
  } catch (error) {
    return;
  }
  if (!VIDFAST_HOST_RE.test(host)) return;

  const payload = event.data;
  if (!payload || typeof payload !== "object") return;
  if (payload.type !== "PLAYER_EVENT" && payload.type !== "MEDIA_DATA") return;

  const data = payload.data || payload;
  if (data.tmdbId && String(data.tmdbId) !== String(state.player.item.id)) return;

  const currentTime = Number(data.currentTime);
  const duration = Number(data.duration);
  if (Number.isFinite(currentTime) && currentTime >= 0) {
    state.player.currentTime = currentTime;
    state.subtitles.lastExternalSync = Date.now();
    renderActiveSubtitleCue();
  }
  if (Number.isFinite(duration) && duration > 0) state.player.duration = duration;

  const eventName = data.event || "";
  const now = Date.now();
  if (eventName === "ended") {
    saveHistory(true, true);
  } else if (eventName === "pause" || eventName === "seeked") {
    saveHistory(false);
  } else if (now - lastProgressPersist > 15000) {
    lastProgressPersist = now;
    saveHistory(false);
  }
});

// Header shadow on scroll
window.addEventListener(
  "scroll",
  () => {
    siteHeader.classList.toggle("scrolled", window.scrollY > 12);
  },
  { passive: true }
);

// ==========================================
// Lumière AdShield — Anti-Popup & Anti-Redirect Engine
// ==========================================
(function initAdShield() {
  const originalWindowOpen = window.open;
  window._isAuthorizedNavigation = false;

  // Intercept and neutralize rogue popup attempts while streaming
  window.open = function (url, target, features) {
    if (playerDialog && playerDialog.open) {
      console.warn("[Lumière AdShield] Neutralized popup window attempt:", url);
      return null;
    }
    return originalWindowOpen.call(window, url, target, features);
  };

  // Prevent background popunder focus theft
  window.addEventListener("blur", () => {
    if (playerDialog && playerDialog.open) {
      setTimeout(() => {
        try {
          window.focus();
        } catch (e) {}
      }, 50);
    }
  });

  // Guard against top-window navigation hijack while player is open
  window.addEventListener("beforeunload", (e) => {
    if (playerDialog && playerDialog.open && !window._isAuthorizedNavigation) {
      e.preventDefault();
      return (e.returnValue = "Playback in progress. Stay on Lumière?");
    }
  });

  // Mark intentional app navigations as authorized
  document.addEventListener("click", (e) => {
    const link = e.target.closest("a, form");
    if (link) {
      window._isAuthorizedNavigation = true;
      setTimeout(() => {
        window._isAuthorizedNavigation = false;
      }, 2000);
    }
  });
})();

// Light dismiss for dialogs
enableLightDismiss(detailDialog);
enableLightDismiss(playerDialog);
if (profileDialog) enableLightDismiss(profileDialog);

// Boot
document.addEventListener("DOMContentLoaded", () => {
  loadHome();
});
