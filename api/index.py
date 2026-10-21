import os
import re
import json
import time
import hashlib
import hmac
import secrets
import urllib.request
import urllib.error
import urllib.parse

from flask import Flask, request, jsonify, redirect, send_from_directory, abort
from itsdangerous import URLSafeTimedSerializer

try:
    from upstash_redis import Redis
except Exception:  # pragma: no cover
    Redis = None

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    app.json.ensure_ascii = False
except Exception:
    pass

# ------------------------------------------------------------------ config
REDIS_URL = (
    os.environ.get('UPSTASH_REDIS_REST_URL')
    or os.environ.get('KV_REST_API_URL')
    or os.environ.get('REDIS_REST_URL')
)
REDIS_TOKEN = (
    os.environ.get('UPSTASH_REDIS_REST_TOKEN')
    or os.environ.get('KV_REST_API_TOKEN')
    or os.environ.get('REDIS_REST_TOKEN')
)
SECRET = os.environ.get('XG_SECRET') or 'xg-thunder-set-XG_SECRET-env'
SESSION_TTL = 8 * 3600

redis = Redis(url=REDIS_URL, token=REDIS_TOKEN) if (Redis and REDIS_URL and REDIS_TOKEN) else None

SESSION_API_ACCESS = 'https://ff-eat-token-to-access-token.vercel.app/Eat'
SESSION_API_JWT = 'https://ff-eat-to-jwt-bio-update-m41nul.vercel.app/api/verify-token'
BACKUP_API = 'https://access.killersharmabot.online/access'

M_BASE = 'https://ff-long-bio-update-tools.vercel.app'
M_KEY = 'm41nul-x'
WZ_API = 'https://wzlongsign.vercel.app/updatebio'
MAX_BIO_LEN = 280

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

SETTINGS_KEY = 'xg:settings'
USERS_KEY = 'xg:users'


# ------------------------------------------------------------------ storage
def _rget(key, default=None):
    if not redis:
        return default
    try:
        v = redis.get(key)
        if v is None:
            return default
        if isinstance(v, (dict, list)):
            return v
        if isinstance(v, bytes):
            v = v.decode('utf-8', 'replace')
        return json.loads(v)
    except Exception:
        return default


def _rset(key, value):
    if not redis:
        return
    redis.set(key, json.dumps(value))


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


def get_settings():
    s = _rget(SETTINGS_KEY)
    if not isinstance(s, dict) or not s.get('platforms'):
        s = {'logo': DEFAULT_LOGO, 'platforms': DEFAULT_PLATFORMS, 'maintenance': False, 'maintenance_until': 0}
        _rset(SETTINGS_KEY, s)
    return s


def get_users():
    u = _rget(USERS_KEY)
    if not isinstance(u, dict) or not u:
        u = _default_users()
        _rset(USERS_KEY, u)
    return u


# ------------------------------------------------------------------ auth
signer = URLSafeTimedSerializer(SECRET, salt='xg-admin-v1')


def make_token(username, role):
    return signer.dumps({'u': username, 'r': role})


def read_session():
    auth = request.headers.get('Authorization', '') or ''
    if auth.lower().startswith('bearer '):
        token = auth[7:].strip()
    else:
        token = (request.headers.get('X-Auth-Token', '') or '').strip()
    if not token:
        return None
    try:
        data = signer.loads(token, max_age=SESSION_TTL)
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get('u'):
        return None
    return data


def require_auth(role=None):
    sess = read_session()
    if not sess:
        return None, (jsonify(success=False, error='Unauthorized. Please login again.'), 401)
    if role and sess.get('r') != role:
        return None, (jsonify(success=False, error='Forbidden. Developer access required.'), 403)
    return sess, None


@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Auth-Token'
    return resp


# ------------------------------------------------------------------ pages
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')


@app.route('/')
def home():
    return send_from_directory(PUBLIC_DIR, 'index.html')


@app.route('/admin')
@app.route('/admin/')
def admin_page():
    return send_from_directory(PUBLIC_DIR, 'admin.html')


