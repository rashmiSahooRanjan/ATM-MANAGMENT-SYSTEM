from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from io import BytesIO
import re
import os

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

app = Flask(__name__)
app.config.from_object(Config)

mongo = PyMongo(app)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin' not in session:
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def generate_account_number():
    last_user = mongo.db.users.find_one(sort=[("_id", -1)])
    if last_user and 'account_number' in last_user:
        last_num = int(last_user['account_number'].replace('ATM', ''))
        return f"ATM{last_num + 1:05d}"
    return "ATM10001"

def generate_transaction_id():
    import random, string
    return 'TXN' + ''.join(random.choices(string.digits, k=10))

def get_current_user():
    if 'user_id' in session:
        return mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return None

def ensure_admin():
    """Create default admin if not exists."""
    existing = mongo.db.admins.find_one({'username': app.config['ADMIN_USERNAME']})
    if not existing:
        mongo.db.admins.insert_one({
            'username': app.config['ADMIN_USERNAME'],
            'password': generate_password_hash(app.config['ADMIN_PASSWORD']),
            'created_at': datetime.now()
        })

# ─────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Valid email is required.')
        if not mobile or not re.match(r'^\d{10}$', mobile):
            errors.append('Valid 10-digit mobile number is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', form_data=request.form)

        if mongo.db.users.find_one({'email': email}):
            flash('Email already registered.', 'danger')
            return render_template('register.html', form_data=request.form)

        account_number = generate_account_number()
        hashed_pw = generate_password_hash(password)
        now = datetime.now()

        mongo.db.users.insert_one({
            'account_number': account_number,
            'full_name': full_name,
            'email': email,
            'mobile': mobile,
            'password': hashed_pw,
            'balance': 0.0,
            'status': 'active',
            'last_login': now,
            'created_at': now
        })

        flash(f'Account created! Your Account Number: {account_number}', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = mongo.db.users.find_one({'email': email})
        if not user or not check_password_hash(user['password'], password):
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')

        if user.get('status') == 'frozen':
            flash('Your account is frozen. Contact support.', 'danger')
            return render_template('login.html')

        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'last_login': datetime.now()}})
        session['user_id'] = str(user['_id'])
        session['account_number'] = user['account_number']
        session['full_name'] = user['full_name']
        flash(f'Welcome back, {user["full_name"]}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# USER ROUTES
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if not user:
        session.clear()
        return redirect(url_for('login'))

    recent_txns = list(mongo.db.transactions.find(
        {'account_number': user['account_number']}
    ).sort('timestamp', -1).limit(5))

    total_txns = mongo.db.transactions.count_documents({'account_number': user['account_number']})

    # Chart data: last 7 days deposits vs withdrawals
    seven_days_ago = datetime.now() - timedelta(days=7)
    chart_labels = []
    chart_deposits = []
    chart_withdrawals = []
    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        label = day.strftime('%d %b')
        chart_labels.append(label)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        dep = mongo.db.transactions.aggregate([
            {'$match': {'account_number': user['account_number'], 'transaction_type': 'Deposit',
                        'timestamp': {'$gte': day_start, '$lte': day_end}}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ])
        dep_list = list(dep)
        chart_deposits.append(dep_list[0]['total'] if dep_list else 0)

        wit = mongo.db.transactions.aggregate([
            {'$match': {'account_number': user['account_number'], 'transaction_type': 'Withdraw',
                        'timestamp': {'$gte': day_start, '$lte': day_end}}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ])
        wit_list = list(wit)
        chart_withdrawals.append(wit_list[0]['total'] if wit_list else 0)

    return render_template('dashboard.html',
        user=user,
        recent_txns=recent_txns,
        total_txns=total_txns,
        chart_labels=chart_labels,
        chart_deposits=chart_deposits,
        chart_withdrawals=chart_withdrawals
    )

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    user = get_current_user()
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('deposit.html', user=user)

        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('deposit.html', user=user)

        if amount > 1000000:
            flash('Maximum single deposit is ₹10,00,000.', 'danger')
            return render_template('deposit.html', user=user)

        new_balance = user['balance'] + amount
        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'balance': new_balance}})

        txn_id = generate_transaction_id()
        mongo.db.transactions.insert_one({
            'transaction_id': txn_id,
            'account_number': user['account_number'],
            'transaction_type': 'Deposit',
            'amount': amount,
            'receiver_account': None,
            'balance_after': new_balance,
            'status': 'Success',
            'timestamp': datetime.now()
        })

        flash(f'₹{amount:,.2f} deposited successfully! Transaction ID: {txn_id}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('deposit.html', user=user)

@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    user = get_current_user()
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('withdraw.html', user=user)

        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('withdraw.html', user=user)

        if amount > user['balance']:
            flash('Insufficient balance.', 'danger')
            return render_template('withdraw.html', user=user)

        if amount > 100000:
            flash('Maximum single withdrawal is ₹1,00,000.', 'danger')
            return render_template('withdraw.html', user=user)

        new_balance = user['balance'] - amount
        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'balance': new_balance}})

        txn_id = generate_transaction_id()
        mongo.db.transactions.insert_one({
            'transaction_id': txn_id,
            'account_number': user['account_number'],
            'transaction_type': 'Withdraw',
            'amount': amount,
            'receiver_account': None,
            'balance_after': new_balance,
            'status': 'Success',
            'timestamp': datetime.now()
        })

        flash(f'₹{amount:,.2f} withdrawn successfully! Transaction ID: {txn_id}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('withdraw.html', user=user)

@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    user = get_current_user()
    if request.method == 'POST':
        receiver_acc = request.form.get('receiver_account', '').strip().upper()
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('transfer.html', user=user)

        if receiver_acc == user['account_number']:
            flash('Cannot transfer to your own account.', 'danger')
            return render_template('transfer.html', user=user)

        receiver = mongo.db.users.find_one({'account_number': receiver_acc})
        if not receiver:
            flash('Receiver account not found.', 'danger')
            return render_template('transfer.html', user=user)

        if receiver.get('status') == 'frozen':
            flash('Receiver account is frozen.', 'danger')
            return render_template('transfer.html', user=user)

        if amount <= 0:
            flash('Amount must be greater than 0.', 'danger')
            return render_template('transfer.html', user=user)

        if amount > user['balance']:
            flash('Insufficient balance.', 'danger')
            return render_template('transfer.html', user=user)

        # Deduct sender
        new_sender_balance = user['balance'] - amount
        mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'balance': new_sender_balance}})

        # Add receiver
        new_receiver_balance = receiver['balance'] + amount
        mongo.db.users.update_one({'_id': receiver['_id']}, {'$set': {'balance': new_receiver_balance}})

        txn_id = generate_transaction_id()
        now = datetime.now()

        # Sender transaction
        mongo.db.transactions.insert_one({
            'transaction_id': txn_id,
            'account_number': user['account_number'],
            'transaction_type': 'Transfer Sent',
            'amount': amount,
            'receiver_account': receiver_acc,
            'balance_after': new_sender_balance,
            'status': 'Success',
            'timestamp': now
        })

        # Receiver transaction
        mongo.db.transactions.insert_one({
            'transaction_id': txn_id + 'R',
            'account_number': receiver_acc,
            'transaction_type': 'Transfer Received',
            'amount': amount,
            'receiver_account': user['account_number'],
            'balance_after': new_receiver_balance,
            'status': 'Success',
            'timestamp': now
        })

        flash(f'₹{amount:,.2f} transferred to {receiver["full_name"]} ({receiver_acc}). TXN: {txn_id}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('transfer.html', user=user)

@app.route('/balance')
@login_required
def balance():
    user = get_current_user()
    return render_template('balance.html', user=user)

@app.route('/history')
@login_required
def history():
    user = get_current_user()
    page = int(request.args.get('page', 1))
    per_page = 10
    search = request.args.get('search', '').strip()
    txn_type = request.args.get('type', '').strip()

    query = {'account_number': user['account_number']}
    if search:
        query['$or'] = [
            {'transaction_id': {'$regex': search, '$options': 'i'}},
            {'transaction_type': {'$regex': search, '$options': 'i'}}
        ]
    if txn_type:
        query['transaction_type'] = txn_type

    total = mongo.db.transactions.count_documents(query)
    total_pages = (total + per_page - 1) // per_page
    skip = (page - 1) * per_page

    transactions = list(mongo.db.transactions.find(query).sort('timestamp', -1).skip(skip).limit(per_page))

    return render_template('history.html',
        user=user,
        transactions=transactions,
        page=page,
        total_pages=total_pages,
        total=total,
        search=search,
        txn_type=txn_type
    )

@app.route('/history/pdf')
@login_required
def download_history_pdf():
    user = get_current_user()
    transactions = list(mongo.db.transactions.find(
        {'account_number': user['account_number']}
    ).sort('timestamp', -1).limit(100))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=20, textColor=colors.HexColor('#1a237e'),
                                  alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                     fontSize=10, textColor=colors.HexColor('#555555'),
                                     alignment=TA_CENTER, spaceAfter=4)
    info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.HexColor('#333333'),
                                 spaceAfter=2)

    elements.append(Paragraph("🏦 ATM Management System", title_style))
    elements.append(Paragraph("Transaction History Report", subtitle_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", subtitle_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a237e')))
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph(f"<b>Account Holder:</b> {user['full_name']}", info_style))
    elements.append(Paragraph(f"<b>Account Number:</b> {user['account_number']}", info_style))
    elements.append(Paragraph(f"<b>Email:</b> {user['email']}", info_style))
    elements.append(Paragraph(f"<b>Current Balance:</b> ₹{user['balance']:,.2f}", info_style))
    elements.append(Spacer(1, 0.4*cm))

    data = [['#', 'Transaction ID', 'Type', 'Amount (₹)', 'Date & Time', 'Status']]
    for i, txn in enumerate(transactions, 1):
        data.append([
            str(i),
            txn.get('transaction_id', 'N/A'),
            txn.get('transaction_type', 'N/A'),
            f"₹{txn.get('amount', 0):,.2f}",
            txn['timestamp'].strftime('%d %b %Y %I:%M %p') if isinstance(txn.get('timestamp'), datetime) else str(txn.get('timestamp', '')),
            txn.get('status', 'N/A')
        ])

    col_widths = [0.6*cm, 3.2*cm, 3.2*cm, 2.5*cm, 4.2*cm, 2*cm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8eaf6')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c5cae9')),
        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#c5cae9')))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("This is a computer-generated document. No signature required.", subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"transactions_{user['account_number']}.pdf",
                     mimetype='application/pdf')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            mobile = request.form.get('mobile', '').strip()

            if not full_name:
                flash('Full name is required.', 'danger')
                return render_template('profile.html', user=user)
            if not re.match(r'^\d{10}$', mobile):
                flash('Valid 10-digit mobile number is required.', 'danger')
                return render_template('profile.html', user=user)

            mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'full_name': full_name, 'mobile': mobile}})
            session['full_name'] = full_name
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not check_password_hash(user['password'], current_pw):
                flash('Current password is incorrect.', 'danger')
                return render_template('profile.html', user=user)
            if len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'danger')
                return render_template('profile.html', user=user)
            if new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
                return render_template('profile.html', user=user)

            mongo.db.users.update_one({'_id': user['_id']}, {'$set': {'password': generate_password_hash(new_pw)}})
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))

    user = get_current_user()
    return render_template('profile.html', user=user)

