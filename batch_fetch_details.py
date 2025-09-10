#!/usr/bin/env python3
"""
Batch fetch detailed attendee information using the working fetcher
"""

import json
import csv
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AttendeeDetailsFetcher:
    def __init__(self):
        self.url = config.GRAPHQL_URL
        self.headers = config.HEADERS.copy()
        self.cookies = config.COOKIES.copy()
        self.event_id = config.EVENT_ID

    def build_detail_query(self, person_id: str) -> List[Dict]:
        """Build the GraphQL query to fetch detailed attendee information"""
        return [
            {
                "operationName": "EventPersonDetailsQuery",
                "variables": {
                    "skipMeetings": True,
                    "withEvent": True,
                    "withHostedBuyerView": False,
                    "personId": person_id,
                    "userId": "",
                    "eventId": self.event_id,
                    "viewId": ""
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "b0e088da2df3b4f5c63d871d4f0e628da4fe3b582e5f7478bcbf4fa6421fecd0"
                    }
                }
            },
            {
                "operationName": "PersonUserId",
                "variables": {
                    "personId": person_id
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "109137c30f77f624ffa4263a20e90a0a4fc9e9e7ddade6a7a5039a935b69e1b0"
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
                "variables": {
                    "eventId": self.event_id
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "dd75ad419aef13cd3cc94c3115b8323f05ea5b0bab929b74a953f455a2c873dd"
                    }
                }
            },
            {
                "operationName": "ApplicationProvider_CurrentCommunity",
                "variables": {
                    "communitySlug": "all-in"
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "1d630032bb7429fef5056900473d82b31f00d49569654de2234017d4c0002bec"
                    }
                }
            }
        ]

    def extract_about_me_fields(self, response_data: List[Dict]) -> Dict:
        """Extract the About Me fields from the API response"""
        about_me_data = {}
        
        for result in response_data:
            if 'data' in result and 'person' in result['data']:
                person = result['data']['person']
                
                # Basic info
                about_me_data['id'] = person.get('id', '')
                about_me_data['firstName'] = person.get('firstName', '')
                about_me_data['lastName'] = person.get('lastName', '')
                about_me_data['jobTitle'] = person.get('jobTitle', '')
                about_me_data['organization'] = person.get('organization', '')
                about_me_data['biography'] = person.get('biography', '')
                about_me_data['email'] = person.get('email', '')
                about_me_data['websiteUrl'] = person.get('websiteUrl', '')
                
                # Phone numbers
                about_me_data['mobilePhone'] = person.get('mobilePhone', '')
                about_me_data['landlinePhone'] = person.get('landlinePhone', '')
                
                # Address/Location
                if 'address' in person and person['address']:
                    address = person['address']
                    about_me_data['city'] = address.get('city', '')
                    about_me_data['country'] = address.get('country', '')
                    about_me_data['state'] = address.get('state', '')
                
                # Social links
                if 'socialNetworks' in person and person['socialNetworks']:
                    for network in person['socialNetworks']:
                        network_type = network.get('type', '').lower()
                        profile = network.get('profile', '')
                        # Build full URL for LinkedIn
                        if network_type == 'linkedin' and profile:
                            about_me_data[f'social_{network_type}'] = f'https://www.linkedin.com/in/{profile}'
                        else:
                            about_me_data[f'social_{network_type}'] = profile
                
                # Custom fields from withEvent.fields (About Me section)
                if 'withEvent' in person and person['withEvent']:
                    with_event = person['withEvent']
                    
                    if 'fields' in with_event:
                        for field in with_event['fields']:
                            field_name = field.get('name', '')
                            
                            # Handle different field types
                            if field.get('__typename') == 'Core_MultipleSelectField':
                                # For multiple select fields (like Interests)
                                if 'values' in field and field['values']:
                                    values = [v.get('text', '') for v in field['values']]
                                    field_value = ' | '.join(values)
                                else:
                                    field_value = ''
                            elif field.get('__typename') == 'Core_SelectField':
                                # For single select fields
                                if 'value' in field and field['value']:
                                    field_value = field['value'].get('text', '')
                                else:
                                    field_value = ''
                            else:
                                # For other field types
                                field_value = field.get('value', '')
                            
                            # Map field names to cleaner keys
                            field_mapping = {
                                'Country': 'detail_country',
                                'Province': 'detail_province', 
                                'Category': 'detail_category',
                                'Industry': 'detail_industry',
                                'Organization type': 'detail_org_type',
                                'Organization AI Maturity': 'detail_ai_maturity',
                                'Position type': 'detail_position_type',
                                'Motivation': 'detail_motivation',
                                'Language': 'detail_language',
                                'Interests': 'detail_interests'
                            }
                            
                            # Store the field value
                            if field_name in field_mapping:
                                about_me_data[field_mapping[field_name]] = field_value
                            else:
                                # Store any other fields with cleaned name
                                clean_name = field_name.replace(' ', '_').replace('-', '_').lower()
                                about_me_data[f'field_{clean_name}'] = field_value
                
                break  # Found the person data, no need to continue
        
        return about_me_data

    def fetch_attendee_details(self, person_id: str, save_raw: bool = False) -> Optional[Dict]:
        """Fetch detailed information for a single attendee"""
        try:
            query = self.build_detail_query(person_id)
            response = requests.post(
                self.url,
                headers=self.headers,
                cookies=self.cookies,
                json=query,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Save raw response for debugging
                if save_raw:
                    with open('data/raw_attendee_response.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print("💾 Raw response saved to data/raw_attendee_response.json")
                
                return self.extract_about_me_fields(data)
            else:
                print(f"❌ Failed to fetch details for {person_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching details for {person_id}: {e}")
            return None

class BatchProcessor:
    def __init__(self, num_workers: int = None, delay_seconds: float = None):
        self.fetcher = AttendeeDetailsFetcher()
        self.num_workers = num_workers or config.DEFAULT_WORKERS
        self.delay_seconds = delay_seconds or config.DEFAULT_DELAY_SECONDS
        self.all_results = []
        self.failed_ids = []
        self.processed_count = 0
        self.total_count = 0
        
    def process_attendee(self, attendee_data: Dict) -> Dict:
        """Process a single attendee"""
        person_id = attendee_data['id']
        
        try:
            # Add delay to be respectful to the API
            time.sleep(self.delay_seconds)
            
            # Fetch details using the working fetcher
            details = self.fetcher.fetch_attendee_details(person_id)
            
            if details:
                # Merge with basic data
                merged = {**attendee_data}
                merged.update(details)
                
                self.processed_count += 1
                if self.processed_count % 50 == 0:
                    logger.info(f"Progress: {self.processed_count}/{self.total_count} attendees processed")
                
                return merged
            else:
                logger.warning(f"No data returned for {person_id}")
                self.failed_ids.append(person_id)
                return None
                
        except Exception as e:
            logger.error(f"Error processing {person_id}: {e}")
            self.failed_ids.append(person_id)
            return None
    
    def process_all(self, attendees: List[Dict]):
        """Process all attendees"""
        self.total_count = len(attendees)
        logger.info(f"Starting to fetch details for {self.total_count} attendees with {self.num_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            future_to_attendee = {
                executor.submit(self.process_attendee, attendee): attendee 
                for attendee in attendees
            }
            
            # Process completed tasks
            for future in as_completed(future_to_attendee):
                result = future.result()
                if result:
                    self.all_results.append(result)
        
        logger.info(f"Completed fetching details. Success: {len(self.all_results)}, Failed: {len(self.failed_ids)}")
    
    def save_results(self):
        """Save the results to CSV and JSON files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to CSV
        csv_path = Path(config.ATTENDEES_WITH_DETAILS_CSV)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.all_results:
            # Get all unique fieldnames
            fieldnames = set()
            for result in self.all_results:
                fieldnames.update(result.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.all_results)
            logger.info(f"Saved {len(self.all_results)} attendees to {csv_path}")
        
        # Save to JSON
        json_path = Path(config.ATTENDEES_WITH_DETAILS_JSON)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {json_path}")
        
        # Save failed IDs if any
        if self.failed_ids:
            failed_path = Path(f'data/failed_ids_{timestamp}.json')
            with open(failed_path, 'w') as f:
                json.dump(self.failed_ids, f, indent=2)
            logger.warning(f"Saved {len(self.failed_ids)} failed IDs to {failed_path}")
        
        # Save checkpoint
        checkpoint_path = Path(f'{config.CHECKPOINT_DIR}/details_checkpoint_{timestamp}.json')
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_processed': len(self.all_results),
                'failed_count': len(self.failed_ids),
                'success_rate': f"{(len(self.all_results) / self.total_count * 100):.1f}%" if self.total_count > 0 else "0%"
            }, f, indent=2)

def main():
    # Load existing attendees
    attendees_file = Path(config.ATTENDEES_JSON)
    if not attendees_file.exists():
        logger.error(f"File not found: {attendees_file}")
        return
    
    with open(attendees_file, 'r') as f:
        attendees = json.load(f)
    
    logger.info(f"Loaded {len(attendees)} attendees from {attendees_file}")
    
    # For testing, process just first 10
    # attendees = attendees[:10]
    # logger.info("Testing with first 10 attendees only")
    
    # Initialize processor with 5 workers and 0.5 second delay
    processor = BatchProcessor(num_workers=5, delay_seconds=0.5)
    
    start_time = time.time()
    
    # Process all attendees
    processor.process_all(attendees)
    
    # Save results
    processor.save_results()
    
    elapsed = time.time() - start_time
    logger.info(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    if len(attendees) > 0:
        logger.info(f"Average time per attendee: {elapsed/len(attendees):.2f} seconds")

if __name__ == "__main__":
    main()