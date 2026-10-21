import http.server
import urllib.request
import urllib.error
import urllib.parse
import re
import json
import sys
import os
import time
import base64
import hashlib
import hmac
import secrets
import threading
import mimetypes

PORT = 8000

SESSION_API_ACCESS = 'https://ff-eat-token-to-access-token.vercel.app/Eat'
SESSION_API_JWT = 'https://ff-eat-to-jwt-bio-update-m41nul.vercel.app/api/verify-token'
BACKUP_API = 'https://access.killersharmabot.online/access'

M_BASE = 'https://ff-long-bio-update-tools.vercel.app'
M_KEY = 'm41nul-x'
WZ_API = 'https://wzlongsign.vercel.app/updatebio'
MAX_BIO_LEN = 280

# ---------------------------------------------------------------- paths / store
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
LOCK = threading.Lock()

SESSIONS = {}
SESSION_TTL = 8 * 3600

DEFAULT_LOGO = 'https://plain-apac-prod-public.komododecks.com/202609/10/UJcvrE1pPPPV6GGGwVXK/image.jpg'

DEFAULT_PLATFORMS = [
    {
        'id': 'google',
        'name': 'Google',
        'link': 'https://auth.garena.com/universal/oauth?platform=8&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https%3A%2F%2Fapi.ff.garena.co.id%2Fauth%2Fauth%2Fcallback_n%3Fsite%3Dhttps%3A%2F%2Fapi-discountstore.kiosgamer.gameid.garena.co.id%2Foauth%2Fcallback_redirect%2F',
    },
    {
        'id': 'facebook',
        'name': 'Facebook',
        'link': 'https://auth.garena.com/universal/oauth?platform=3&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/',
    },
    {
        'id': 'apple',
        'name': 'Apple',
        'link': 'https://appleid.apple.com/auth/authorize?client_id=com.garena.connect.100067&redirect_uri=https%3A%2F%2Fauth.garena.com%2Foauth%2Flogin%2Fapple&response_mode=form_post&response_type=code+id_token&scope=name+email&state=69507abcacd811f19252da5d42aa8e87-platform%3D10%26response_type%3Dcode%26locale%3Den-SG%26client_id%3D100067%26redirect_uri%3Dhttps%253A%252F%252Fapi.ff.garena.co.id%252Fauth%252Fauth%252Fcallback_n%253Fsite%253Dhttps%253A%252F%252Fapi-discountstore.kiosgamer.gameid.garena.co.id%252Foauth%252Fcallback_redirect%252F%26version%3Duniversal',
    },
    {
        'id': 'x',
        'name': 'X (Twitter)',
        'link': 'https://auth.garena.com/universal/oauth?platform=11&response_type=code&locale=en-SG&client_id=100067&redirect_uri=https://api.ff.garena.co.id/auth/auth/callback_n?site=https://api-discountstore.kiosgamer.gameid.garena.co.id/oauth/callback_redirect/',
    },
    {
        'id': 'vk',
        'name': 'VK',
        'link': 'https://id.vk.ru/auth?app_id=54473168&device_id=&response_type=code&redirect_uri=https%3A%2F%2Fauth.garena.com%2Funiversal%2Foauth%2Fvk%3Fplatform%3D5%26response_type%3Dcode%26locale%3Den-SG%26client_id%3D100067%26redirect_uri%3Dhttps%3A%2F%2Fapi.ff.garena.co.id%2Fauth%2Fauth%2Fcallback_n%3Fsite%3Dhttps%3A%2F%2Fapi-discountstore.kiosgamer.gameid.garena.co.id%2Foauth%2Fcallback_redirect%2F%26vk_client_id%3D54473168&scope=vkid.personal_info&lang_id=3&scheme=&oauth_version=2&redirect_state=90205a783d264098868d63bc27f17a0e&code_challenge=QW2VNpTbLmnW9ZACal5hCvbmCieS9eiBLFJdLw6Kbb8&code_challenge_method=sha256',
    },
]


def hash_pw(pw):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt.encode('utf-8'), 120000).hex()
    return salt + '$' + h


def verify_pw(pw, stored):
    try:
        salt, h = str(stored).split('$', 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt.encode('utf-8'), 120000).hex()
    return hmac.compare_digest(calc, h)


def _default_users():
    return {
        'admin': {
            'password': hash_pw('raj11223'),
            'role': 'developer',
            'email': '',
        },
        'smartraj6392@gmail.com': {
            'password': hash_pw('raj11223'),
            'role': 'moderator',
            'email': 'smartraj6392@gmail.com',
        },
    }


