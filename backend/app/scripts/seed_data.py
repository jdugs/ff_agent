#!/usr/bin/env python3
"""
Seed the database with sample NFL teams and sources
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.players import NFLTeam
from app.models.sources import Source
from app.config import settings

def create_session():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def seed_nfl_teams(db):
    """Add all NFL teams"""
    teams_data = [
        ('ARI', 'Cardinals', 'Arizona', 'NFC', 'West'),
        ('ATL', 'Falcons', 'Atlanta', 'NFC', 'South'),
        ('BAL', 'Ravens', 'Baltimore', 'AFC', 'North'),
        ('BUF', 'Bills', 'Buffalo', 'AFC', 'East'),
        ('CAR', 'Panthers', 'Carolina', 'NFC', 'South'),
        ('CHI', 'Bears', 'Chicago', 'NFC', 'North'),
        ('CIN', 'Bengals', 'Cincinnati', 'AFC', 'North'),
        ('CLE', 'Browns', 'Cleveland', 'AFC', 'North'),
        ('DAL', 'Cowboys', 'Dallas', 'NFC', 'East'),
        ('DEN', 'Broncos', 'Denver', 'AFC', 'West'),
        ('DET', 'Lions', 'Detroit', 'NFC', 'North'),
        ('GB', 'Packers', 'Green Bay', 'NFC', 'North'),
        ('HOU', 'Texans', 'Houston', 'AFC', 'South'),
        ('IND', 'Colts', 'Indianapolis', 'AFC', 'South'),
        ('JAX', 'Jaguars', 'Jacksonville', 'AFC', 'South'),
        ('KC', 'Chiefs', 'Kansas City', 'AFC', 'West'),
        ('LV', 'Raiders', 'Las Vegas', 'AFC', 'West'),
        ('LAC', 'Chargers', 'Los Angeles', 'AFC', 'West'),
        ('LAR', 'Rams', 'Los Angeles', 'NFC', 'West'),
        ('MIA', 'Dolphins', 'Miami', 'AFC', 'East'),
        ('MIN', 'Vikings', 'Minnesota', 'NFC', 'North'),
        ('NE', 'Patriots', 'New England', 'AFC', 'East'),
        ('NO', 'Saints', 'New Orleans', 'NFC', 'South'),
        ('NYG', 'Giants', 'New York', 'NFC', 'East'),
        ('NYJ', 'Jets', 'New York', 'AFC', 'East'),
        ('PHI', 'Eagles', 'Philadelphia', 'NFC', 'East'),
        ('PIT', 'Steelers', 'Pittsburgh', 'AFC', 'North'),
        ('SF', '49ers', 'San Francisco', 'NFC', 'West'),
        ('SEA', 'Seahawks', 'Seattle', 'NFC', 'West'),
        ('TB', 'Buccaneers', 'Tampa Bay', 'NFC', 'South'),
        ('TEN', 'Titans', 'Tennessee', 'AFC', 'South'),
        ('WAS', 'Commanders', 'Washington', 'NFC', 'East'),
    ]
    
    for team_code, team_name, city, conference, division in teams_data:
        existing = db.query(NFLTeam).filter(NFLTeam.team_code == team_code).first()
        if not existing:
            team = NFLTeam(
                team_code=team_code,
                team_name=team_name,
                city=city,
                conference=conference,
                division=division
            )
            db.add(team)
    
    db.commit()
    print(f"✅ Added NFL teams")

def seed_sources(db):
    """Add initial data sources"""
    sources_data = [
        # Sleeper API sources
        {
            'name': 'Sleeper League Data',
            'source_type': 'league_data',
            'data_method': 'api',
            'specialty': 'league_management',
            'update_frequency': 'hourly',
            'api_base_url': 'https://api.sleeper.app/v1',
            'requires_api_key': False,
            'rate_limit_per_hour': 1000,
            'authentication_type': 'none',
            'base_weight': 1.00
        },
        # FantasyPros API sources
        {
            'name': 'FantasyPros API Consensus',
            'source_type': 'consensus',
            'data_method': 'api',
            'specialty': 'rankings',
            'update_frequency': 'daily',
            'api_base_url': 'https://api.fantasypros.com/v2',
            'requires_api_key': True,
            'api_key_name': 'FANTASYPROS_API_KEY',
            'api_version': 'v2',
            'rate_limit_per_hour': 200,
            'authentication_type': 'api_key',
            'base_weight': 1.00
        },
        # Web scraping sources
        {
            'name': 'FantasyPros Web Rankings',
            'source_type': 'rankings',
            'data_method': 'web_scraping',
            'specialty': 'rankings',
            'update_frequency': 'daily',
            'url_template': 'https://fantasypros.com/nfl/rankings/{position}.php?week={week}&year={year}',
            'url_type': 'templated',
            'base_weight': 0.90
        },
        {
            'name': 'ESPN Fantasy Web',
            'source_type': 'rankings',
            'data_method': 'web_scraping',
            'specialty': 'general',
            'update_frequency': 'daily',
            'base_weight': 0.85
        },
    ]
    
    for source_data in sources_data:
        existing = db.query(Source).filter(Source.name == source_data['name']).first()
        if not existing:
            source = Source(**source_data)
            db.add(source)
    
    db.commit()
    print(f"✅ Added data sources")

def main():
    """Main seeding function"""
    print("🌱 Seeding database with initial data...")
    
    db = create_session()
    try:
        seed_nfl_teams(db)
        seed_sources(db)
        print("\n🎉 Database seeded successfully!")
        
        # Show what was added
        team_count = db.query(NFLTeam).count()
        source_count = db.query(Source).count()
        print(f"📊 Total: {team_count} teams, {source_count} sources")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()