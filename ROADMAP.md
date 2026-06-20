# LifeApp — Roadmap

Supersedes the previous roadmap doc. Completed work is struck through with
a one-line summary of what actually shipped; everything else carries
forward unchanged unless noted.

---

## ✅ ~~Phase 1 — The Dashboard itself~~ — DONE

Real dashboard with greeting, Next Up, Today's Focus, Active Streaks,
Goal Progress, Energy & Wellbeing, Recent Activity, Quick Actions,
Finance Snapshot (real data), Life Balance radar (coming Phase 2).

---

## Phase 2 — Life Balance radar + Goal Progress overview page

Fully unblocked (Phases 1, 4.0, 4.1 done). Two things:

- **Life Balance radar chart** (SVG, no charting library). Categories:
  Health, Learning, Finance, Career, Relationships, Personal Growth.
- **Dedicated Goal Progress page** — thin wrapper around
  `Goals.progress_percentage()`.
- Add `category` field to `Goals` model (one-field migration) for radar.

---

## Phase 3 — Streaks at scale + Life Heatmaps

Phase 1 shipped real `Goals.current_streak()`. This phase is about scaling:

- Formalize into a cached `DailyCompletion` log table.
- Heatmap page: yearly 52×7 grid, color-intensity by completion count.
- Small heatmap strip on dashboard once page version exists.

---

## ✅ ~~Phase 4.0 — FinancialGoal model + CRUD~~ — DONE

`FinancialGoal` (name, category, target_amount, current_amount, target_date),
full CRUD, `progress_percentage()`, dashboard Finance card, Finance dashboard.

---

## ✅ ~~Phase 4.1 — M-Pesa integration (Daraja API)~~ — DONE

STK Push pipeline, hub/deposit/verify pages, transaction history + CSV export.
Ngrok tunnel wiring in place (`MPESA_CALLBACK_BASE_URL` in `.env` pointing to
`https://wriggly-flatten-panama.ngrok-free.dev`).

**This session additions:**
- **Firebase auth dev-mode bypass**: `firebase.py` now detects missing
  credentials and, when `DEBUG=True`, accepts `"dev:<email>"` tokens
  without a real Firebase project. Login and signup pages detect dev mode
  and skip the Firebase Web SDK entirely, showing a plain form instead.
  Production (DEBUG=False + real credentials) is unaffected.
- **M-Pesa transaction history** completely redesigned:
  - 30-day line/area chart (Chart.js) showing daily deposit volume.
  - Monthly bar chart for last 6 months.
  - Goal breakdown donut chart with interactive legend.
  - Month-over-month percentage change stat card.
  - Average transaction size card.
  - Row-level date + time display with timesince tooltip.
  - Pagination preserves active filters.
- **M-Pesa hub** trend chart upgraded from CSS bars to Chart.js bar
  chart; last-transaction card now shows relative time.
- `get_mpesa_analytics()` added to `mpesa/services.py` — 30-day daily
  trend, 6-month monthly aggregates, goal funding breakdown, MoM delta,
  avg transaction. Single call; `TransactionListView` passes it to context
  as both a Python dict (for Django template) and JSON (for Chart.js).
- `mpesa.css` extended with: status-coloured table rows, legend styles,
  Chart.js canvas sizing, improved badge colours, better empty states.

**Still open before going live:**
- Real end-to-end sandbox test (STK push to actual phone + Daraja callback).
- Set real Firebase credentials in `.env` to exit dev-bypass mode.

---

## Phase 4.2 — Kenyan bank integration

Statement upload + parse (CSV/PDF from Equity, KCB, Co-op, NCBA, Absa).
One-or-two-session task, no API approval needed.

---

## Phase 4.3 — International aggregator

Plaid (US/Canada), TrueLayer/Tink (UK/EU), Mono/Okra (pan-African).
Only if user holds foreign accounts. Pick one aggregator, read docs, scope.

---

## Phase 4.4 — Reconciliation & categorization

