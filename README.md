# BetterSelf.app

> A comprehensive personal productivity and life management tool

BetterSelf.app is a Django-based web application designed to help users manage and improve various aspects of their lives, including time management, financial tracking, wellness monitoring, and goal setting with intelligent date handling.

## 🎯 Project Overview

BetterSelf is built to provide a unified dashboard for personal life management. Users can set hierarchical goals (yearly, monthly, weekly, daily), track routines, manage schedules, monitor finances, and track wellness metrics—all from one integrated platform.

**Status:** Active Development (v2.0)  
**Tech Stack:** Django 5.1.5 | Python 3.13 | PostgreSQL | Bootstrap CSS | Django-Allauth

---

## ✨ Key Features

### 📅 Time Management (v2.0 - Enhanced)
- **Hierarchical Goal System**: Set goals at multiple time scales
  - Yearly Goals (full year tracking)
  - Monthly Goals (targeted monthly achievements)
  - Weekly Goals (Sun-Sat automatic week calculation)
  - Daily Goals (daily task tracking)
  - Custom Period Goals (flexible time ranges)
- **Intelligent Date Input System** ⭐ NEW
  - Partial date entry: enter only what you need
  - Year-only: `"2026"` → auto-fills with today's month/day
  - Month-only: `"Feb"` or `"02"` → auto-fills with today's year/day
  - Day-only: `"15th"` or `"15"` → auto-fills with today's year/month
  - Full date: combine all components for precise entry
  - Smart error detection for day-of-week names (Mon, Tue, etc.)
  - Ambiguity detection for month abbreviations (M→Mar/May suggestions)
  - Ordinal suffix support: `1st`, `2nd`, `3rd`, `4th`, `21st`, `22nd`, etc.
- **Task Subtasks**: Create nested tasks within goals for better organization
- **Schedule Management**: View and organize your schedule
- **Routine Tracking**: Build and maintain regular routines

### 💰 Finance Tracking
- Track expenses and financial metrics
- Wealth monitoring and goal setting
- Financial dashboard and reports

### 🏥 Well-being Monitoring
- Track physical and mental health metrics
- Wellness dashboard for health insights
- Integration with daily activities

### 👤 User Accounts
- User authentication and profile management
- Social login support (Google, GitHub, Facebook, Instagram)
- Profile customization with profile images
- Task and goal associations per user

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.13+
- PostgreSQL (or SQLite for local development)
- pip and virtualenv

### Step 1: Clone the Repository
```bash
git clone https://github.com/E-Nyakundi/BetterSelf.app.git
cd BetterSelf
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate      # macOS/Linux
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_NAME=BetterSelf
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 7: Start Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## 📋 Project Structure

```
BetterSelf/
├── Accounts/              # User authentication & profiles
│   ├── models.py         # User profile models
│   ├── views.py          # Login, signup, dashboard views
│   ├── forms.py          # User forms
│   └── templates/        # Auth templates
├── Time_Manager/         # Goal & task management
│   ├── models.py         # Goal, routine, schedule models
│   ├── views.py          # Goal CRUD operations
│   ├── forms.py          # Goal forms (with new date fields)
│   ├── date_utils.py     # Date parsing & utilities (NEW)
│   ├── date_fields.py    # Custom form fields (NEW)
│   └── templates/        # Goal templates
├── Finance_Wealth/       # Financial tracking
├── WellBeing/           # Health monitoring
├── Inventory/           # Item tracking
├── static/              # CSS & JavaScript
├── templates/           # Base templates
├── manage.py
├── README.md
└── requirements.txt
```

---

## 🎨 User Interface

### Dashboard
- Central hub showing all goals and activities
- Quick access to all life management modules
- Recent activity and upcoming tasks

### Goal Management
- Create goals at different time scales
- Track progress with visual indicators
- Add tasks/subtasks to goals
- Flexible date entry with intelligent parsing

### Schedules & Routines
- View your schedule at a glance
- Track daily routines and habits
- Calendar view for planning

---

## 🔧 Technical Details

### Custom Date Input System (v2.0)

**Files:**
- `Time_Manager/date_utils.py` - Parsing and formatting utilities
- `Time_Manager/date_fields.py` - Custom Django form fields
- `Time_Manager/forms.py` - Updated forms using new date fields

**Key Components:**
```python
# Utility functions
parse_month("Feb")              # → 2
parse_day("15th")              # → 15
add_ordinal_suffix(1)          # → "1st"
parse_partial_date(year=2026, month="Feb")  # → date(2026, 2, today.day)

