#!/usr/bin/env python3
"""
Reorganize and rename columns in the attendees CSV for better readability
"""

import pandas as pd
from pathlib import Path
import unicodedata
import re
import config

def clean_text(text):
    """Clean text by handling French characters and special characters"""
    if pd.isna(text) or text == '':
        return text
    
    # Convert to string if not already
    text = str(text)
    
    # Common French character replacements for better Excel compatibility
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ô': 'o', 'ö': 'o',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c',
        'î': 'i', 'ï': 'i',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'À': 'A', 'Â': 'A', 'Ä': 'A',
        'Ô': 'O', 'Ö': 'O',
        'Ù': 'U', 'Û': 'U', 'Ü': 'U',
        'Ç': 'C',
        'Î': 'I', 'Ï': 'I',
        'œ': 'oe', 'Œ': 'OE',
        '–': '-', '—': '-',  # Em and en dashes
        '"': '"', '"': '"',  # Smart quotes
        ''': "'", ''': "'",  # Smart single quotes
        '…': '...',  # Ellipsis
    }
    
    # Apply replacements
    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)
    
    # Remove any remaining non-ASCII characters that might cause issues
    # This normalizes unicode and removes combining characters
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if ord(c) < 128 or c.isspace()])
    
    # Clean up extra whitespace
    text = ' '.join(text.split())
    
    return text

def reorganize_csv():
    # Read the CSV
    csv_path = Path(config.ATTENDEES_WITH_DETAILS_CSV)
    df = pd.read_csv(csv_path)
    
    print(f"Original columns: {list(df.columns)}")
    print(f"Total attendees: {len(df)}")
    
    # Define column mapping and order
    column_mapping = {
        # Basic Info
        'firstName': 'First Name',
        'lastName': 'Last Name',
        'jobTitle': 'Job Title',
        'organization': 'Organization',
        
        # Location
        'detail_country': 'Country',
        'detail_province': 'Province/State',
        
        # Professional Details
        'detail_category': 'Attendee Category',
        'detail_industry': 'Industry',
        'detail_org_type': 'Organization Type',
        'detail_position_type': 'Position Type',
        
        # AI Related
        'detail_ai_maturity': 'AI Maturity Level',
        'detail_motivation': 'Event Motivation',
        
        # Other
        'detail_language': 'Language',
        'detail_interests': 'Interests',
        
        # Contact Info (if available)
        'email': 'Email',
        'mobilePhone': 'Mobile Phone',
        'landlinePhone': 'Landline Phone',
        'websiteUrl': 'Website',
        
        # Additional
        'biography': 'Biography',
        'id': 'Attendee ID'
    }
    
    # Define the desired column order
    desired_order = [
        # Primary identification
        'First Name',
        'Last Name',
        'Job Title',
        'Organization',
        
        # Location
        'Country',
        'Province/State',
        
        # Professional categorization
        'Attendee Category',
        'Industry',
        'Organization Type',
        'Position Type',
        
        # AI and Event specific
        'AI Maturity Level',
        'Event Motivation',
        
        # Communication
        'Language',
        'Email',
        'Mobile Phone',
        'Landline Phone',
        'Website',
        
        # Additional info
        'Interests',
        'Biography',
        
        # System ID
        'Attendee ID'
    ]
    
    # Rename columns
    df_renamed = df.rename(columns=column_mapping)
    
    # Select only the columns that exist and are in our desired order
    existing_columns = [col for col in desired_order if col in df_renamed.columns]
    
    # Add any columns that weren't in our mapping (to not lose data)
    remaining_columns = [col for col in df_renamed.columns if col not in existing_columns]
    
    # Combine all columns
    final_column_order = existing_columns + remaining_columns
    
    # Reorder the dataframe
    df_final = df_renamed[final_column_order]
    
    # Apply text cleaning to all string columns
    print("\n🧹 Cleaning text in all columns...")
    for col in df_final.columns:
        if df_final[col].dtype == 'object':  # String columns
            df_final[col] = df_final[col].apply(clean_text)
    
    # Save the reorganized CSV with UTF-8 BOM for better Excel compatibility
    output_path = Path(config.ATTENDEES_ORGANIZED_CSV)
    df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # Also save a version without special characters for maximum compatibility
    excel_safe_path = output_path.parent / f"{output_path.stem}_excel_safe.csv"
    df_final.to_csv(excel_safe_path, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ Reorganized CSV saved to: {output_path}")
    print(f"✅ Excel-safe version saved to: {excel_safe_path}")
    print(f"Final columns ({len(df_final.columns)}): {list(df_final.columns)[:10]}...")
    
    # Show sample of the data
    print("\nSample of reorganized data:")
    print(df_final[['First Name', 'Last Name', 'Organization', 'Country', 'Attendee Category']].head())
    
    # Statistics
    print("\n📊 Statistics:")
    print(f"Total attendees: {len(df_final)}")
    print(f"Countries represented: {df_final['Country'].nunique()}")
    print(f"Industries: {df_final['Industry'].nunique()}")
    print(f"Organizations: {df_final['Organization'].nunique()}")
    
    # Top values
    print("\n🏆 Top 5 Countries:")
    print(df_final['Country'].value_counts().head())
    
    print("\n🏢 Top 5 Industries:")
    print(df_final['Industry'].value_counts().head())
    
    print("\n🎯 AI Maturity Distribution:")
    print(df_final['AI Maturity Level'].value_counts())
    
    return df_final

if __name__ == "__main__":
    reorganize_csv()