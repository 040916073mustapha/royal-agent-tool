from flask import Flask, jsonify, request, render_template
import json
import os

app = Flask(__name__)

# ── Load data ──────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), encoding='utf-8') as f:
        return json.load(f)

zr_prices = load_json('zr_prices.json')
local_prices = load_json('local_prices.json')
policies_db = load_json('policies.json')

# ── Routes ─────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

# ── API: Search wilayas (autocomplete) ────────────────────
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

# ── API: Local communes list ──────────────────────────────
@app.route('/api/communes')
def list_communes():
    return jsonify(sorted(local_prices.keys()))

# ── API: Quick replies ────────────────────────────────────
@app.route('/api/policies')
def list_policies():
    return jsonify(policies_db['policies'])

# ── API: Submit order ─────────────────────────────────────
orders_store = []  # in-memory for MVP; upgrade to SQLite later

@app.route('/api/orders', methods=['POST'])
def submit_order():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'بيانات الطلب مطلوبة'}), 400

    required = ['name', 'phone', 'wilaya', 'commune', 'product', 'size', 'color', 'quantity', 'delivery_type']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'الحقول الناقصة: {", ".join(missing)}'}), 400

    order = {
        'id': len(orders_store) + 1,
        'name': data['name'],
        'phone': data['phone'],
        'wilaya': data['wilaya'],
        'commune': data['commune'],
        'product': data['product'],
        'size': data['size'],
        'color': data['color'],
        'quantity': int(data.get('quantity', 1)),
        'delivery_type': data['delivery_type'],
        'note': data.get('note', ''),
        'timestamp': None  # no time import for simplicity
    }
    orders_store.append(order)
    return jsonify({'success': True, 'order_id': order['id'], 'order': order})

# ── API: Get all orders (for admin later) ─────────────────
@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(list(reversed(orders_store)))

# ── Run ───────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
