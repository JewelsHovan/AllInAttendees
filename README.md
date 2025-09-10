# All In 2025 Attendee Scraper

A set of scripts to scrape and process attendee information from the All In 2025 event on SwapCard.

## Configuration

All authentication tokens and settings are centralized in `config.py`. Update the Bearer token if it expires.

## Scripts

### 1. `scrape_all_attendees_complete.py`
Fetches the basic list of all attendees.
- Automatically handles pagination
- Outputs: `data/all_attendees_final.json` and CSV

```bash
python scrape_all_attendees_complete.py
```

### 2. `batch_fetch_details.py`
Fetches detailed "About Me" information for each attendee.
- Uses 5 concurrent workers with rate limiting
- Takes ~7 minutes for all attendees
- Outputs: `data/all_attendees_with_details.json` and CSV

```bash
python batch_fetch_details.py
```

### 3. `reorganize_csv.py`
Reorganizes the CSV with human-readable column names and logical ordering.
- Outputs: `data/csv/all_attendees_with_details_organized.csv`

```bash
python reorganize_csv.py
```

## Typical Workflow

```bash
# Step 1: Get all attendees
python scrape_all_attendees_complete.py

# Step 2: Fetch detailed information
python batch_fetch_details.py

# Step 3: Create organized CSV
python reorganize_csv.py
```

## Output Files

- `data/all_attendees_final.json` - Basic attendee list
- `data/all_attendees_with_details.json` - Full attendee details
- `data/csv/all_attendees_with_details_organized.csv` - Final organized spreadsheet

## Statistics (as of last run)

- **2,453** total attendees
- **25** countries represented
- **20** industries
- **1,326** unique organizations

## Updating Authentication

If you get 401 errors, update the Bearer token in `config.py`:

1. Go to https://app.swapcard.com/event/all-in-2025/people
2. Open Developer Tools (F12) → Network tab
3. Click on any attendee
4. Find the GraphQL request
5. Copy the `authorization` header value
6. Update in `config.py`