# Custom form fields
PartialYearField()             # Year-only input
PartialMonthField()            # Month name/digit
PartialDayField()              # Day with ordinal
PartialDateField()             # Combined date picker
```

**Features:**
- Detects day-of-week names and provides guidance
- Handles ambiguous month abbreviations (M, J, etc.)
- Validates ranges (day 1-31, month 1-12, year 1900-2100)
- Generates friendly error messages

### Database Models

**User Model** (Extended via Profile)
- User authentication via Django auth
- Social authentication support
- Profile customization

**Goal Models**
- `Goal` - Base goal with year range
- `YearlyGoal`, `MonthlyGoal`, `WeeklyGoal`, `DailyGoal`, `CustomPeriodGoal`
- `Task` - Subtasks within goals
- Hierarchical relationship structure

**Other Models**
- `Routine` - Recurring activities
- `Schedule` - Event scheduling
- Financial & wellness trackers

---

## 📱 Django Apps

### Accounts
- User registration and authentication
- Profile management
- Social authentication (django-allauth)

### Time_Manager
- Goal creation and tracking
- Task management
- Schedule organization
- Routine building

### Finance_Wealth
- Expense tracking
- Financial goals
- Wealth monitoring

### WellBeing
- Health metrics
- Wellness tracking
- Mental health check-ins

### Inventory
- Item tracking
- Category management
- Usage history

---

## 🔐 Security & Authentication

- Django built-in authentication system
- Social authentication via django-allauth (Google, GitHub, Facebook, Instagram)
- CSRF protection
- Secure password hashing
- User data isolation per account

---

## 🧪 Testing

Run system checks:
```bash
python manage.py check
```

Run tests (when available):
```bash
python manage.py test
```

---

## 🌳 Recent Updates (v2.0)

### Intelligent Date Input System
- ✅ Partial date entry support
- ✅ Ordinal suffix handling (1st, 2nd, 3rd, etc.)
- ✅ Month name parsing (Feb, March, May, etc.)
- ✅ Day-of-week detection with helpful errors
- ✅ Ambiguous input detection
- ✅ Custom form widgets with proper decompress()
- ✅ Integration with all goal forms
- ✅ Comprehensive error messages

### Fixed Issues
- ✅ NotImplementedError in MultiWidget rendering
- ✅ Date field validation
- ✅ Form submission handling

---

## 📝 Development Roadmap

### Completed
- ✅ User authentication system
- ✅ Hierarchical goal system
- ✅ Intelligent date input (v2.0)
- ✅ Social authentication

### In Progress
- 🔄 Week display with date ranges
- 🔄 Templates for all goal types
- 🔄 Schedule visualization

### Planned
- 📅 Calendar integration
- 📊 Analytics dashboard
- 🔔 Notifications & reminders
- 📱 Mobile-responsive improvements
- 🎯 Advanced goal analytics

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows Django best practices and includes appropriate documentation.

---

## 📄 License

This project is open source. Check LICENSE file for details.

---

## 📞 Contact & Support

For issues, questions, or suggestions, please:
- Open an issue on GitHub
- Contact: n.lewisedgar@gmail.com

---

## 🙏 Acknowledgments

- Built with Django Framework
- Authentication via django-allauth
- Bootstrap CSS framework
- PostgreSQL database

---

**Last Updated:** May 19, 2026  
**Current Version:** v2.0  
**Branch:** B-2.0 
