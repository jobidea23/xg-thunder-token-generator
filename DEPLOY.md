# Deploy XG THUNDER on Vercel — Full Guide

Is project me local server (Windows) + Vercel (cloud) dono support hai.

- Local: `start.bat` (ya `python dev_server.py`) → http://localhost:8000/
- Vercel: ek Flask app (`api/index.py`) + `public/` folder (website + admin panel)

---

## 1. Zaroori cheez — Vercel pe storage (Upstash Redis)

Vercel **serverless** hai — disk permanent nahi hota. Isliye settings (logo + platform
links) aur users **Upstash Redis** me save hote hain (free plan kaafi hai).

1. https://upstash.com par free account banao → **Create Database** (region: koi bhi paas wala).
2. Database khulne par **REST API** section se ye 2 values copy karo:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`
3. (Vercel KV use kar rahe ho to naam `KV_REST_API_URL` / `KV_REST_API_TOKEN` bhi chalega.)

> Redis set na ho to app chalega par settings/users save nahi honge (defaults use honge).

---

## 2. Code GitHub par daalo

Is folder me ye files honi chahiye (deployment ke liye):

```
api/index.py          <- Flask backend (Vercel Function)
public/index.html     <- main website
public/admin.html     <- developer/moderator panel
requirements.txt      <- flask, upstash-redis
vercel.json           <- function config
.vercelignore         <- local-only files ignore
```

GitHub par naya repo banao aur ye files push kar do (dev_server.py, settings.json,
users.json, uploads/ ki zaroorat nahi — .vercelignore unhe skip kar deta hai).

```bash
git init
git add .
git commit -m "XG Thunder token generator + admin panel"
git branch -M main
git remote add origin https://github.com/<tum>/<repo>.git
git push -u origin main
```

---

## 3. Vercel par import karo

1. https://vercel.com → **Add New → Project** → apna GitHub repo import karo.
2. Framework Preset: **Other** (automatic detect ho jayega).
3. **Environment Variables** me add karo (Production + Preview + Development sab me):
   - `UPSTASH_REDIS_REST_URL`  = (step 1 wali value)
   - `UPSTASH_REDIS_REST_TOKEN` = (step 1 wali value)
   - `XG_SECRET` = koi lamba random string (login session secure karne ke liye)
4. **Deploy** dabao.

Deploy ke baad:

- Website: `https://<project>.vercel.app/`
- Admin panel: `https://<project>.vercel.app/admin`

---

## 4. Login (default)

| Role | Username | Password |
|------|----------|----------|
| Developer | `admin` | `raj11223` |
| Moderator | `smartraj6392@gmail.com` | `raj11223` |

Pehli baar `admin` login karke **Users section** me apna password change kar lo, aur
`XG_SECRET` strong rakho.

> Note: Users/Redis me password **hash** hoke jaate hain (plaintext nahi).

---

## 5. Kaise kaam karta hai

- Website load hote hi `GET /api/settings` se logo + 5 platform links aate hain.
- Panel se link **Update / Publish** karne par `POST /api/admin/settings` → Redis me save
  → website ke buttons turant naye link par redirect karte hain.
- Logo change karne par image browser me chhoti (512px JPEG) hokar base64 me Redis me
  save hoti hai (Vercel ke 4.5MB request limit ke andar).
- Login par signed token milta hai (itsdangerous, `XG_SECRET` se) which expires 8 hours me.

---

## 6. Local develop karna

`dev_server.py` = Python http.server (same APIs, JSON files me data). Sirf local testing
ke liye. Cloud pe always Flask (`api/index.py`) chalta hai.

Flask app locally test karna ho to:

```bash
pip install flask itsdangerous upstash-redis
python api/index.py
# http://localhost:5000 par khulega
```
