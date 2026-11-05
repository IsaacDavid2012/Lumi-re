# Lumière — Cinema, Beautifully Streamed

A minimal, ad-free streaming front end for a **1,266,484+ title** movie and TV catalog.
Browse with [The Movie Database (TMDB)](https://www.themoviedb.org/) metadata and stream
through a clean [VidFast](https://vidfast.vc/) player embed.

Includes:
- **Netflix/Prime-style Home**: Featured hero carousel, Top 10 rail, trending, popular,
  top-rated, in-theaters, coming-soon, and TV rows.
- **Live Search**: Debounced search across movies, series, and numeric TMDB IDs.
- **Browse Views**: Popular / Top Rated / In Theaters / Coming Soon / Trending with load-more.
- **Rich Details**: Backdrop art, cast, genres, runtime, seasons/episodes, trailer, and recommendations.
- **Streaming Player**: VidFast movie and TV embeds with season/episode switching and fullscreen.
- **Multi-User Accounts**: Self-service signup, per-user watch history, password updates, session revocation,
  admin account management, and account deletion.
- **Continue Watching**: Playback progress is autosaved per account via VidFast player events,
  including TV season/episode, resume timestamps, and one-click removal.
- **SQLite FTS5 Fallback**: Offline title search if the TMDB API is unavailable.
- **Hardened Security**: `scrypt` password hashing, constant-time verification, session version tokens (`auth_version`)
  for instant multi-device revocation, Origin + CSRF protection, HTTPOnly/SameSite session cookies,
  per-IP and per-account brute-force rate limiting, strict CSP, and security audit logging.
- **Brand Assets & PWA Manifest**: Custom `Lumière` SVG/ICO favicons, Apple Touch icon, and Web App Manifest.

---

## 🚀 Running the App

```bash
cd /jarvis/code/gmovies
python3 app.py
```

Open **http://localhost:5000** and sign in. Friends can create their own account at
**http://localhost:5000/signup**; each account gets a private Continue Watching list.

Default credentials (configured upon first run via environment variables or initial setup):

```text
username: admin (or configured via LUMIERE_ADMIN_USER)
password: <set your strong password upon initial setup>
```

Admins can create accounts, grant/revoke free ("comped") billing access, revoke active sessions, view the security audit log, and delete accounts from
**http://localhost:5000/admin**. Any user can manage their RM30/month Stripe subscription, update their password, sign out other devices, clear their
watch history, or delete their account from **http://localhost:5000/account**. Public Terms of Service, Site Rules, and Privacy Policy are served at
**http://localhost:5000/terms** and **http://localhost:5000/privacy**.

Environment variables (loaded automatically from `.env`):

```bash
LUMIERE_SITE_NAME=Lumière       # Optional custom brand name
LUMIERE_ADMIN_USER=Isaac        # Default admin username
LUMIERE_COOKIE_SECURE=1         # Set to 1 when serving exclusively over HTTPS
LUMIERE_TRUSTED_HOSTS=...       # Optional comma-separated allowed Host headers
FLASK_SECRET_KEY=...            # Optional fixed session secret (auto-persisted in data/.flask_secret_key)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_... # Optional Stripe webhook signing secret
STRIPE_PRICE_CENTS=3000         # 3000 = RM30.00 / month
STRIPE_CURRENCY=myr             # Malaysian Ringgit (myr)
TMDB_API_KEY=...                # TMDB v3 API key (defaults are included)
TMDB_READ_TOKEN=...             # Optional v4 bearer token
```

### API & System Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/home` | Hero titles plus all home rows (cached) |
| `GET /api/catalog?type=movie&category=popular&page=1` | Paginated browse catalog |
| `GET /api/search?q=...&type=multi&page=1` | Movie/TV/multi search with TMDB-ID lookup |
| `GET /api/title/<movie\|tv>/<id>` | Full details, cast, seasons, trailer, recommendations |
| `GET /api/tv/<id>/season/<n>` | Episode list for a season |
| `GET /api/history` | Current user's Continue Watching items |
| `POST /api/history` | Autosave a movie/TV playback position (CSRF protected) |
| `DELETE /api/history/<movie\|tv>/<id>` | Remove one title from the current user's history |
| `POST /account/password` | Change password and revoke all other sessions |
| `POST /account/revoke-sessions` | Sign out all other devices for the current account |
| `GET /healthz` | Healthcheck endpoint |

---

## 💻 CLI Search Tool (`search.py`)

You can also search directly from the terminal without starting the web server:

```bash
# Keyword & Full-Text Search
python3 search.py "Inception"
python3 search.py "Interstellar" --limit 5

# Look up directly by TMDB ID
python3 search.py --id 27205

# Match exact title
python3 search.py "The Dark Knight" --exact

# Show top popular movies
python3 search.py --top --limit 10
```

---

## 🐳 Docker Deployment

The application is fully containerized with automated restarts and production hardening:

```bash
docker compose up -d --build
```

Configured with:
- `restart: always`
- Healthcheck monitoring on port 5000
- Traefik integration on the `coolify` Docker network
- Automated routing for `movies.creativeclicks.art` and `testmovies.creativeclicks.art`

---

## 📱 Native Desktop & Mobile Apps

Lumière includes native installable apps across platforms (source in `apps/`):
- **Android**: Java 17 native wrapper (`Lumiere.apk`) with hardware acceleration and fullscreen video playback.
- **Windows**: Electron 33 NSIS installer (`Lumiere-Setup.exe`) with isolated sandbox security.
- **macOS**: Apple HFS hybrid volume disk image (`Lumiere.dmg`) and portable zip (`Lumiere-mac.zip`).
- **iOS / iPadOS**: Progressive Web App (PWA) with Apple touch icons and standalone full-screen support.

Download portal available at `/apps`.

---

## 🔄 Updating the Catalog

TMDB exports an updated dump of movie IDs and titles every day. To refresh your local database:

```bash
python3 update_catalog.py
```

This will automatically locate today's export file from `http://files.tmdb.org/p/exports/`, download it, and rebuild the SQLite database and search indexes.
