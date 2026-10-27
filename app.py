import os
import json
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-session-key-adarsh")

# Cloud configuration (Set in Render Environment Variables or keep default)
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

# -----------------------------------------------------------------------------
# 1. API Endpoint for ERP Python sync
# -----------------------------------------------------------------------------
@app.route("/api/sync", methods=["POST"])
def sync_dashboard():
    auth_header = request.headers.get("X-API-KEY")
    if auth_header != API_SECRET_TOKEN:
        return jsonify({"status": "unauthorized"}), 401
    
    payload = request.get_json()
    if not payload:
        return jsonify({"status": "bad request"}), 400
    
    save_data(payload)
    return jsonify({"status": "success", "message": "All reports updated successfully"}), 200

# -----------------------------------------------------------------------------
# 2. Login & Logout
# -----------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("portal"))
        else:
            error = "Invalid password. Please try again."
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEW ERP Portal - Authentication</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light d-flex align-items-center" style="height: 100vh;">
        <div class="container" style="max-width: 380px;">
            <div class="card shadow-sm p-4 border-0">
                <h5 class="text-center fw-bold mb-1">Adarsh Engineering Works</h5>
                <p class="text-center text-muted small mb-3">Executive Operations & Tax Portal</p>
                {% if error %}<div class="alert alert-danger py-2 small">{{ error }}</div>{% endif %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label small fw-semibold">Enter Password</label>
                        <input type="password" name="password" class="form-control" placeholder="••••••••" required autofocus>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Sign In</button>
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

# -----------------------------------------------------------------------------
# 3. Main Multi-Report Portal
# -----------------------------------------------------------------------------
@app.route("/")
@login_required
def portal():
    data = get_data()
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AEW ERP - Executive Business Intelligence</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #F1F5F9; font-size: 0.88rem; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            .kpi-card { border-radius: 6px; border: 1px solid #CBD5E1; background: #FFF; padding: 12px; }
            .kpi-title { font-size: 0.72rem; font-weight: 800; text-transform: uppercase; margin-bottom: 2px; }
            .kpi-value { font-size: 1.35rem; font-weight: 800; color: #0F172A; }
            .table-sm th, .table-sm td { padding: 6px 10px; font-size: 0.84rem; }
            .nav-pills .nav-link { color: #334155; font-weight: 600; padding: 6px 16px; border-radius: 4px; }
            .nav-pills .nav-link.active { background-color: #0284C7; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark px-3 py-2 mb-3 shadow-sm">
            <span class="navbar-brand mb-0 h6 fw-bold">ADARSH ENGINEERING WORKS - Executive Operations</span>
            <div class="d-flex align-items-center">
                <span class="text-light opacity-75 me-3 small">Synced: {{ data.get('last_synced', 'Pending First Sync') }}</span>
                <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
            </div>
        </nav>

        <div class="container-fluid px-3">
            <!-- Navigation Tabs -->
            <ul class="nav nav-pills mb-3 border-bottom pb-2">
                <li class="nav-item">
                    <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#tab-dashboard">📊 Operations Dashboard</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab-gstr3b">🏛️ GSTR-3B Tax Offset</button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" data-bs-toggle="pill" data-bs-target="#tab-ledgers">👥 Party Outstanding</button>
                </li>
            </ul>

            <div class="tab-content">
                <!-- TAB 1: EXECUTIVE OPERATIONS DASHBOARD -->
                <div class="tab-pane fade show active" id="tab-dashboard">
                    <!-- KPI Metric Ribbon -->
                    <div class="row g-2 mb-3">
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-primary">
                                <div class="kpi-title text-primary">This Month Turnover</div>
                                <div class="kpi-value">₹ {{ data.get('turnover', '0.00') }}</div>
                                <small class="text-muted">{{ data.get('period', 'Active Month') }}</small>
                            </div>
                        </div>
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-secondary">
                                <div class="kpi-title text-secondary">Period Billed</div>
                                <div class="kpi-value">₹ {{ data.get('period_billed', '0.00') }}</div>
                                <small class="text-muted">Outward Billed</small>
                            </div>
                        </div>
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-success">
                                <div class="kpi-title text-success">Collected Cash/Bank</div>
                                <div class="kpi-value">₹ {{ data.get('collected_cash', '0.00') }}</div>
                                <small class="text-muted">Recovery: {{ data.get('recovery_rate', '0%') }}</small>
                            </div>
                        </div>
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-danger">
                                <div class="kpi-title text-danger">AR Outstanding</div>
                                <div class="kpi-value">₹ {{ data.get('ar_outstanding', '0.00') }}</div>
                                <small class="text-muted">Pending Total</small>
                            </div>
                        </div>
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-info">
                                <div class="kpi-title text-info">Net GST Liability</div>
                                <div class="kpi-value">₹ {{ data.get('net_gst', '0.00') }}</div>
                                <small class="text-muted">Payable Cash</small>
                            </div>
                        </div>
                        <div class="col-6 col-md-2">
                            <div class="kpi-card border-start border-4 border-warning">
                                <div class="kpi-title text-warning">Open Challans</div>
                                <div class="kpi-value">{{ data.get('open_challans_count', '0') }} Open</div>
                                <small class="text-muted">Dispatched Not Invoiced</small>
                            </div>
                        </div>
                    </div>

                    <!-- Aging Ribbon -->
                    <div class="alert alert-light border py-2 mb-3 d-flex gap-4">
                        <span class="fw-bold text-dark">AR Aging Health:</span>
                        <span class="text-success fw-semibold">● &lt;30d: ₹ {{ data.get('aging_30', '0.00') }}</span>
                        <span class="text-warning fw-semibold">● 30-60d: ₹ {{ data.get('aging_60', '0.00') }}</span>
                        <span class="text-danger fw-semibold">● &gt;60d: ₹ {{ data.get('aging_over_60', '0.00') }}</span>
                    </div>

                    <!-- Split Tables & Top Buyers -->
                    <div class="row g-3">
                        <div class="col-lg-8">
                            <div class="card shadow-sm border-0">
                                <div class="card-header bg-white fw-bold py-2">Recent Invoices & Receivables (Latest 10)</div>
                                <div class="table-responsive">
                                    <table class="table table-sm table-hover align-middle mb-0">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Doc #</th>
                                                <th>Customer</th>
                                                <th>Date</th>
                                                <th class="text-end">Total (₹)</th>
                                                <th class="text-end">Balance (₹)</th>
                                                <th class="text-center">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for inv in data.get('recent_invoices', []) %}
                                            <tr>
                                                <td class="fw-bold">{{ inv.doc_no }}</td>
                                                <td>{{ inv.customer }}</td>
                                                <td>{{ inv.date }}</td>
                                                <td class="text-end">{{ inv.total }}</td>
                                                <td class="text-end fw-bold text-danger">{{ inv.balance }}</td>
                                                <td class="text-center">
                                                    <span class="badge {{ 'bg-success' if inv.status == 'Paid' else ('bg-warning text-dark' if inv.status == 'Partial' else 'bg-danger') }}">
                                                        {{ inv.status }}
                                                    </span>
                                                </td>
                                            </tr>
                                            {% else %}
                                            <tr><td colspan="6" class="text-center py-3 text-muted">No recent invoices synced yet.</td></tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        <div class="col-lg-4">
                            <div class="card shadow-sm border-0">
                                <div class="card-header bg-white fw-bold py-2">Top Buyers (Active Period)</div>
                                <ul class="list-group list-group-flush">
                                    {% for buyer in data.get('top_buyers', []) %}
                                    <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                                        <span class="fw-semibold text-truncate" style="max-width: 200px;">{{ buyer.name }}</span>
                                        <span class="badge bg-primary rounded-pill">₹ {{ buyer.amount }}</span>
                                    </li>
                                    {% else %}
                                    <li class="list-group-item text-muted text-center py-3">No top buyers recorded.</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- TAB 2: GSTR-3B TAX OFFSET REPORT -->
                <div class="tab-pane fade" id="tab-gstr3b">
                    <div class="card shadow-sm border-0 p-3">
                        <h6 class="fw-bold mb-3 text-primary">🏛️ GSTR-3B Tax Offset & Net Liability Statement</h6>
                        <div class="table-responsive">
                            <table class="table table-bordered table-sm align-middle mb-0">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Tax Period / Month</th>
                                        <th class="text-end">Sales Taxable (₹)</th>
                                        <th class="text-end">Outward GST (₹)</th>
                                        <th class="text-end">Inward ITC Offset (₹)</th>
                                        <th class="text-end">Net Cash Tax Due (₹)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for row in data.get('gstr3b_reports', []) %}
                                    <tr>
                                        <td class="fw-bold">{{ row.month }}</td>
                                        <td class="text-end">{{ row.sales_taxable }}</td>
                                        <td class="text-end text-danger fw-semibold">₹ {{ row.outward_tax }}</td>
                                        <td class="text-end text-primary fw-semibold">₹ {{ row.inward_itc }}</td>
                                        <td class="text-end fw-bold {{ 'text-danger' if '-' not in row.net_liability else 'text-success' }}">
                                            ₹ {{ row.net_liability }}
                                        </td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="5" class="text-center py-3 text-muted">No tax offset data synced.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- TAB 3: PARTY RECEIVABLES LEDGER SUMMARY -->
                <div class="tab-pane fade" id="tab-ledgers">
                    <div class="card shadow-sm border-0 p-3">
                        <h6 class="fw-bold mb-3 text-primary">👥 Customer / Party Receivables Outstanding</h6>
                        <div class="table-responsive">
                            <table class="table table-striped table-sm align-middle mb-0">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Customer / OEM Client</th>
                                        <th class="text-end">Total Billed (₹)</th>
                                        <th class="text-end">Total Received (₹)</th>
                                        <th class="text-end">Pending Outstanding (₹)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for party in data.get('party_ledgers', []) %}
                                    <tr>
                                        <td class="fw-bold">{{ party.customer }}</td>
                                        <td class="text-end">{{ party.billed }}</td>
                                        <td class="text-end text-success">{{ party.paid }}</td>
                                        <td class="text-end fw-bold text-danger">₹ {{ party.pending }}</td>
                                    </tr>
                                    {% else %}
                                    <tr><td colspan="4" class="text-center py-3 text-muted">No pending balances synced.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """, data=data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
