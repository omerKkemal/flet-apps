<div align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-green.svg" alt="Version 1.0.0"/>
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/flet-0.25.0+-orange.svg" alt="Flet 0.25.0+"/>
  <img src="https://img.shields.io/badge/license-MIT-purple.svg" alt="License MIT"/>
</div>

<br/>

<p align="center">
  <b>📿 رحلة العودة إلى الله خطوة بخطوة</b><br/>
  <i>A beautiful Islamic application to track and manage missed prayers (Qada) with a spiritual dark theme</i>
</p>

<br/>

## ✨ Features

### 🌙 Beautiful Dark Theme
- Islamic-inspired color palette (Deep Green, Gold, Royal Blue)
- Night sky ambiance for peaceful usage
- Smooth gradients and elegant shadows
- RTL support for Arabic language

### 📊 Smart Tracking
- Track missed prayers (Fajr, Dhuhr, Asr, Maghrib, Isha)
- Track fasting days
- Multiple time units: Days, Weeks, Months, Years
- Automatic calculation of total days

### 💾 Database Persistence
- SQLite3 database for data storage
- Save progress automatically
- View history of all sessions
- Resume incomplete sessions

### 📈 Progress Statistics
- Completed days counter
- Total tasks completed
- Remaining days tracker
- Visual progress indicators

### 🎯 Interactive Features
- Checkbox-based daily tasks
- Automatic next button enabling
- Save progress manually
- Session history with resume option
- Celebration screen upon completion

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/prayer-tracker.git
cd prayer-tracker
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install flet
```

### Step 4: Run the Application
```bash
python main.py
```

## 📖 How to Use

### 1. **Start a New Session**
   - Select worship type (Prayer/Fasting)
   - Choose time unit (Day/Week/Month/Year)
   - Enter the amount
   - Click "✨ إنشاء القائمة"

### 2. **Complete Daily Tasks**
   - Check off each prayer/fasting task for the day
   - All tasks must be completed to enable the "Next" button
   - Click "➡️ التالي" to move to the next day

### 3. **Save Progress**
   - Click the save button (💾) to manually save progress
   - Progress is automatically saved when moving to next day

### 4. **View History**
   - Click the history button (📜) to see past sessions
   - Resume any incomplete session
   - Track your overall progress

### 5. **Completion**
   - Upon completing all days, a celebration screen appears
   - Start a new session from the completion screen

## 🎨 Color Scheme

| Color | Hex Code | Usage |
|-------|----------|-------|
| Deep Green | `#4CAF50` | Primary buttons, accents |
| Gold | `#FFD700` | Headers, highlights |
| Coral Red | `#FF6B6B` | Errors, warnings |
| Dark Blue | `#16213E` | Surface cards |
| Royal Blue | `#0F3460` | Card backgrounds |
| Dark Purple | `#1A1A2E` | Main background |

## 🗄️ Database Structure

### Sessions Table
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qada_type TEXT NOT NULL,
    unit TEXT NOT NULL,
    amount INTEGER NOT NULL,
    total_days INTEGER NOT NULL,
    current_day INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Daily Tasks Table
```sql
CREATE TABLE daily_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    day_number INTEGER NOT NULL,
    tasks_completed TEXT,  -- JSON array
    completed BOOLEAN DEFAULT 0,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions (id)
)
```

## 🛠️ Project Structure

```
prayer-tracker/
│
├── main.py                 # Main application file
├── prayer_tracker.db       # SQLite database (auto-generated)
├── README.md              # This file
└── requirements.txt       # Dependencies
```

## 📦 Dependencies

- [Flet](https://flet.dev/) - GUI framework for building interactive apps
- SQLite3 - Built-in Python database (no installation needed)
- JSON - Built-in Python module

## 🌟 Future Enhancements

- [ ] Add reminders/notifications
- [ ] Export data to CSV/PDF
- [ ] Add more worship types (Quran reading, Charity, etc.)
- [ ] Cloud synchronization
- [ ] Progress charts and analytics
- [ ] Multi-language support (English/Arabic)
- [ ] Mobile app version
- [ ] Prayer time integration

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Islamic art inspiration for the color scheme
- Flet framework for making Python GUI development easy
- The open-source community for continuous support

## 📞 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - email@example.com

Project Link: [https://github.com/yourusername/prayer-tracker](https://github.com/yourusername/prayer-tracker)

## 🎉 Support

If you find this project helpful, please give it a ⭐️!

---

<div align="center">
  <b>📿 جزاك الله خيراً | May Allah reward you abundantly</b>
</div>
```

## 📄 requirements.txt

```txt
flet>=0.25.0
```

## 🚀 Quick Start Script (install.sh)

```bash
#!/bin/bash

echo "📿 Installing Prayer Tracker..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing dependencies..."
pip install flet

echo "✅ Installation complete!"
echo "🚀 Run the app with: python3 main.py"
```

## 🚀 Quick Start Script (install.bat for Windows)

```batch
@echo off
echo 📿 Installing Prayer Tracker...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo 📥 Installing dependencies...
pip install flet

echo ✅ Installation complete!
echo 🚀 Run the app with: python main.py
pause
