from flask import Flask, jsonify, request, render_template, redirect
import json
import os
import sqlite3
import datetime
from functools import wraps

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'royal_agent.db')

# Admin credentials
ADMIN_USER = "royal"
ADMIN_PASS = "chaussures2024"

# ── Load JSON data ─────────────────────────────────────────
def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), encoding='utf-8') as f:
        return json.load(f)

zr_prices = load_json('zr_prices.json')
local_prices = load_json('local_prices.json')
policies_db = load_json('policies.json')

# ── Database setup ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            wilaya TEXT NOT NULL,
            commune TEXT NOT NULL,
            product TEXT NOT NULL,
            size TEXT NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            delivery_type TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ── Basic Auth ─────────────────────────────────────────────
def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return jsonify({'error': 'Authentication required'}), 401, {
        'WWW-Authenticate': 'Basic realm="Royal Agent Tool"'
    }

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            # For browser HTML pages, redirect to login prompt
            if request.accept_mimetypes.best == 'text/html':
                return authenticate()
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# ── Routes: Public ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── API: Wilayas ──────────────────────────────────────────
@app.route('/api/wilayas')
def list_wilayas():
    query = request.args.get('q', '').strip()
    wilayas = sorted(zr_prices.keys())
    if query:
        wilayas = [w for w in wilayas if query in w]
    return jsonify(wilayas)

# ── API: ZR Express price ─────────────────────────────────
@app.route('/api/shipping/zr')
def shipping_zr():
    wilaya = request.args.get('wilaya', '').strip()
    data = zr_prices.get(wilaya)
    if not data:
        return jsonify({'error': 'الولاية غير موجودة'}), 404
    return jsonify({
        'wilaya': wilaya,
        'home': data['home'],
        'office': data['office']
    })

# ── API: Local Tlemcen price ──────────────────────────────
@app.route('/api/shipping/local')
def shipping_local():
    commune = request.args.get('commune', '').strip()
    data = local_prices.get(commune)
    if not data:
        return jsonify({'error': 'البلدية غير موجودة'}), 404
    return jsonify({
        'commune': commune,
        'home': data['home'],
        'office': data['office']
    })

@app.route('/api/communes')
def list_communes():
    return jsonify(sorted(local_prices.keys()))

# ── API: Policies ──────────────────────────────────────────
@app.route('/api/policies')
def list_policies():
    return jsonify(policies_db['policies'])

# ── API: Submit order (Public - for agents) ───────────────
@app.route('/api/orders', methods=['POST'])
def submit_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'بيانات الطلب مطلوبة'}), 400

    required = ['name', 'phone', 'wilaya', 'commune', 'product', 'size', 'color', 'quantity', 'delivery_type']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'الحقول الناقصة: {", ".join(missing)}'}), 400

    conn = get_db()
    cur = conn.execute('''
        INSERT INTO orders (name, phone, wilaya, commune, product, size, color, quantity, delivery_type, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name'], data['phone'], data['wilaya'], data['commune'],
        data['product'], data['size'], data['color'],
        int(data.get('quantity', 1)),
        data['delivery_type'], data.get('note', '')
    ))
    conn.commit()
    order_id = cur.lastrowid
    conn.close()

    return jsonify({'success': True, 'order_id': order_id})

# ── API: Get orders (Admin only) ──────────────────────────
@app.route('/api/orders', methods=['GET'])
@requires_auth
def get_orders():
    conn = get_db()
    search = request.args.get('q', '').strip()
    if search:
        rows = conn.execute('''
            SELECT * FROM orders
            WHERE name LIKE ? OR phone LIKE ? OR wilaya LIKE ? OR product LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()
    else:
        rows = conn.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── API: Get single order ─────────────────────────────────
@app.route('/api/orders/<int:order_id>', methods=['GET'])
@requires_auth
def get_order(order_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'الطلب غير موجود'}), 404
    return jsonify(dict(row))

# ── API: Delete order ────────────────────────────────────
@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
@requires_auth
def delete_order(order_id):
    conn = get_db()
    cur = conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if deleted == 0:
        return jsonify({'error': 'الطلب غير موجود'}), 404
    return jsonify({'success': True, 'deleted': order_id})

# ── API: Daily count ──────────────────────────────────────
# ── API: Today orders ────────────────────────────────────
@app.route('/api/orders/today')
def today_orders():
    conn = get_db()
    today = datetime.date.today().isoformat()
    rows = conn.execute('SELECT * FROM orders WHERE date(created_at) = ? ORDER BY created_at DESC', (today,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders/today-count')
def today_count():
    conn = get_db()
    today = datetime.date.today().isoformat()
    row = conn.execute('SELECT COUNT(*) as cnt FROM orders WHERE date(created_at) = ?', (today,)).fetchone()
    conn.close()
    return jsonify({'count': row['cnt']})

# ── Admin page ────────────────────────────────────────────
@app.route('/admin')
@requires_auth
def admin_page():
    return render_template('admin.html')

# ── Run ───────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