def _load_json(path, default):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _init_store():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        _save_json(SETTINGS_FILE, {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS, 'maintenance': False, 'maintenance_until': 0})
    if not os.path.exists(USERS_FILE):
        _save_json(USERS_FILE, _default_users())


def create_session(username, role):
    token = secrets.token_hex(24)
    SESSIONS[token] = {'username': username, 'role': role, 'exp': time.time() + SESSION_TTL}
    return token


def get_session(handler):
    auth = handler.headers.get('Authorization', '') or ''
    if auth.lower().startswith('bearer '):
        token = auth[7:].strip()
    else:
        token = (handler.headers.get('X-Auth-Token', '') or '').strip()
    if not token:
        return None
    sess = SESSIONS.get(token)
    if not sess:
        return None
    if sess['exp'] < time.time():
        SESSIONS.pop(token, None)
        return None
    sess['token'] = token
    return sess


class Handler(http.server.BaseHTTPRequestHandler):

    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Auth-Token')
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        try:
            length = int(self.headers.get('Content-Length') or 0)
        except (TypeError, ValueError):
            length = 0
        raw = self.rfile.read(length).decode('utf-8', 'replace') if length else '{}'
        try:
            data = json.loads(raw or '{}')
        except Exception:
            data = {}
        return data if isinstance(data, dict) else {}

    def _require_auth(self, role=None):
        sess = get_session(self)
        if not sess:
            self._send(401, {'success': False, 'error': 'Unauthorized. Please login again.'})
            return None
        if role and sess['role'] != role:
            self._send(403, {'success': False, 'error': 'Forbidden. Developer access required.'})
            return None
        return sess

    def do_OPTIONS(self):
        self._send(200, b'')

    def do_GET(self):
        path = urllib.parse.urlparse(self.path)

        if path.path in ('/', '/index.html'):
            self._serve_file('index.html', 'text/html; charset=utf-8')
            return

        if path.path in ('/admin', '/admin/', '/admin.html'):
            self._serve_file('admin.html', 'text/html; charset=utf-8')
            return

        if path.path.startswith('/uploads/'):
            self._serve_upload(path.path[len('/uploads/'):])
            return

        _ext = os.path.splitext(path.path)[1].lower()
        if _ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf'):
            self._serve_file(os.path.basename(path.path), mimetypes.guess_type(path.path)[0] or 'application/octet-stream')
            return

        if path.path == '/api/settings':
            with LOCK:
                s = _load_json(SETTINGS_FILE, {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS})
            self._send(200, {
                'logo': s.get('logo') or DEFAULT_LOGO,
                'platforms': s.get('platforms') or DEFAULT_PLATFORMS,
                'maintenance': bool(s.get('maintenance')),
                'maintenance_until': s.get('maintenance_until') or 0,
            })
            return

        if path.path == '/api/admin/data':
            self._admin_data()
            return

        if path.path == '/api/convert':
            qs = urllib.parse.parse_qs(path.query)
            eat = (qs.get('eat') or qs.get('eat_token') or [''])[0].strip()
            if not eat:
                self._send(400, {'error': 'eat token required'})
                return

            result = self._fetch_all(eat)
            self._send(200, result)
            return

        if path.path == '/api/update-bio':
            qs = urllib.parse.parse_qs(path.query)
            token = (qs.get('token') or qs.get('access_token') or qs.get('eat_token') or [''])[0].strip()
            bio = qs.get('bio', [''])[0].strip()
            region = qs.get('region', [''])[0].strip()
            result = self._update_bio(token, bio, region)
            self._send(result['code'], result['body'])
            return

        self._send(404, {'error': 'not found'})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path)
        routes = {
            '/api/login': self._login,
            '/api/logout': self._logout,
            '/api/admin/settings': self._save_settings,
            '/api/admin/logo': self._upload_logo,
            '/api/admin/users': self._save_user,
        }
        if path.path in routes:
            routes[path.path]()
            return

        if path.path == '/api/update-bio':
            body = self._read_json_body()
            token = str(body.get('token') or '').strip()
            bio = str(body.get('bio') or '').strip()
            region = str(body.get('region') or '').strip()
            result = self._update_bio(token, bio, region)
            self._send(result['code'], result['body'])
            return

        self._send(404, {'error': 'not found'})

    # ------------------------------------------------------------- admin auth/API
    def _login(self):
        body = self._read_json_body()
        ident = str(body.get('username') or '').strip()
        email = str(body.get('email') or '').strip()
        pw = str(body.get('password') or '')

        if not ident and not email:
            self._send(400, {'success': False, 'error': 'Username ya email daalo'})
            return
        if not pw:
            self._send(400, {'success': False, 'error': 'Password daalo'})
            return

        with LOCK:
            users = _load_json(USERS_FILE, {})
        key = None
        # 1) username (exact pehle, phir case-insensitive)
        if ident:
            for uname in users:
                if ident == uname:
                    key = uname
                    break
            if key is None:
                for uname in users:
                    if ident.lower() == uname.lower():
                        key = uname
                        break
        # 2) email fallback
        if key is None:
            probe = (email or ident).lower()
            if probe:
                for uname, u in users.items():
                    if probe == str(u.get('email', '')).lower():
                        key = uname
                        break

        if key is None or not verify_pw(pw, users[key].get('password', '')):
            self._send(200, {'success': False, 'error': 'Galat username/email ya password'})
            return

        u = users[key]
        token = create_session(key, u.get('role', 'moderator'))
        self._send(200, {
            'success': True,
            'token': token,
            'username': key,
            'role': u.get('role', 'moderator'),
            'email': u.get('email', ''),
        })

    def _logout(self):
        sess = get_session(self)
        if sess:
            SESSIONS.pop(sess['token'], None)
        self._send(200, {'success': True})

    def _admin_data(self):
        sess = self._require_auth()
        if not sess:
            return
        with LOCK:
            settings = _load_json(SETTINGS_FILE, {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS})
            users = _load_json(USERS_FILE, {})
        me = users.get(sess['username'], {})
        payload = {
            'success': True,
            'settings': {
                'logo': settings.get('logo') or DEFAULT_LOGO,
                'platforms': settings.get('platforms') or DEFAULT_PLATFORMS,
                'maintenance': bool(settings.get('maintenance')),
                'maintenance_until': settings.get('maintenance_until') or 0,
            },
            'me': {
                'username': sess['username'],
                'role': sess['role'],
                'email': me.get('email', ''),
            },
        }
        if sess['role'] == 'developer':
            payload['users'] = [
                {'username': k, 'email': v.get('email', ''), 'role': v.get('role', '')}
                for k, v in users.items()
            ]
        self._send(200, payload)

    def _save_settings(self):
        sess = self._require_auth()
        if not sess:
            return
        body = self._read_json_body()
        with LOCK:
            s = _load_json(SETTINGS_FILE, {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS})
            if body.get('logo') is not None:
                s['logo'] = str(body.get('logo')).strip()
            if body.get('maintenance') is not None:
                s['maintenance'] = bool(body.get('maintenance'))
            if body.get('maintenance_until') is not None:
                try:
                    s['maintenance_until'] = int(body.get('maintenance_until') or 0)
                except (TypeError, ValueError):
                    s['maintenance_until'] = 0
            if isinstance(body.get('platforms'), list):
                new = []
                for p in body['platforms']:
                    if not isinstance(p, dict):
                        continue
                    pid = str(p.get('id') or '').strip()
                    if not pid:
                        continue
                    new.append({
                        'id': pid,
                        'name': str(p.get('name') or '').strip(),
                        'link': str(p.get('link') or '').strip(),
                    })
                if new:
                    s['platforms'] = new
            _save_json(SETTINGS_FILE, s)
        self._send(200, {'success': True, 'settings': s})

    def _upload_logo(self):
        sess = self._require_auth()
        if not sess:
            return
        body = self._read_json_body()
        data_url = str(body.get('dataUrl') or '')
        m = re.match(r'^data:(image/(png|jpe?g|webp|gif));base64,(.+)$', data_url, re.I | re.S)
        if not m:
            self._send(400, {'success': False, 'error': 'Invalid image data'})
            return
        ext = {'png': 'png', 'jpg': 'jpg', 'jpeg': 'jpg', 'webp': 'webp', 'gif': 'gif'}[m.group(2).lower()]
        try:
            raw = base64.b64decode(m.group(3))
        except Exception:
            self._send(400, {'success': False, 'error': 'Invalid image data'})
            return
        if len(raw) > 4 * 1024 * 1024:
            self._send(400, {'success': False, 'error': 'Image too large (max 4MB)'})
            return
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        fname = 'logo_' + str(int(time.time())) + '.' + ext
        with open(os.path.join(UPLOADS_DIR, fname), 'wb') as f:
            f.write(raw)
        url = '/uploads/' + fname
        with LOCK:
            s = _load_json(SETTINGS_FILE, {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS})
            s['logo'] = url
            _save_json(SETTINGS_FILE, s)
        self._send(200, {'success': True, 'logo': url})

    def _save_user(self):
        sess = self._require_auth(role='developer')
        if not sess:
            return
        body = self._read_json_body()
        uname = str(body.get('username') or '').strip()
        orig = str(body.get('original_username') or uname).strip()
        email = str(body.get('email') or '').strip()
        role = str(body.get('role') or 'moderator').strip()
        pw = str(body.get('password') or '')

        if not uname:
            self._send(400, {'success': False, 'error': 'Username required'})
            return
        if role not in ('developer', 'moderator'):
            role = 'moderator'
        if ' ' in uname:
            self._send(400, {'success': False, 'error': 'Username me space nahi hona chahiye'})
            return

        with LOCK:
            users = _load_json(USERS_FILE, {})
            existing = users.get(orig, {})
            if not existing and not pw:
                self._send(400, {'success': False, 'error': 'Naye user ke liye password zaroori hai'})
                return
            if orig != uname and uname in users:
                self._send(400, {'success': False, 'error': 'Ye username already exists'})
                return
            rec = {
                'role': role,
                'email': email or existing.get('email', ''),
                'password': hash_pw(pw) if pw else existing.get('password', ''),
            }
            if orig != uname and orig in users:
                del users[orig]
            users[uname] = rec
            _save_json(USERS_FILE, users)
        self._send(200, {'success': True})

    # ------------------------------------------------------------------- helpers
    def _serve_file(self, name, ctype):
        fp = os.path.join(BASE_DIR, 'public', name)
        if not os.path.isfile(fp):
            fp = os.path.join(BASE_DIR, name)
        try:
            with open(fp, 'rb') as f:
                self._send(200, f.read(), ctype)
        except FileNotFoundError:
            self._send(404, b'file not found')

    def _serve_upload(self, name):
        name = os.path.basename(name)
        fp = os.path.join(UPLOADS_DIR, name)
        if name and os.path.isfile(fp):
            ctype = mimetypes.guess_type(fp)[0] or 'application/octet-stream'
            with open(fp, 'rb') as f:
                self._send(200, f.read(), ctype)
        else:
            self._send(404, b'not found')

    def _fetch_url(self, url, timeout=15):
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
        req.add_header('Accept', 'application/json')
        resp = urllib.request.urlopen(req, timeout=timeout)
        return resp.read().decode()

    def _fetch_all(self, eat):
        out = {'eat': eat, 'access_token': None, 'jwt_token': None,
               'nickname': None, 'region': None, 'account_id': None,
               'headPic': None, 'bannerId': None, 'level': None,
               'avatar_url': None, 'banner_url': None, 'banner_bg': None,
               'errors': {}}

        enc = urllib.parse.quote(eat)

        # --- Access token via session API ---
        try:
            data = json.loads(self._fetch_url(f'{SESSION_API_ACCESS}?eat_token={enc}'))
            if isinstance(data, dict):
                if data.get('access_token'):
                    out['access_token'] = data['access_token']
                    out['nickname'] = data.get('account_nickname') or out['nickname']
                    out['region'] = data.get('region') or out['region']
                    out['account_id'] = data.get('account_id') or out['account_id']
                elif data.get('error'):
                    out['errors']['access'] = data['error']
        except Exception as e:
            out['errors']['access'] = str(e)

        # --- JWT via session API ---
        try:
            data = json.loads(self._fetch_url(f'{SESSION_API_JWT}?eat_token={enc}'))
            if isinstance(data, dict):
                if data.get('jwt_token'):
                    out['jwt_token'] = data['jwt_token']
                    acc = data.get('account') or {}
                    out['nickname'] = acc.get('nickname') or out['nickname']
                    out['region'] = acc.get('region') or out['region']
                    out['account_id'] = acc.get('uid') or out['account_id']
                elif data.get('error'):
                    out['errors']['jwt'] = data['error']
        except Exception as e:
            out['errors']['jwt'] = str(e)

        # --- Backup API (rich data: headPic, bannerId, level) ---
        try:
            data = json.loads(self._fetch_url(f'{BACKUP_API}?access_token={enc}'))
            if isinstance(data, dict):
                if data.get('access_token') and not out['access_token']:
                    out['access_token'] = data['access_token']
                out['nickname'] = data.get('nickname') or out['nickname']
                out['region'] = data.get('lockRegion') or data.get('noti_region') or data.get('region') or out['region']
                out['account_id'] = str(data.get('accountId') or data.get('account_id') or out['account_id'] or '')
                if data.get('token'):
                    out['jwt_token'] = data['token']
                # Photo-related fields
                head_pic = data.get('headPic') or data.get('headpic')
                banner_id = data.get('bannerId') or data.get('banner_id')
                level = data.get('level')
                if head_pic:
                    out['headPic'] = head_pic
                    out['avatar_url'] = f'https://ffitems.devhubx.org/items/{head_pic}'
                if banner_id:
                    out['bannerId'] = banner_id
                    out['banner_bg'] = f'https://ffitems.devhubx.org/items/{banner_id}'
                if level is not None:
                    out['level'] = level
                if head_pic and banner_id and out.get('nickname') and level is not None:
                    out['banner_url'] = (
                        'https://image.killersharmabot.online/banner-image?headPic=' +
                        str(head_pic) + '&bannerId=' + str(banner_id) +
                        '&name=' + urllib.parse.quote(str(out['nickname'])) +
                        '&level=' + str(level)
                    )
                if data.get('error') and 'access' not in out['errors']:
                    out['errors']['backup'] = data['error']
        except Exception as e:
            out['errors']['backup'] = str(e)

        if not out['access_token'] and not out['jwt_token'] and out['errors']:
            out['error'] = '; '.join(out['errors'].values())
        return out

    def log_message(self, *args):
        pass

    def _update_bio(self, token, bio, region=''):
        if not token or not bio:
            return {'code': 400, 'body': {'success': False, 'error': 'token and bio required'}}
        if len(bio) > MAX_BIO_LEN:
            return {'code': 400, 'body': {'success': False, 'error': f'Bio cannot exceed {MAX_BIO_LEN} characters'}}

        m = re.search(r'[?&]eat=([^&]+)', token) if isinstance(token, str) else None
        if m:
            raw = urllib.parse.unquote(m.group(1))
            is_url_eat = True
        else:
            raw = token.strip()
            is_url_eat = False

        if not raw:
            return {'code': 400, 'body': {'success': False, 'error': 'Could not extract token'}}

        enc = urllib.parse.quote(raw)
        enc_bio = urllib.parse.quote(bio)
        enc_region = urllib.parse.quote(region or '')

        def json_url(url):
            try:
                return json.loads(self._fetch_url(url, timeout=25))
            except urllib.error.HTTPError as e:
                try:
                    return json.loads(e.read().decode('utf-8', 'replace'))
                except Exception:
                    return {}
            except Exception:
                return {}

        if is_url_eat:
            calls = [
                f'{M_BASE}/api/eat-to-bio?eat_token={enc}&bio={enc_bio}&key={M_KEY}',
                f'{WZ_API}?token={enc}&bio={enc_bio}&region={enc_region}',
            ]
        elif raw.startswith('eyJ'):
            calls = [
                f'{WZ_API}?token={enc}&bio={enc_bio}&region={enc_region}',
                f'{M_BASE}/api/bio?access_token={enc}&bio={enc_bio}&key={M_KEY}',
                f'{M_BASE}/api/eat-to-bio?eat_token={enc}&bio={enc_bio}&key={M_KEY}',
            ]
        else:
            calls = [
                f'{M_BASE}/api/bio?access_token={enc}&bio={enc_bio}&key={M_KEY}',
                f'{WZ_API}?token={enc}&bio={enc_bio}&region={enc_region}',
                f'{M_BASE}/api/eat-to-bio?eat_token={enc}&bio={enc_bio}&key={M_KEY}',
            ]

        last_msg = 'Bio update failed'
        last_code = 0
        for url in calls:
            data = json_url(url)
            if self._bio_success(data):
                return {'code': 200, 'body': self._norm_bio_resp(data)}
            msg = data.get('message') or data.get('error') or data.get('server_response')
            if not msg and data.get('status_code'):
                msg = f'service status {data["status_code"]}'
            if msg and last_msg == 'Bio update failed':
                last_msg = str(msg).strip()
            if data.get('status_code'):
                last_code = data.get('status_code')

        return {'code': 200, 'body': {'success': False, 'error': last_msg, 'code': last_code}}

    def _bio_success(self, data):
        if not isinstance(data, dict):
            return False
        if data.get('success') is True:
            return True
        if str(data.get('status', '')).lower() in ('success', 'ok', 'true'):
            return True
        return False

    def _norm_bio_resp(self, r):
        br = r.get('bio_update') or {}
        return {
            'success': True,
            'nickname': r.get('account_nickname') or r.get('nickname') or br.get('nickname') or '',
            'uid': str(r.get('account_id') or r.get('uid') or br.get('uid') or ''),
            'region': r.get('region') or br.get('region') or '',
            'platform': r.get('platform') or br.get('platform') or ''
        }

if __name__ == '__main__':
    _init_store()
    print('XG Thunder server chal raha hai: http://localhost:' + str(PORT))
    print('Developer panel: http://localhost:' + str(PORT) + '/admin')
    print('Band karne ke liye Ctrl+C dabao.')
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer band ho gaya.')
