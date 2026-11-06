# Automatic article publishing — instructions for the scheduled run

Every run publishes **one** article: the first entry in `content/article-plan.json` whose `status` is `"planned"`.

## Steps

1. `git pull` the repo (branch `main`).
2. Open `content/article-plan.json` and take the first entry with `"status": "planned"`. If none is left, stop and report that the plan is finished.
3. Write the article as `content/articles/<slug>.json` with exactly these keys
   (copy the shape of `content/articles/facebook-ads-no-messages.json`):
   - `title_ar` — the plan's `title_ar` (you may tighten it; keep the keyword in it, under 70 characters).
   - `title_en` — the plan's `title_en`.
   - `excerpt_ar` — 1–2 sentences, about 150 characters, containing the keyword. This shows in Google results.
   - `excerpt_en` — English version of the excerpt.
   - `service` — the plan's `service` (`ads`, `reels`, `podcast` or `studio`).
   - `date` — today's date in Africa/Cairo, `YYYY-MM-DD`.
   - `minutes` — round(word count / 180), at least 3.
   - `draft` — `false`.
   - `cover` — `/uploads/articles/<slug>.jpg`.
   - `body_ar` — the article in Markdown (see rules below).
   - `body_en` — `""` (the English page falls back to Arabic).
4. Make the cover: `python3 tools/make_cover.py <slug> <service> "<title_en>"`.
5. In `content/article-plan.json` set that entry's `status` to `"published"` and `date` to today.
6. Run `python3 build.py`. It must finish with `built … files`. Then delete `dist/`, `preview/` and `__pycache__/`.
7. Commit (`Publish article: <slug>`) with the attribution lines the session asks for, and push to `main`.
   Cloudflare Pages rebuilds the live site from the push in about a minute.

## Writing rules (body_ar)

- **Egyptian Arabic**, clear and professional, the voice of the existing articles: direct, practical, no filler.
  Write "رسايل" not "رسائل", "إزاي", "عشان", etc., like the other articles.
- **700–1,200 words.** The first paragraph answers the question straight away — no long introduction.
- Structure with `##` headings (one question per section). Lists with `- ` or `1. `. Bold with `**…**`.
- **Never invent numbers, case studies, client names, results or statistics.** No "we raised X's bookings by 40%".
  Where a number depends on the business, explain how to calculate or judge it instead of giving one.
  Prices are allowed only from `content/pricing.json` (Marvels' own prices).
- Medical topics: general guidance only, no medical claims; mention that medical ads must follow the
  Egyptian Medical Syndicate and Ministry of Health rules.
- **At least two internal links**, as relative Markdown links:
  - the service page for the article's pillar: `[…](ads)`, `[…](reels)`, `[…](podcast)`, `[…](studio)`, `[…](pricing)`;
  - and one related, already-published article: `[…](blog-<slug>)` (check which slugs exist in `content/articles/`).
- End with a short "تبدأ منين؟" or similar practical checklist, then one natural line inviting a
  [free audit](audit) or the relevant service page. No hard sell.
- Not limited to Obour: write for businesses anywhere in Egypt (and the Arab world). Mention Obour / East Cairo only
  in studio or shooting topics, where the client has to come in person.

## Do not

- Do not change `build.py`, `src/`, `admin/` or any other content file.
- Do not publish more than one article per run.
- If the build fails, do not push; report the error.