@app.route('/<path:filename>')
def static_files(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf', '.html'):
        abort(404)
    safe = os.path.basename(filename)
    for base in (os.path.join(BASE_DIR, 'public'), BASE_DIR):
        fp = os.path.join(base, safe)
        if os.path.isfile(fp):
            return send_from_directory(base, safe)
    abort(404)


@app.route('/api/health')
def health():
    return jsonify(ok=True, storage='redis' if redis else 'none')


# ------------------------------------------------------------------ public settings
@app.route('/api/settings')
def api_settings():
    s = get_settings()
    return jsonify(logo=s.get('logo') or DEFAULT_LOGO, platforms=s.get('platforms') or DEFAULT_PLATFORMS, maintenance=bool(s.get('maintenance')), maintenance_until=s.get('maintenance_until') or 0)


# ------------------------------------------------------------------ login / logout
@app.route('/api/login', methods=['POST'])
def api_login():
    body = request.get_json(silent=True) or {}
    ident = str(body.get('username') or '').strip()
    email = str(body.get('email') or '').strip()
    pw = str(body.get('password') or '')

    if not ident and not email:
        return jsonify(success=False, error='Username ya email daalo'), 400
    if not pw:
        return jsonify(success=False, error='Password daalo'), 400

    users = get_users()
    key = None
    if ident:
        if ident in users:
            key = ident
        else:
            for uname in users:
                if ident.lower() == uname.lower():
                    key = uname
                    break
    if key is None:
        probe = (email or ident).lower()
        if probe:
            for uname, u in users.items():
                if probe == str(u.get('email', '')).lower():
                    key = uname
                    break

    if key is None or not verify_pw(pw, users[key].get('password', '')):
        return jsonify(success=False, error='Galat username/email ya password')

    u = users[key]
    role = u.get('role', 'moderator')
    return jsonify(success=True, token=make_token(key, role), username=key, role=role, email=u.get('email', ''))


@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify(success=True)


# ------------------------------------------------------------------ admin data
@app.route('/api/admin/data')
def api_admin_data():
    sess, err = require_auth()
    if err:
        return err
    settings = get_settings()
    users = get_users()
    me = users.get(sess['u'], {})
    payload = {
        'success': True,
        'settings': {
            'logo': settings.get('logo') or DEFAULT_LOGO,
            'platforms': settings.get('platforms') or DEFAULT_PLATFORMS,
            'maintenance': bool(settings.get('maintenance')),
            'maintenance_until': settings.get('maintenance_until') or 0,
        },
        'me': {'username': sess['u'], 'role': sess.get('r'), 'email': me.get('email', '')},
    }
    if sess.get('r') == 'developer':
        payload['users'] = [
            {'username': k, 'email': v.get('email', ''), 'role': v.get('role', '')}
            for k, v in users.items()
        ]
    return jsonify(payload)


@app.route('/api/admin/settings', methods=['POST'])
def api_save_settings():
    sess, err = require_auth()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    s = get_settings()
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
    _rset(SETTINGS_KEY, s)
    return jsonify(success=True, settings=s)


@app.route('/api/admin/logo', methods=['POST'])
def api_upload_logo():
    sess, err = require_auth()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    data_url = str(body.get('dataUrl') or '')
    m = re.match(r'^data:(image/(png|jpe?g|webp|gif));base64,(.+)$', data_url, re.I | re.S)
    if not m:
        return jsonify(success=False, error='Invalid image data'), 400
    if len(data_url) > 900000:
        return jsonify(success=False, error='Image too large. Chhoti image use karo (max ~650KB).'), 400
    s = get_settings()
    s['logo'] = data_url
    _rset(SETTINGS_KEY, s)
    return jsonify(success=True, logo=data_url)


@app.route('/api/admin/users', methods=['POST'])
def api_save_user():
    sess, err = require_auth(role='developer')
    if err:
        return err
    body = request.get_json(silent=True) or {}
    uname = str(body.get('username') or '').strip()
    orig = str(body.get('original_username') or uname).strip()
    email = str(body.get('email') or '').strip()
    role = str(body.get('role') or 'moderator').strip()
    pw = str(body.get('password') or '')

    if not uname:
        return jsonify(success=False, error='Username required'), 400
    if role not in ('developer', 'moderator'):
        role = 'moderator'
    if ' ' in uname:
        return jsonify(success=False, error='Username me space nahi hona chahiye'), 400

    users = get_users()
    existing = users.get(orig, {})
    if not existing and not pw:
        return jsonify(success=False, error='Naye user ke liye password zaroori hai'), 400
    if orig != uname and uname in users:
        return jsonify(success=False, error='Ye username already exists'), 400

    users[uname] = {
        'role': role,
        'email': email or existing.get('email', ''),
        'password': hash_pw(pw) if pw else existing.get('password', ''),
    }
    if orig != uname and orig in users:
        del users[orig]
    _rset(USERS_KEY, users)
    return jsonify(success=True)


# ------------------------------------------------------------------ token convert
def _fetch_url(url, timeout=15):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
    req.add_header('Accept', 'application/json')
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode()


def _fetch_all(eat):
    out = {'eat': eat, 'access_token': None, 'jwt_token': None,
           'nickname': None, 'region': None, 'account_id': None,
           'headPic': None, 'bannerId': None, 'level': None,
           'avatar_url': None, 'banner_url': None, 'banner_bg': None,
           'errors': {}}

    enc = urllib.parse.quote(eat)

    try:
        data = json.loads(_fetch_url(f'{SESSION_API_ACCESS}?eat_token={enc}'))
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

    try:
        data = json.loads(_fetch_url(f'{SESSION_API_JWT}?eat_token={enc}'))
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

    try:
        data = json.loads(_fetch_url(f'{BACKUP_API}?access_token={enc}'))
        if isinstance(data, dict):
            if data.get('access_token') and not out['access_token']:
                out['access_token'] = data['access_token']
            out['nickname'] = data.get('nickname') or out['nickname']
            out['region'] = data.get('lockRegion') or data.get('noti_region') or data.get('region') or out['region']
            out['account_id'] = str(data.get('accountId') or data.get('account_id') or out['account_id'] or '')
            if data.get('token'):
                out['jwt_token'] = data['token']
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


@app.route('/api/convert')
def api_convert():
    eat = (request.args.get('eat') or request.args.get('eat_token') or '').strip()
    if not eat:
        return jsonify(error='eat token required'), 400
    return jsonify(_fetch_all(eat))


# ------------------------------------------------------------------ bio update
def _norm_bio_resp(r):
    br = r.get('bio_update') or {}
    return {
        'success': True,
        'nickname': r.get('account_nickname') or br.get('nickname') or '',
        'uid': str(r.get('account_id') or br.get('uid') or ''),
        'region': r.get('region') or br.get('region') or '',
        'platform': br.get('platform') or '',
    }


def _update_bio(token, bio, region=''):
    if not token or not bio:
        return 400, {'success': False, 'error': 'token and bio required'}
    if len(bio) > MAX_BIO_LEN:
        return 400, {'success': False, 'error': f'Bio cannot exceed {MAX_BIO_LEN} characters'}

    m = re.search(r'[?&]eat=([^&]+)', token) if isinstance(token, str) else None
    if m:
        raw = urllib.parse.unquote(m.group(1))
        is_url_eat = True
    else:
        raw = token.strip()
        is_url_eat = False

    if not raw:
        return 400, {'success': False, 'error': 'Could not extract token'}

    enc = urllib.parse.quote(raw)
    enc_bio = urllib.parse.quote(bio)

    def json_url(url):
        try:
            return json.loads(_fetch_url(url, timeout=25))
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode('utf-8', 'replace'))
            except Exception:
                return {}
        except Exception:
            return {}

    data = {}
    if is_url_eat:
        data = json_url(f'{M_BASE}/api/eat-to-bio?eat_token={enc}&bio={enc_bio}&key={M_KEY}')
        if data.get('status') == 'success':
            return 200, _norm_bio_resp(data)
    elif raw.startswith('eyJ'):
        data = json_url(f'{WZ_API}?token={enc}&bio={enc_bio}&region={urllib.parse.quote(region)}')
        if data.get('success'):
            return 200, {'success': True, 'nickname': data.get('nickname') or '', 'uid': str(data.get('uid') or ''), 'region': region}
    else:
        data = json_url(f'{M_BASE}/api/bio?access_token={enc}&bio={enc_bio}&key={M_KEY}')
        if data.get('status') == 'success':
            return 200, _norm_bio_resp(data)
        data = json_url(f'{M_BASE}/api/eat-to-bio?eat_token={enc}&bio={enc_bio}&key={M_KEY}')
        if data.get('status') == 'success':
            return 200, _norm_bio_resp(data)

    msg = data.get('message') or data.get('error') or 'Bio update failed'
    return 200, {'success': False, 'error': msg, 'code': data.get('status_code') or 0}


@app.route('/api/update-bio', methods=['GET', 'POST'])
def api_update_bio():
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        token = str(body.get('token') or '').strip()
        bio = str(body.get('bio') or '').strip()
        region = str(body.get('region') or '').strip()
    else:
        token = (request.args.get('token') or request.args.get('access_token') or request.args.get('eat_token') or '').strip()
        bio = (request.args.get('bio') or '').strip()
        region = (request.args.get('region') or '').strip()
    code, body = _update_bio(token, bio, region)
    return jsonify(body), code


# Local dev entrypoint (Vercel uses `app` automatically)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=True)