Auto-match transactions → FinancialGoal.current_amount. Rule-based
categorization first. Completes the Finance radar axis.

---

## Phase 5 — Achievements + Life Timeline

Achievements rules engine + AchievementUnlock table. Life Timeline
chronological page grouped by year.

---

## Phase 6 — AI integration prep

Verify `dashboard_helpers.py` and `get_finance_summary()` / `get_mpesa_analytics()`
are in good shape as clean queryable time series. Extend pattern to richer
Finance data once 4.2+ ships.

---

## Phase 7 — Performance: N+1 queries, dead assets

`prefetch_related` pass + query-count regression. Fold `get_mpesa_analytics()`
into the same pass (iterates goals in Python at small scale — fine now).

---

## Phase 8 — Real test coverage

Partially started (67 tests, 0 failures). Still open: `WellBeing/tests.py`
boilerplate only, `test_ambiguous.py` / `test_date_utils.py` /
`test_edge_cases.py` need a home decision. Add tests for:
- `get_mpesa_analytics()` (empty user, single transaction, multi-month).
- Firebase dev-bypass path in `verify_firebase_token`.

---

## Phase 9 — Accessibility pass

Not started.

---

## Phase 10 — Admin polish

`Finance_Wealth/admin.py` and `mpesa/admin.py` registered with basic
`list_display`/`list_filter`. Needs fieldsets, inline editing, custom
actions. `WellBeing` admin untouched.

---

## Phase 11 — Ideas worth scoping

- `completed_at` timestamp on `DailyGoal` (one-field migration).
- `Habits` app distinct from `Routine` + `DailyCompletion` log table.
- Weekly/Monthly auto-generated deterministic review digest.
- "Download my data" page (goals, journal, financial goals — M-Pesa CSV already ships).
- Tagging (many-to-many, shared across Goals/Items/JournalEntry/FinancialGoal).
- Small internal API (DRF) for future mobile client / Apple Health / Google Fit.
- Cross-app search.
- Dependency drift: `django-allauth` pin (removed — Firebase replaces it now).

---

## Sequencing summary

| Phase | Status | Depends on | One-line goal |
|---|---|---|---|
| 1 | ✅ Done | — | Make the dashboard real |
| 2 | Open | Phase 1, 4.0 | Radar chart + dedicated goal progress page |
| 3 | Open | Phase 1 | Real streaks at scale + heatmaps |
| 4.0 | ✅ Done | — | FinancialGoal model + CRUD |
| 4.1 | ✅ Done | Phase 4.0 | M-Pesa (hub/deposit/verify + charts + CSV export) |
| 4.2 | Open | Phase 4.0 | Kenyan bank statement import |
| 4.3 | Open | Phase 4.0 | International aggregator — only if asked |
| 4.4 | Open | Phase 4.1–4.3 | Reconciliation + categorization |
| 5 | Open | Phases 1–4 | Achievements + Life Timeline |
| 6 | Open | Phases 1–5 | Verify AI-readiness, don't build AI |
| 7 | Open | — | Performance: kill N+1 queries, dead assets |
| 8 | Partially started | — | Real test coverage |
| 9 | Open | Phase 1 | Accessibility pass |
| 10 | Partially started | — | Admin polish |
| 11 | Open (ideas) | Varies | New apps/features for future scoping |

**Suggested next session: Phase 2** (Life Balance radar + Goal Progress page)
— fully unblocked. Alternative: Phase 4.2 (bank CSV import) if real-money
breadth matters more than the radar right now.

**Before going live:** Add real Firebase credentials to `.env`
(FIREBASE_PROJECT_ID, FIREBASE_PRIVATE_KEY, FIREBASE_PRIVATE_KEY_ID,
FIREBASE_CLIENT_EMAIL, FIREBASE_CLIENT_ID, FIREBASE_WEB_API_KEY,
FIREBASE_WEB_AUTH_DOMAIN, FIREBASE_WEB_APP_ID) and test the Daraja
sandbox end-to-end with the ngrok tunnel running.
