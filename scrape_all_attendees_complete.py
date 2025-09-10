import requests
import json
import csv
import time
from typing import List, Dict, Optional
import config

class SwapCardScraper:
    def __init__(self):
        self.url = config.GRAPHQL_URL
        self.headers = config.HEADERS.copy()
        self.cookies = config.COOKIES.copy()
        
        self.all_attendees = []
        self.unique_ids = set()
        self.total_count = None
        self.max_pages_safety = 200  # Safety limit to prevent infinite loops

    def build_initial_query(self) -> List[Dict]:
        """Build the initial page query (like the browser does on first load)"""
        return [
            {
                "operationName": "ContentViewAdsQuery",
                "variables": {"eventSlug": config.EVENT_SLUG},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "941de0c4ddd8cf381fc8a2d929aa818c2c80bf2e88f190cfb9d45984012698f7"
                    }
                }
            },
            {
                "operationName": "SelfVisibilityOnEvent",
                "variables": {"eventId": config.EVENT_ID},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "9fd18d43cdc5c28cfa23d3d36da590b39a77eaea82311d805733a3092d2d8be5"
                    }
                }
            },
            {
                "operationName": "EventPeopleListViewConnections",
                "variables": {"eventId": config.EVENT_ID},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "6647969f39e9e03ec7b583da22a8bb1180985387cebf5169ff96f41792cbf862"
                    }
                }
            },
            {
                "operationName": "EventAvailabilityFilterListViewQuery",
                "variables": {"viewId": config.VIEW_ID},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "2bf9e6a45af03a5211b8646f0895b0f52969900bc1056ba989154e9ca2e3922c"
                    }
                }
            },
            {
                "operationName": "EventPeopleListViewConnectionQuery",
                "variables": {
                    "viewId": config.VIEW_ID
                    # No cursor for initial request
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "69e1ba85ea607db3bda1d9a656348cb545879099d7ee11aa3e7449d0e4f8a408"
                    }
                }
            },
            {
                "operationName": "SingleCommunityQuery",
                "variables": {},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "0fbbcdbf8bde4a9b8986bb9982f3d875d0ffb56f8e742c28ec9e958cc2729f8c"
                    }
                }
            },
            {
                "operationName": "CurrentEventPersonProviderQuery",
                "variables": {"eventId": config.EVENT_ID},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "dd75ad419aef13cd3cc94c3115b8323f05ea5b0bab929b74a953f455a2c873dd"
                    }
                }
            },
            {
                "operationName": "ApplicationProvider_CurrentCommunity",
                "variables": {"communitySlug": "all-in"},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "1d630032bb7429fef5056900473d82b31f00d49569654de2234017d4c0002bec"
                    }
                }
            }
        ]

    def build_pagination_query(self, cursor: str) -> List[Dict]:
        """Build pagination query with cursor (for subsequent pages)"""
        return [{
            "operationName": "EventPeopleListViewConnectionQuery",
            "variables": {
                "viewId": config.VIEW_ID,
                "endCursor": cursor
            },
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "69e1ba85ea607db3bda1d9a656348cb545879099d7ee11aa3e7449d0e4f8a408"
                }
            }
        }]

    def extract_attendees(self, response_data: List[Dict]) -> tuple[List[Dict], Optional[str], bool, Optional[int]]:
        """Extract attendees from response and return (attendees, next_cursor, has_more, total_count)"""
        attendees = []
        next_cursor = None
        has_more = False
        total_count = None
        
        for result in response_data:
            if 'data' in result:
                # Try different paths where people data might be
                people_data = None
                
                # Path 1: Direct view.people
                if 'view' in result['data'] and 'people' in result['data']['view']:
                    people_data = result['data']['view']['people']
                
                if people_data:
                    # Get total count if available
                    if 'totalCount' in people_data and total_count is None:
                        total_count = people_data['totalCount']
                    
                    if 'nodes' in people_data:
                        for person in people_data['nodes']:
                            person_id = person.get('id', '')
                            
                            # Skip if we've already seen this person
                            if person_id in self.unique_ids:
                                continue
                                
                            self.unique_ids.add(person_id)
                            
                            attendee = {
                                'id': person_id,
                                'firstName': person.get('firstName', ''),
                                'lastName': person.get('lastName', ''),
                                'jobTitle': person.get('jobTitle', ''),
                                'organization': person.get('organization', ''),
                                'photoUrl': person.get('photoUrl', ''),
                                'biography': person.get('biography', ''),
                                'userId': person.get('userId', '')
                            }
                            attendees.append(attendee)
                    
                    # Get pagination info
                    if 'pageInfo' in people_data:
                        page_info = people_data['pageInfo']
                        has_more = page_info.get('hasNextPage', False)
                        if has_more:
                            next_cursor = page_info.get('endCursor')
        
        return attendees, next_cursor, has_more, total_count

    def scrape_all_attendees(self, save_interval: int = 10):
        """Scrape all attendees automatically until no more pages"""
        print("🚀 Starting automated complete scrape...")
        print("   Will automatically fetch all available pages")
        
        # Step 1: Get the first page (initial load, no cursor)
        print("\n📄 Fetching initial page (attendees 1-30)...")
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                cookies=self.cookies,
                json=self.build_initial_query(),
                timeout=30
            )
            
            if response.status_code == 200:
                attendees, cursor, has_more, total_count = self.extract_attendees(response.json())
                
                # Store the total count if we got it
                if total_count:
                    self.total_count = total_count
                    print(f"📊 Total attendees available: {self.total_count}")
                    estimated_pages = (self.total_count // 30) + (1 if self.total_count % 30 else 0)
                    print(f"📄 Estimated pages to fetch: {estimated_pages}")
                
                if attendees:
                    self.all_attendees.extend(attendees)
                    print(f"✅ Found {len(attendees)} attendees on initial page")
                    print(f"   First: {attendees[0]['firstName']} {attendees[0]['lastName']}")
                    print(f"   Last: {attendees[-1]['firstName']} {attendees[-1]['lastName']}")
                    if cursor:
                        print(f"   Next cursor: {cursor[:50]}...")
            else:
                print(f"❌ Failed to get initial page: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching initial page: {e}")
            return []
        
        # Step 2: Paginate through remaining pages automatically
        page_num = 2
        consecutive_empty = 0
        
        while cursor and has_more and page_num <= self.max_pages_safety:
            print(f"\n📄 Fetching page {page_num}...")
            print(f"   Using cursor: {cursor[:50]}...")
            
            try:
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    cookies=self.cookies,
                    json=self.build_pagination_query(cursor),
                    timeout=30
                )
                
                if response.status_code == 200:
                    attendees, next_cursor, has_more, _ = self.extract_attendees(response.json())
                    
                    if attendees:
                        consecutive_empty = 0
                        self.all_attendees.extend(attendees)
                        unique_count = len(self.unique_ids)
                        
                        # Calculate progress
                        if self.total_count:
                            progress = (unique_count / self.total_count) * 100
                            print(f"✅ Found {len(attendees)} new attendees")
                            print(f"📊 Progress: {unique_count}/{self.total_count} ({progress:.1f}%)")
                        else:
                            print(f"✅ Found {len(attendees)} new attendees")
                            print(f"📊 Total collected: {unique_count}")
                        
                        # Save checkpoint periodically
                        if page_num % save_interval == 0:
                            self.save_checkpoint(f"data/checkpoints/checkpoint_{page_num}.json")
                            print(f"💾 Checkpoint saved")
                        
                        cursor = next_cursor
                    else:
                        consecutive_empty += 1
                        print(f"⚠️ No new attendees on page {page_num}")
                        if consecutive_empty >= 3:
                            print("No new data for 3 consecutive pages, stopping.")
                            break
                    
                    # Check if we've reached the expected total
                    if self.total_count and len(self.unique_ids) >= self.total_count:
                        print(f"\n✅ Reached expected total of {self.total_count} attendees!")
                        break
                        
                else:
                    print(f"❌ Request failed: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"❌ Error on page {page_num}: {e}")
                break
            
            page_num += 1
            time.sleep(0.3)  # Respectful delay
        
        if not has_more or not cursor:
            print("\n🎉 Reached the last page!")
        elif page_num > self.max_pages_safety:
            print(f"\n⚠️ Reached safety limit of {self.max_pages_safety} pages")
        
        return self.all_attendees

    def save_checkpoint(self, filename: str):
        """Save current progress to a checkpoint file"""
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'attendees': self.all_attendees,
                'unique_count': len(self.unique_ids),
                'total_expected': self.total_count,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2, ensure_ascii=False)

    def save_to_csv(self, filename: str = "data/csv/all_attendees_final.csv"):
        """Save all attendees to CSV file"""
        if not self.all_attendees:
            print("No attendees to save")
            return
        
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        fieldnames = ['id', 'firstName', 'lastName', 'jobTitle', 'organization', 'photoUrl', 'biography', 'userId']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.all_attendees)
        
        print(f"💾 Saved {len(self.all_attendees)} attendees to {filename}")

    def save_to_json(self, filename: str = None):
        if filename is None:
            filename = config.ATTENDEES_JSON
        """Save all attendees to JSON file"""
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_attendees, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(self.all_attendees)} attendees to {filename}")

    def print_summary(self):
        """Print summary statistics"""
        if not self.all_attendees:
            print("No attendees collected")
            return
        
        print("\n" + "="*50)
        print("📈 FINAL SUMMARY")
        print("="*50)
        print(f"Total attendees collected: {len(self.all_attendees)}")
        print(f"Unique attendees: {len(self.unique_ids)}")
        
        if self.total_count:
            print(f"Expected total: {self.total_count}")
            print(f"Collection rate: {(len(self.unique_ids)/self.total_count)*100:.1f}%")
        
        # Count unique organizations
        organizations = set(a.get('organization', '') for a in self.all_attendees if a.get('organization'))
        print(f"Unique organizations: {len(organizations)}")
        
        # Show first and last attendees
        print("\n👥 First 5 attendees:")
        for i, attendee in enumerate(self.all_attendees[:5], 1):
            name = f"{attendee.get('firstName', '')} {attendee.get('lastName', '')}".strip()
            org = attendee.get('organization', 'N/A')
            print(f"{i}. {name:30} - {org}")
        
        print("\n👥 Last 5 attendees:")
        for i, attendee in enumerate(self.all_attendees[-5:], 1):
            name = f"{attendee.get('firstName', '')} {attendee.get('lastName', '')}".strip()
            org = attendee.get('organization', 'N/A')
            print(f"{i}. {name:30} - {org}")


if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    print("="*60)
    print(f"ALL IN 2025 - ATTENDEE SCRAPER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    scraper = SwapCardScraper()
    
    # Scrape all attendees automatically
    attendees = scraper.scrape_all_attendees(save_interval=10)
    
    if attendees:
        # Save to both CSV and JSON with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save with timestamp
        scraper.save_to_csv(f"data/csv/all_attendees_{timestamp}.csv")
        scraper.save_to_json(f"data/all_attendees_{timestamp}.json")
        
        # Also save as "latest" for easy access
        scraper.save_to_csv("data/csv/all_attendees_latest.csv")
        scraper.save_to_json("data/all_attendees_latest.json")
        
        # Print summary
        scraper.print_summary()
        
        print(f"\n✅ Scraping completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("❌ No attendees were collected")
        
    print("="*60)