# API: Validate receiver account
@app.route('/api/validate-account/<account_number>')
@login_required
def validate_account(account_number):
    acc = account_number.strip().upper()
    user = mongo.db.users.find_one({'account_number': acc})
    if user:
        return jsonify({'valid': True, 'name': user['full_name'], 'status': user.get('status', 'active')})
    return jsonify({'valid': False})

# ─────────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────────

@app.route('/admin')
def admin_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    ensure_admin()
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = mongo.db.admins.find_one({'username': username})
        if admin and check_password_hash(admin['password'], password):
            session['admin'] = username
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users = mongo.db.users.count_documents({})
    active_users = mongo.db.users.count_documents({'status': 'active'})
    frozen_users = mongo.db.users.count_documents({'status': 'frozen'})
    total_txns = mongo.db.transactions.count_documents({})

    dep_agg = list(mongo.db.transactions.aggregate([
        {'$match': {'transaction_type': 'Deposit'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]))
    total_deposits = dep_agg[0]['total'] if dep_agg else 0

    wit_agg = list(mongo.db.transactions.aggregate([
        {'$match': {'transaction_type': 'Withdraw'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]))
    total_withdrawals = wit_agg[0]['total'] if wit_agg else 0

    trf_agg = list(mongo.db.transactions.aggregate([
        {'$match': {'transaction_type': 'Transfer Sent'}},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]))
    total_transfers = trf_agg[0]['total'] if trf_agg else 0

    recent_users = list(mongo.db.users.find().sort('created_at', -1).limit(5))
    recent_txns = list(mongo.db.transactions.find().sort('timestamp', -1).limit(10))

    # Monthly stats for chart
    monthly_labels = []
    monthly_deposits = []
    monthly_withdrawals = []
    for i in range(5, -1, -1):
        month_date = datetime.now() - timedelta(days=30 * i)
        label = month_date.strftime('%b %Y')
        monthly_labels.append(label)
        m_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_date.month == 12:
            m_end = month_date.replace(year=month_date.year+1, month=1, day=1) - timedelta(seconds=1)
        else:
            m_end = month_date.replace(month=month_date.month+1, day=1) - timedelta(seconds=1)

        d_agg = list(mongo.db.transactions.aggregate([
            {'$match': {'transaction_type': 'Deposit', 'timestamp': {'$gte': m_start, '$lte': m_end}}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]))
        monthly_deposits.append(d_agg[0]['total'] if d_agg else 0)

        w_agg = list(mongo.db.transactions.aggregate([
            {'$match': {'transaction_type': 'Withdraw', 'timestamp': {'$gte': m_start, '$lte': m_end}}},
            {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
        ]))
        monthly_withdrawals.append(w_agg[0]['total'] if w_agg else 0)

    return render_template('admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        frozen_users=frozen_users,
        total_txns=total_txns,
        total_deposits=total_deposits,
        total_withdrawals=total_withdrawals,
        total_transfers=total_transfers,
        recent_users=recent_users,
        recent_txns=recent_txns,
        monthly_labels=monthly_labels,
        monthly_deposits=monthly_deposits,
        monthly_withdrawals=monthly_withdrawals
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10

    query = {}
    if search:
        query['$or'] = [
            {'full_name': {'$regex': search, '$options': 'i'}},
            {'email': {'$regex': search, '$options': 'i'}},
            {'account_number': {'$regex': search, '$options': 'i'}},
            {'mobile': {'$regex': search, '$options': 'i'}}
        ]
    if status_filter:
        query['status'] = status_filter

    total = mongo.db.users.count_documents(query)
    total_pages = (total + per_page - 1) // per_page
    skip = (page - 1) * per_page
    users = list(mongo.db.users.find(query).sort('created_at', -1).skip(skip).limit(per_page))

    return render_template('users.html',
        users=users,
        page=page,
        total_pages=total_pages,
        total=total,
        search=search,
        status_filter=status_filter
    )

@app.route('/admin/users/action', methods=['POST'])
@admin_required
def admin_user_action():
    user_id = request.form.get('user_id')
    action = request.form.get('action')

    try:
        uid = ObjectId(user_id)
    except Exception:
        flash('Invalid user ID.', 'danger')
        return redirect(url_for('admin_users'))

    user = mongo.db.users.find_one({'_id': uid})
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users'))

    if action == 'freeze':
        mongo.db.users.update_one({'_id': uid}, {'$set': {'status': 'frozen'}})
        flash(f'Account {user["account_number"]} frozen.', 'warning')
    elif action == 'activate':
        mongo.db.users.update_one({'_id': uid}, {'$set': {'status': 'active'}})
        flash(f'Account {user["account_number"]} activated.', 'success')
    elif action == 'delete':
        mongo.db.users.delete_one({'_id': uid})
        mongo.db.transactions.delete_many({'account_number': user['account_number']})
        flash(f'User {user["account_number"]} deleted.', 'danger')

    return redirect(url_for('admin_users'))

# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('404.html', error="500 - Internal Server Error"), 500

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        ensure_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)
