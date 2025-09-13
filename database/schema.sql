-- All In 2025 Attendee Database Schema
-- PostgreSQL/Supabase

-- Drop existing tables if needed (careful in production!)
-- DROP TABLE IF EXISTS attendee_changes CASCADE;
-- DROP TABLE IF EXISTS attendees CASCADE;
-- DROP TABLE IF EXISTS scraper_runs CASCADE;

-- Table to track scraper runs
CREATE TABLE IF NOT EXISTS scraper_runs (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP NOT NULL UNIQUE,
    run_date DATE NOT NULL,
    total_attendees INTEGER NOT NULL,
    new_attendees INTEGER DEFAULT 0,
    updated_attendees INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Master attendees table
CREATE TABLE IF NOT EXISTS attendees (
    -- Primary identifiers
    id VARCHAR(255) PRIMARY KEY,  -- SwapCard internal ID
    user_id VARCHAR(255) UNIQUE,  -- User ID from platform
    email VARCHAR(255) UNIQUE NOT NULL,
    
    -- Basic information
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    job_title TEXT,
    organization TEXT,
    biography TEXT,
    
    -- Contact information
    mobile_phone VARCHAR(100),
    landline_phone VARCHAR(100),
    website_url TEXT,
    photo_url TEXT,
    
    -- Detail fields (from About Me)
    detail_country VARCHAR(255),
    detail_province VARCHAR(255),
    detail_language VARCHAR(100),
    detail_industry VARCHAR(255),
    detail_org_type VARCHAR(255),
    detail_position_type VARCHAR(255),
    detail_ai_maturity VARCHAR(255),
    detail_category VARCHAR(255),
    detail_interests TEXT,  -- Pipe-separated values
    detail_motivation TEXT,
    
    -- Social media links
    social_linkedin TEXT,
    social_twitter TEXT,
    social_facebook TEXT,
    social_instagram TEXT,
    social_github TEXT,
    social_dribbble TEXT,
    social_pinterest TEXT,
    social_skype VARCHAR(255),
    social_googleplus TEXT,
    social_vimeo TEXT,
    social_youtube TEXT,
    
    -- Tracking fields
    first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_run_id INTEGER REFERENCES scraper_runs(id),
    update_count INTEGER DEFAULT 0,
    
    -- Metadata
    raw_data JSONB,  -- Store complete raw data for reference
    
    -- Indexes will be added below
    CONSTRAINT email_not_empty CHECK (email != '')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_attendees_email ON attendees(email);
CREATE INDEX IF NOT EXISTS idx_attendees_organization ON attendees(organization);
CREATE INDEX IF NOT EXISTS idx_attendees_country ON attendees(detail_country);
CREATE INDEX IF NOT EXISTS idx_attendees_industry ON attendees(detail_industry);
CREATE INDEX IF NOT EXISTS idx_attendees_first_seen ON attendees(first_seen_at);
CREATE INDEX IF NOT EXISTS idx_attendees_last_updated ON attendees(last_updated_at);
CREATE INDEX IF NOT EXISTS idx_attendees_full_name ON attendees(first_name, last_name);

-- Full text search index for biography and interests
CREATE INDEX IF NOT EXISTS idx_attendees_search ON attendees USING GIN(
    to_tsvector('english', 
        COALESCE(first_name, '') || ' ' || 
        COALESCE(last_name, '') || ' ' || 
        COALESCE(organization, '') || ' ' || 
        COALESCE(biography, '') || ' ' || 
        COALESCE(detail_interests, '')
    )
);

-- Optional: Table to track changes over time
CREATE TABLE IF NOT EXISTS attendee_changes (
    id SERIAL PRIMARY KEY,
    attendee_id VARCHAR(255) REFERENCES attendees(id),
    run_id INTEGER REFERENCES scraper_runs(id),
    field_name VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_changes_attendee ON attendee_changes(attendee_id);
CREATE INDEX IF NOT EXISTS idx_changes_run ON attendee_changes(run_id);
CREATE INDEX IF NOT EXISTS idx_changes_timestamp ON attendee_changes(changed_at);

-- Create a view for easy analytics
CREATE OR REPLACE VIEW attendee_statistics AS
SELECT 
    COUNT(DISTINCT id) as total_attendees,
    COUNT(DISTINCT organization) as unique_organizations,
    COUNT(DISTINCT detail_country) as unique_countries,
    COUNT(DISTINCT detail_industry) as unique_industries,
    COUNT(CASE WHEN detail_interests IS NOT NULL AND detail_interests != '' THEN 1 END) as with_interests,
    COUNT(CASE WHEN biography IS NOT NULL AND biography != '' THEN 1 END) as with_biography,
    MIN(first_seen_at) as earliest_attendee,
    MAX(last_updated_at) as latest_update
FROM attendees;

-- Function to update last_updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated_at = CURRENT_TIMESTAMP;
    NEW.update_count = COALESCE(OLD.update_count, 0) + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update last_updated_at
CREATE TRIGGER update_attendees_updated_at 
    BEFORE UPDATE ON attendees 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();