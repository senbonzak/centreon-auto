#!/usr/bin/env python3
"""
Auto Ack Dashboard for Production
Clean version without test data and SocketIO
"""

from flask import Flask, render_template_string, jsonify, request, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os
import logging
import csv
from io import StringIO
from sqlalchemy import and_, or_, func
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///centreon_dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db = SQLAlchemy(app)

# ===============================================
# DATABASE MODELS
# ===============================================

class AlertAcknowledgment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.String(50), nullable=False)
    host_id = db.Column(db.String(50), nullable=False)
    service_name = db.Column(db.String(200))
    host_name = db.Column(db.String(200))
    status = db.Column(db.String(20))
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    response_time = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'host_id': self.host_id,
            'service_name': self.service_name,
            'host_name': self.host_name,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'success': self.success,
            'error_message': self.error_message,
            'response_time': self.response_time
        }

# ===============================================
# HTML TEMPLATES
# ===============================================

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centreon Auto-Acknowledge Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body { background-color: #f8f9fa; }
        .card { margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .metric-card { text-align: center; padding: 1.5rem; }
        .metric-value { font-size: 2rem; font-weight: bold; margin: 0.5rem 0; }
        .chart-container { position: relative; height: 300px; }
        .navbar { background: linear-gradient(135deg, #2c3e50, #34495e) !important; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="fas fa-tachometer-alt me-2"></i>Auto Ack Dashboard
            </span>
            <div class="navbar-nav">
                <a class="nav-link active" href="/">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
                <a class="nav-link" href="/history">
                    <i class="fas fa-history me-1"></i>History
                </a>
            </div>
            <span class="navbar-text">
                <button class="btn btn-outline-light btn-sm" onclick="location.reload()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Metrics -->
        <div class="row">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value text-primary" id="totalAcks">-</div>
                    <div>24h Acknowledgments</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value text-success" id="successfulAcks">-</div>
                    <div>24h Successful</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value text-warning" id="successRate">-</div>
                    <div>Success Rate</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="metric-value text-info" id="avgTime">-</div>
                    <div>Avg Time (s)</div>
                </div>
            </div>
        </div>

        <!-- Charts -->
        <div class="row">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar me-2"></i>Hourly Acknowledgments (24h)</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="hourlyChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie me-2"></i>Status Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="statusChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-clock me-2"></i>Recent Activity</h5>
                    </div>
                    <div class="card-body">
                        <div id="recentActivity">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let hourlyChart, statusChart;

        async function loadData() {
            try {
                // Stats
                const statsResponse = await fetch('/api/stats');
                const stats = await statsResponse.json();
                
                document.getElementById('totalAcks').textContent = stats.last_24h.total_acks;
                document.getElementById('successfulAcks').textContent = stats.last_24h.successful_acks;
                document.getElementById('successRate').textContent = stats.last_24h.success_rate + '%';
                document.getElementById('avgTime').textContent = stats.performance.avg_response_time + 's';

                // Hourly chart
                const chartResponse = await fetch('/api/charts/hourly');
                const chartData = await chartResponse.json();
                
                if (hourlyChart) hourlyChart.destroy();
                const ctx = document.getElementById('hourlyChart').getContext('2d');
                hourlyChart = new Chart(ctx, {
                    type: 'bar',
                    data: chartData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true } }
                    }
                });

                // Status chart
                const statusResponse = await fetch('/api/charts/status-distribution');
                const statusData = await statusResponse.json();
                
                if (statusChart) statusChart.destroy();
                const statusCtx = document.getElementById('statusChart').getContext('2d');
                statusChart = new Chart(statusCtx, {
                    type: 'doughnut',
                    data: statusData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });

                // Recent activity
                const activityResponse = await fetch('/api/recent-acks?limit=5');
                const activity = await activityResponse.json();
                
                const activityHtml = activity.acknowledgments.map(ack => `
                    <div class="border-start border-3 ${ack.success ? 'border-success' : 'border-danger'} ps-3 mb-2">
                        <strong>${ack.service_name || ack.service_id}</strong> on <strong>${ack.host_name || ack.host_id}</strong>
                        <br><small class="text-muted">${new Date(ack.acknowledged_at).toLocaleString()}</small>
                        <span class="badge bg-${ack.success ? 'success' : 'danger'} ms-2">
                            ${ack.success ? 'Success' : 'Failed'}
                        </span>
                        ${ack.status ? `<span class="badge bg-secondary ms-1">${ack.status}</span>` : ''}
                    </div>
                `).join('');
                
                document.getElementById('recentActivity').innerHTML = 
                    activityHtml || '<p class="text-muted">No recent activity</p>';

            } catch (error) {
                console.error('Error:', error);
                document.getElementById('recentActivity').innerHTML = 
                    '<p class="text-danger">Error loading data</p>';
            }
        }

        document.addEventListener('DOMContentLoaded', loadData);
        setInterval(loadData, 30000); // Auto-refresh every 30 seconds
    </script>
</body>
</html>
"""

HISTORY_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>History - Centreon Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .card { margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .navbar { background: linear-gradient(135deg, #2c3e50, #34495e) !important; }
        .filter-section { background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <span class="navbar-brand">
                <i class="fas fa-tachometer-alt me-2"></i>Centreon Dashboard
            </span>
            <div class="navbar-nav">
                <a class="nav-link" href="/">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
                <a class="nav-link active" href="/history">
                    <i class="fas fa-history me-1"></i>History
                </a>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Filters -->
        <div class="filter-section">
            <h5><i class="fas fa-filter me-2"></i>Filters</h5>
            <div class="row">
                <div class="col-md-3">
                    <label class="form-label">Period (days)</label>
                    <select id="periodFilter" class="form-select">
                        <option value="1">Last 24h</option>
                        <option value="7" selected>Last 7 days</option>
                        <option value="30">Last 30 days</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Status</label>
                    <select id="statusFilter" class="form-select">
                        <option value="">All</option>
                        <option value="WARNING">WARNING</option>
                        <option value="CRITICAL">CRITICAL</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Result</label>
                    <select id="successFilter" class="form-select">
                        <option value="">All</option>
                        <option value="true">Successful</option>
                        <option value="false">Failed</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button class="btn btn-primary" onclick="loadHistoryData()">
                        <i class="fas fa-search me-1"></i>Filter
                    </button>
                    <button class="btn btn-success ms-2" onclick="exportData()">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                </div>
            </div>
        </div>

        <!-- Period stats -->
        <div class="row">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-primary" id="histTotal">-</h3>
                        <p class="mb-0">Total Period</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-success" id="histSuccess">-</h3>
                        <p class="mb-0">Successful</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-danger" id="histFailed">-</h3>
                        <p class="mb-0">Failed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h3 class="text-info" id="histAvgTime">-</h3>
                        <p class="mb-0">Avg Time</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- History table -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-table me-2"></i>Detailed History</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Date/Time</th>
                                        <th>Service</th>
                                        <th>Host</th>
                                        <th>Status</th>
                                        <th>Result</th>
                                        <th>Time (s)</th>
                                        <th>Error</th>
                                    </tr>
                                </thead>
                                <tbody id="historyTable">
                                    <tr><td colspan="7" class="text-center">Click "Filter" to load data</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentHistoryData = [];

        async function loadHistoryData() {
            const period = document.getElementById('periodFilter').value;
            const status = document.getElementById('statusFilter').value;
            const success = document.getElementById('successFilter').value;
            
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - parseInt(period));
            
            const params = new URLSearchParams({
                start_date: startDate.toISOString().split('T')[0],
                end_date: endDate.toISOString().split('T')[0]
            });
            
            if (status) params.append('status', status);
            if (success) params.append('success', success);
            
            try {
                const response = await fetch('/api/history?' + params);
                const data = await response.json();
                
                currentHistoryData = data.acknowledgments || [];
                
                // Update stats
                const stats = data.stats || {};
                document.getElementById('histTotal').textContent = stats.total || 0;
                document.getElementById('histSuccess').textContent = stats.successful || 0;
                document.getElementById('histFailed').textContent = stats.failed || 0;
                document.getElementById('histAvgTime').textContent = 
                    stats.avg_response_time ? stats.avg_response_time.toFixed(3) + 's' : '-';
                
                // Update table
                const tableBody = document.getElementById('historyTable');
                if (currentHistoryData.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No data found</td></tr>';
                } else {
                    tableBody.innerHTML = currentHistoryData.map(ack => `
                        <tr>
                            <td>${new Date(ack.acknowledged_at).toLocaleString()}</td>
                            <td><strong>${ack.service_name || ack.service_id}</strong></td>
                            <td><strong>${ack.host_name || ack.host_id}</strong></td>
                            <td><span class="badge bg-${getStatusColor(ack.status)}">${ack.status || 'UNKNOWN'}</span></td>
                            <td><span class="badge ${ack.success ? 'bg-success' : 'bg-danger'}">${ack.success ? 'Success' : 'Failed'}</span></td>
                            <td>${ack.response_time ? ack.response_time.toFixed(3) : '-'}</td>
                            <td>${ack.error_message ? `<span class="text-danger" title="${ack.error_message}">${ack.error_message.substring(0, 30)}...</span>` : '-'}</td>
                        </tr>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('historyTable').innerHTML = 
                    '<tr><td colspan="7" class="text-center text-danger">Error loading data</td></tr>';
            }
        }

        function getStatusColor(status) {
            const colors = {
                'WARNING': 'warning',
                'CRITICAL': 'danger'
            };
            return colors[status] || 'secondary';
        }

        function exportData() {
            if (currentHistoryData.length === 0) {
                alert('No data to export');
                return;
            }
            
            const csv = [
                ['Date/Time', 'Service', 'Host', 'Status', 'Result', 'Time', 'Error'],
                ...currentHistoryData.map(ack => [
                    new Date(ack.acknowledged_at).toLocaleString(),
                    ack.service_name || ack.service_id,
                    ack.host_name || ack.host_id,
                    ack.status || '',
                    ack.success ? 'Success' : 'Failed',
                    ack.response_time || '',
                    ack.error_message || ''
                ])
            ].map(row => row.map(cell => '"' + String(cell).replace(/"/g, '""') + '"').join(',')).join('\\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'centreon_history.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }

        // Load default data
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(loadHistoryData, 500);
        });
    </script>
</body>
</html>
"""

# ===============================================
# ROUTES
# ===============================================

@app.route('/')
def index():
    """Dashboard home page"""
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/history')
def history():
    """History page"""
    return render_template_string(HISTORY_TEMPLATE)

@app.route('/api/stats')
def api_stats():
    """API: General statistics"""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        total_acks_24h = AlertAcknowledgment.query.filter(
            AlertAcknowledgment.acknowledged_at >= yesterday
        ).count()
        
        successful_acks_24h = AlertAcknowledgment.query.filter(
            AlertAcknowledgment.acknowledged_at >= yesterday,
            AlertAcknowledgment.success == True
        ).count()
        
        success_rate = (successful_acks_24h / total_acks_24h * 100) if total_acks_24h > 0 else 0
        
        avg_response_time = db.session.query(
            db.func.avg(AlertAcknowledgment.response_time)
        ).filter(
            AlertAcknowledgment.acknowledged_at >= yesterday,
            AlertAcknowledgment.response_time.isnot(None)
        ).scalar() or 0
        
        return jsonify({
            'last_24h': {
                'total_acks': total_acks_24h,
                'successful_acks': successful_acks_24h,
                'failed_acks': total_acks_24h - successful_acks_24h,
                'success_rate': round(success_rate, 2)
            },
            'performance': {
                'avg_response_time': round(avg_response_time, 3)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/hourly')
def api_charts_hourly():
    """API: Hourly chart"""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        results = db.session.query(
            db.func.strftime('%H', AlertAcknowledgment.acknowledged_at).label('hour'),
            db.func.count(AlertAcknowledgment.id).label('total'),
            db.func.sum(db.case([(AlertAcknowledgment.success == True, 1)], else_=0)).label('success'),
            db.func.sum(db.case([(AlertAcknowledgment.success == False, 1)], else_=0)).label('failed')
        ).filter(
            AlertAcknowledgment.acknowledged_at >= yesterday
        ).group_by(
            db.func.strftime('%H', AlertAcknowledgment.acknowledged_at)
        ).all()
        
        hours = [f"{i:02d}:00" for i in range(24)]
        successes = [0] * 24
        failures = [0] * 24
        
        for result in results:
            hour_index = int(result.hour)
            successes[hour_index] = result.success or 0
            failures[hour_index] = result.failed or 0
        
        return jsonify({
            'labels': hours,
            'datasets': [
                {
                    'label': 'Successful',
                    'data': successes,
                    'backgroundColor': 'rgba(40, 167, 69, 0.8)'
                },
                {
                    'label': 'Failed',
                    'data': failures,
                    'backgroundColor': 'rgba(220, 53, 69, 0.8)'
                }
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/status-distribution')
def api_charts_status():
    """API: Status distribution"""
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        results = db.session.query(
            AlertAcknowledgment.status,
            db.func.count(AlertAcknowledgment.id).label('count')
        ).filter(
            AlertAcknowledgment.acknowledged_at >= yesterday
        ).group_by(AlertAcknowledgment.status).all()
        
        labels = []
        data = []
        colors = ['#ffc107', '#dc3545']
        
        for i, result in enumerate(results):
            labels.append(result.status or 'UNKNOWN')
            data.append(result.count)
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': colors[:len(data)]
            }]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-acks')
def api_recent_acks():
    """API: Recent activity"""
    try:
        limit = request.args.get('limit', 10, type=int)
        recent_acks = AlertAcknowledgment.query.order_by(
            AlertAcknowledgment.acknowledged_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'acknowledgments': [ack.to_dict() for ack in recent_acks]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def api_history():
    """API: History with filters"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status_filter = request.args.get('status', '').strip()
        success_filter = request.args.get('success', '').strip()
        
        query = AlertAcknowledgment.query
        
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AlertAcknowledgment.acknowledged_at >= start_dt)
        
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(AlertAcknowledgment.acknowledged_at < end_dt)
        
        if status_filter:
            query = query.filter(AlertAcknowledgment.status == status_filter)
        
        if success_filter:
            success_bool = success_filter.lower() == 'true'
            query = query.filter(AlertAcknowledgment.success == success_bool)
        
        # Stats
        total_count = query.count()
        successful_count = query.filter(AlertAcknowledgment.success == True).count()
        failed_count = total_count - successful_count
        
        avg_response_time = query.filter(
            AlertAcknowledgment.response_time.isnot(None)
        ).with_entities(
            func.avg(AlertAcknowledgment.response_time)
        ).scalar() or 0
        
        # Data (limited to 100 for performance)
        acknowledgments = query.order_by(
            AlertAcknowledgment.acknowledged_at.desc()
        ).limit(100).all()
        
        return jsonify({
            'acknowledgments': [ack.to_dict() for ack in acknowledgments],
            'stats': {
                'total': total_count,
                'successful': successful_count,
                'failed': failed_count,
                'success_rate': (successful_count / total_count * 100) if total_count > 0 else 0,
                'avg_response_time': avg_response_time
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def save_acknowledgment(service_id, host_id, service_name=None, host_name=None, 
                       status=None, success=True, error_message=None, response_time=None):
    """Save an acknowledgment to database"""
    try:
        ack = AlertAcknowledgment(
            service_id=str(service_id),
            host_id=str(host_id),
            service_name=service_name,
            host_name=host_name,
            status=status,
            success=success,
            error_message=error_message,
            response_time=response_time
        )
        db.session.add(ack)
        db.session.commit()
        return ack.id
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving acknowledgment: {e}")
        return None

def init_database():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("Database initialized")

# ===============================================
# INITIALIZATION
# ===============================================

if __name__ == '__main__':
    # Logging configuration
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    init_database()
    
    # Startup information
    port = int(os.getenv('FLASK_PORT', 5000))
    print("=" * 50)
    print("Auto Ack DASHBOARD")
    print("=" * 50)
    print(f"Dashboard: http://localhost:{port}")
    print(f"History: http://localhost:{port}/history")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 50)
    print("Features:")
    print("  - Real-time dashboard with metrics")
    print("  - History page with filters")
    print("  - CSV export functionality")
    print("  - Auto-refresh every 30s")
    print("=" * 50)
    
    # Launch application
    app.run(debug=False, host='0.0.0.0', port=port)