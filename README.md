# All In 2025 Attendee Analytics Platform

Automated scraping and analytics dashboard for All In 2025 conference attendees. This platform collects attendee data daily and provides comprehensive analytics through an interactive Streamlit dashboard.

## 🎯 Features

### Data Collection
- **Automated Daily Scraping**: Collects all attendee information from the All In 2025 platform
- **Detailed Information Fetching**: Retrieves comprehensive "About Me" data for each attendee
- **Smart Rate Limiting**: Respectful API usage with configurable delays
- **Checkpoint System**: Automatic recovery from interruptions
- **Data Organization**: Timestamped runs stored in organized directory structure

### Analytics Dashboard
- **Interactive Visualizations**: Built with Streamlit and Plotly
- **Multi-Tab Analysis**:
  - 🌍 Geographic distribution
  - 🏢 Industry & organization types
  - 👥 Roles & positions
  - 🎯 Interests & motivations
  - 📋 Data quality metrics
- **Search Functionality**: Find attendees by name, email, or organization
- **Export Capabilities**: Download filtered data as CSV

## 📁 Project Structure

```
AllInAttendees/
├── scrape_all_attendees_complete.py   # Main scraper
├── batch_fetch_details.py             # Detailed info fetcher
├── reorganize_csv.py                  # Data cleaning & organization
├── config.py                          # Centralized configuration
├── run_daily_scrape.sh               # Automated daily run script
├── setup_cron.sh                     # Cron job setup
├── refresh_token.py                  # Token management utility
├── cleanup_runs.sh                   # Data cleanup utility
├── run_analytics.sh                  # Launch analytics dashboard
├── streamlit_app/                    # Analytics dashboard
│   ├── app.py                       # Main Streamlit application
│   └── utils/                       # Dashboard utilities
└── data/
    ├── runs/                         # Timestamped data collections
    │   └── YYYY-MM-DD_HHMMSS/      # Individual run data
    └── checkpoints/                  # Recovery checkpoints
```

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r streamlit_app/requirements.txt
pip install requests pandas
```

### 1. Manual Data Collection
```bash
./run_daily_scrape.sh
```

### 2. View Analytics Dashboard
```bash
./run_analytics.sh
# Open browser at http://localhost:8501
```

### 3. Setup Daily Automation
```bash
./setup_cron.sh
# Follow prompts to schedule daily runs
```

## 🔧 Configuration

### Authentication
The system uses JWT tokens that expire after 24 hours. To update:

1. Get a new token from the All In 2025 platform
2. Update using the refresh token utility:
```bash
python3 refresh_token.py --update 'Bearer YOUR_NEW_TOKEN'
```

### Customization
Edit `config.py` to adjust:
- API endpoints
- Rate limiting settings
- File paths
- Authentication headers

## 📊 Data Structure

Each run creates:
- `all_attendees.json` - Raw attendee list
- `all_attendees_with_details.csv` - Enriched data with "About Me" info
- `all_attendees_organized.csv` - Cleaned data with readable column names
- `logs/` - Detailed execution logs

## 📈 Current Statistics

- **2,800+** total attendees (growing daily)
- **25+** countries represented
- **20+** industries
- **1,400+** unique organizations

## 🛠️ Maintenance

### Clean Up Old Runs
```bash
./cleanup_runs.sh
```
Removes incomplete runs and optionally deletes data older than 30 days.

### Check Token Status
```bash
python3 refresh_token.py
```

## 📈 Analytics Dashboard Features

The Streamlit dashboard provides:
- **Real-time Statistics**: Total attendees, companies, countries, industries
- **Distribution Charts**: Interactive bar, pie, and treemap visualizations
- **Data Quality Metrics**: Field completeness analysis
- **Search & Export**: Find and export specific attendee segments

## ⚙️ Workflow

### Automated Daily Collection
```bash
# Runs all three scripts in sequence
./run_daily_scrape.sh
```

### Manual Step-by-Step
```bash
# Step 1: Get all attendees
python scrape_all_attendees_complete.py

# Step 2: Fetch detailed information
python batch_fetch_details.py

# Step 3: Create organized CSV
python reorganize_csv.py
```

## 🔒 Security Notes

- Authentication tokens expire after 24 hours
- Sensitive data is stored locally only
- Use `.gitignore` to exclude data from version control
- Consider encrypting stored tokens for production use

## 📝 Updating Authentication

If you get 401 errors, update the Bearer token:

1. Go to https://app.swapcard.com/event/all-in-2025/people
2. Open Developer Tools (F12) → Network tab
3. Click on any attendee
4. Find the GraphQL request
5. Copy the `authorization` header value
6. Update using: `python3 refresh_token.py --update 'Bearer YOUR_NEW_TOKEN'`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This tool is not officially affiliated with the All In Summit or All In Podcast. Please use responsibly and respect the platform's terms of service.