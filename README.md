
# 🏦 ATM Management System

A full-featured, production-quality ATM Banking System built with **Python Flask** and **MongoDB Atlas**, featuring a premium glassmorphism dark-blue UI.

---

## 🚀 Features

### User Features

- ✅ User Registration with auto-generated Account Numbers (ATM10001, ATM10002…)
- ✅ Secure Login / Logout with Flask sessions
- ✅ Dashboard with balance, stats, recent transactions & 7-day activity chart
- ✅ Deposit Money (with quick-amount buttons & live preview)
- ✅ Withdraw Money (with insufficient-balance guard)
- ✅ Fund Transfer (real-time receiver account validation via API)
- ✅ Balance Inquiry (card-style display)
- ✅ Transaction History (search, filter, pagination)
- ✅ Download Transaction History as PDF (ReportLab)
- ✅ Profile Management (edit name/mobile, change password)

### Admin Features

- ✅ Separate Admin Login (`/admin/login`)
- ✅ Admin Dashboard with system-wide stats and monthly bar chart
- ✅ Manage Users: View, Search, Filter by status
- ✅ Freeze / Activate User Accounts
- ✅ Delete Users (with all associated transactions)

### Security

- ✅ Werkzeug bcrypt password hashing
- ✅ Flask session authentication
- ✅ Protected routes (`@login_required`, `@admin_required`)
- ✅ Input validation (server-side)
- ✅ CSRF-safe forms
- ✅ Frozen account prevention on login and transfer

---

## 🛠️ Tech Stack

| Layer    | Technology                               |
| -------- | ---------------------------------------- |
| Backend  | Python Flask 3.x                         |
| Database | MongoDB Atlas (pymongo)                  |
| Auth     | Flask Session + Werkzeug                 |
| PDF      | ReportLab                                |
| Frontend | HTML5, CSS3, Bootstrap 5, Font Awesome 6 |
| Charts   | Chart.js 4                               |
| Fonts    | Outfit + JetBrains Mono                  |

---

## 📁 Project Structure

```
ATM_Management_System/
├── app.py               # Main Flask application
├── config.py            # Configuration class
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── README.md
├── static/
│   ├── css/
│   │   └── style.css    # Complete custom styles
│   └── js/
│       └── script.js    # Interactivity & animations
└── templates/
    ├── base.html         # Master layout (sidebar + topbar)
    ├── index.html        # Landing page
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── deposit.html
    ├── withdraw.html
    ├── transfer.html
    ├── balance.html
    ├── history.html
    ├── profile.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── users.html
    └── 404.html
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.9+
- MongoDB Atlas account (free tier works)

### 2. Clone / Extract the Project

```bash
cd ATM_Management_System
```

### 3. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Edit `.env`:

```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/atm_management?retryWrites=true&w=majority
SECRET_KEY=your_very_secure_random_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@1234
```

> **Get your MONGO_URI:**
>
> 1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
> 2. Create a free cluster
> 3. Click **Connect → Drivers**
> 4. Copy the connection string and replace `<username>` / `<password>`

### 6. Run the Application

```bash
python app.py
```

Open your browser: **http://localhost:5000**

---

## 👤 Default Credentials

### Admin

| Field    | Value                             |
| -------- | --------------------------------- |
| URL      | http://localhost:5000/admin/login |
| Username | `admin`                         |
| Password | `Admin@1234`                    |

> Change these in your `.env` file before deploying.

### Demo User

Register a new account at `/register` — an account number is auto-generated.

---

## 📊 Database Collections

### `users`

```json
{
  "account_number": "ATM10001",
  "full_name": "John Doe",
  "email": "john@example.com",
  "mobile": "9876543210",
  "password": "<bcrypt_hash>",
  "balance": 5000.00,
  "status": "active",
  "last_login": "2024-01-15T10:30:00",
  "created_at": "2024-01-01T09:00:00"
}
```

### `transactions`

```json
{
  "transaction_id": "TXN1234567890",
  "account_number": "ATM10001",
  "transaction_type": "Deposit",
  "amount": 1000.00,
  "receiver_account": null,
  "balance_after": 6000.00,
  "status": "Success",
  "timestamp": "2024-01-15T10:35:00"
}
```

### `admins`

```json
{
  "username": "admin",
  "password": "<bcrypt_hash>",
  "created_at": "2024-01-01T00:00:00"
}
```

---

## 🌐 Routes Reference

| Route                          | Method   | Description                 |
| ------------------------------ | -------- | --------------------------- |
| `/`                          | GET      | Landing page                |
| `/register`                  | GET/POST | User registration           |
| `/login`                     | GET/POST | User login                  |
| `/logout`                    | GET      | Logout                      |
| `/dashboard`                 | GET      | User dashboard              |
| `/deposit`                   | GET/POST | Deposit money               |
| `/withdraw`                  | GET/POST | Withdraw money              |
| `/transfer`                  | GET/POST | Fund transfer               |
| `/balance`                   | GET      | Balance inquiry             |
| `/history`                   | GET      | Transaction history         |
| `/history/pdf`               | GET      | Download PDF                |
| `/profile`                   | GET/POST | Profile management          |
| `/api/validate-account/<id>` | GET      | Validate receiver account   |
| `/admin/login`               | GET/POST | Admin login                 |
| `/admin/dashboard`           | GET      | Admin dashboard             |
| `/admin/users`               | GET      | Manage users                |
| `/admin/users/action`        | POST     | Freeze/activate/delete user |

---

## 🎨 UI Highlights

- **Dark Blue theme** with Royal Blue and White accents
- **Glassmorphism** cards and panels
- **Responsive sidebar** navigation with collapse support
- **Animated** stat counters, chart.js activity graphs
- **Live balance preview** on deposit/withdraw/transfer
- **Real-time account validation** via fetch API on transfer page
- **PDF receipt generation** with ReportLab

---

## 👨‍💻 Authors

| Name                          | Role      |
| ----------------------------- | --------- |
| **Rashmi Ranjan Sahoo** | Developer |

## 📄 License

MIT License — free to use and modify.
