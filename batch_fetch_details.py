#!/usr/bin/env python3
"""
Batch fetch detailed attendee information using the working fetcher
"""

import json
import csv
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from old.fetch_attendee_details import AttendeeDetailsFetcher
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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