import os
import json
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-session-key")

# Configuration (Set these in Render Environment Variables)
ADMIN_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "AewAdmin@2026")
API_SECRET_TOKEN = os.environ.get("SYNC_API_TOKEN", "aew-sync-token-998877")

DATA_FILE = "dashboard_data.json"

def get_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# 1. Endpoint for your Local Desktop ERP to push data
@app.route("/api/sync", methods=["POST"])
def sync_dashboard():
    auth_header = request.headers.get("X-API-KEY")
    if auth_header != API_SECRET_TOKEN:
        return jsonify({"status": "unauthorized"}), 401
    
    payload = request.get_json()
    if not payload:
        return jsonify({"status": "bad request"}), 400
    
    save_data(payload)
    return jsonify({"status": "success", "message": "Dashboard updated successfully"}), 200

# 2. Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid password. Please try again."
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEW ERP - Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center" style="height: 100vh;">
        <div class="container" style="max-width: 380px;">
            <div class="card shadow-sm p-4">
                <h4 class="text-center mb-3">AEW ERP Portal</h4>
                {% if error %}<div class="alert alert-danger py-2">{{ error }}</div>{% endif %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Access Password</label>
                        <input type="password" name="password" class="form-control" placeholder="Enter password" required autofocus>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Sign In</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# 3. Web Dashboard mirroring your Desktop ERP UI
@app.route("/")
@login_required
def dashboard():
    data = get_data()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEW ERP - Executive Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f3f6f9; font-size: 0.9rem; }
            .kpi-card { border-radius: 6px; border: 1px solid #dee2e6; background: #fff; padding: 14px; }
            .kpi-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
            .kpi-value { font-size: 1.4rem; font-weight: bold; margin-bottom: 2px; }
            .table-sm th, .table-sm td { padding: 6px 10px; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark px-3 mb-3">
            <span class="navbar-brand mb-0 h6">ADARSH ENGINEERING WORKS - Executive Operations & Tax Dashboard</span>
            <div>
                <span class="text-light me-3">Synced: {{ data.get('last_synced', 'Never') }}</span>
                <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
            </div>
        </nav>

        <div class="container-fluid px-4">
            <!-- Summary KPI Cards -->
            <div class="row g-3 mb-3">
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-primary">
                        <div class="kpi-title text-primary">This Month Turnover</div>
                        <div class="kpi-value">₹ {{ data.get('turnover', '0.00') }}</div>
                        <small class="text-muted">{{ data.get('period', 'Active Period') }}</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-secondary">
                        <div class="kpi-title text-secondary">Period Billed</div>
                        <div class="kpi-value">₹ {{ data.get('period_billed', '0.00') }}</div>
                        <small class="text-muted">Current Month Total</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-success">
                        <div class="kpi-title text-success">Collected Cash/Bank</div>
                        <div class="kpi-value">₹ {{ data.get('collected_cash', '0.00') }}</div>
                        <small class="text-muted">Recovery: {{ data.get('recovery_rate', '0%') }}</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-danger">
                        <div class="kpi-title text-danger">AR Outstanding</div>
                        <div class="kpi-value">₹ {{ data.get('ar_outstanding', '0.00') }}</div>
                        <small class="text-muted">Pending Collections</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-info">
                        <div class="kpi-title text-info">Net GST Liability</div>
                        <div class="kpi-value">₹ {{ data.get('net_gst', '0.00') }}</div>
                        <small class="text-muted">Out: ₹{{ data.get('output_gst', '0') }} | ITC: ₹{{ data.get('itc_gst', '0') }}</small>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="kpi-card border-start border-4 border-warning">
                        <div class="kpi-title text-warning">Open Challans</div>
                        <div class="kpi-value">{{ data.get('open_challans_count', '0') }} Open</div>
                        <small class="text-muted">Dispatched Not Invoiced</small>
                    </div>
                </div>
            </div>

            <!-- Invoices Table & Summary -->
            <div class="row g-3">
                <div class="col-lg-8">
                    <div class="card shadow-sm">
                        <div class="card-header bg-white fw-bold">Recent Invoices Receivables (Latest)</div>
                        <div class="table-responsive">
                            <table class="table table-sm table-hover align-middle mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th>Doc #</th>
                                        <th>Customer</th>
                                        <th>Date</th>
                                        <th class="text-end">Total (₹)</th>
                                        <th class="text-end">Balance (₹)</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for inv in data.get('recent_invoices', []) %}
                                    <tr>
                                        <td>{{ inv.doc_no }}</td>
                                        <td>{{ inv.customer }}</td>
                                        <td>{{ inv.date }}</td>
                                        <td class="text-end">{{ inv.total }}</td>
                                        <td class="text-end fw-semibold text-danger">{{ inv.balance }}</td>
                                        <td><span class="badge bg-danger">{{ inv.status }}</span></td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div class="col-lg-4">
                    <div class="card shadow-sm mb-3">
                        <div class="card-header bg-white fw-bold">Top Buyers (Month)</div>
                        <ul class="list-group list-group-flush">
                            {% for buyer in data.get('top_buyers', []) %}
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                {{ buyer.name }}
                                <span class="badge bg-primary rounded-pill">₹ {{ buyer.amount }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                    </div>

                    <div class="card shadow-sm">
                        <div class="card-header bg-white fw-bold">AR Aging Breakdown</div>
                        <div class="card-body">
                            <p class="mb-1 text-success">&lt;30d: <strong>₹ {{ data.get('aging_30', '0.00') }}</strong></p>
                            <p class="mb-1 text-warning">30-60d: <strong>₹ {{ data.get('aging_60', '0.00') }}</strong></p>
                            <p class="mb-0 text-danger">&gt;60d: <strong>₹ {{ data.get('aging_over_60', '0.00') }}</strong></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, data=data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
