#!/usr/bin/env python3
"""
Database setup script for Fantasy Football Dashboard
Run this to initialize the database with tables and initial data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from backend.app.models import Base
from backend.app.config import settings
from backend.app.models.sources import Source
from backend.app.models.players import NFLTeam
from backend.app.database import SessionLocal

def create_database():
    """Create database tables"""
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")

def populate_initial_data():
    """Populate database with initial reference data"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_teams = db.query(NFLTeam).count()
        if existing_teams > 0:
            print("📊 Initial data already exists, skipping population")
            return
        
        # Add NFL teams
        nfl_teams = [
            NFLTeam(team_code='ARI', team_name='Cardinals', city='Arizona', conference='NFC', division='West'),
            NFLTeam(team_code='ATL', team_name='Falcons', city='Atlanta', conference='NFC', division='South'),
            NFLTeam(team_code='BAL', team_name='Ravens', city='Baltimore', conference='AFC', division='North'),
            NFLTeam(team_code='BUF', team_name='Bills', city='Buffalo', conference='AFC', division='East'),
            NFLTeam(team_code='CAR', team_name='Panthers', city='Carolina', conference='NFC', division='South'),
            NFLTeam(team_code='CHI', team_name='Bears', city='Chicago', conference='NFC', division='North'),
            NFLTeam(team_code='CIN', team_name='Bengals', city='Cincinnati', conference='AFC', division='North'),
            NFLTeam(team_code='CLE', team_name='Browns', city='Cleveland', conference='AFC', division='North'),
            NFLTeam(team_code='DAL', team_name='Cowboys', city='Dallas', conference='NFC', division='East'),
            NFLTeam(team_code='DEN', team_name='Broncos', city='Denver', conference='AFC', division='West'),
            NFLTeam(team_code='DET', team_name='Lions', city='Detroit', conference='NFC', division='North'),
            NFLTeam(team_code='GB', team_name='Packers', city='Green Bay', conference='NFC', division='North'),
            NFLTeam(team_code='HOU', team_name='Texans', city='Houston', conference='AFC', division='South'),
            NFLTeam(team_code='IND', team_name='Colts', city='Indianapolis', conference='AFC', division='South'),
            NFLTeam(team_code='JAX', team_name='Jaguars', city='Jacksonville', conference='AFC', division='South'),
            NFLTeam(team_code='KC', team_name='Chiefs', city='Kansas City', conference='AFC', division='West'),
            NFLTeam(team_code='LV', team_name='Raiders', city='Las Vegas', conference='AFC', division='West'),
            NFLTeam(team_code='LAC', team_name='Chargers', city='Los Angeles', conference='AFC', division='West'),
            NFLTeam(team_code='LAR', team_name='Rams', city='Los Angeles', conference='NFC', division='West'),
            NFLTeam(team_code='MIA', team_name='Dolphins', city='Miami', conference='AFC', division='East'),
            NFLTeam(team_code='MIN', team_name='Vikings', city='Minnesota', conference='NFC', division='North'),
            NFLTeam(team_code='NE', team_name='Patriots', city='New England', conference='AFC', division='East'),
            NFLTeam(team_code='NO', team_name='Saints', city='New Orleans', conference='NFC', division='South'),
            NFLTeam(team_code='NYG', team_name='Giants', city='New York', conference='NFC', division='East'),
            NFLTeam(team_code='NYJ', team_name='Jets', city='New York', conference='AFC', division='East'),
            NFLTeam(team_code='PHI', team_name='Eagles', city='Philadelphia', conference='NFC', division='East'),
            NFLTeam(team_code='PIT', team_name='Steelers', city='Pittsburgh', conference='AFC', division='North'),
            NFLTeam(team_code='SF', team_name='49ers', city='San Francisco', conference='NFC', division='West'),
            NFLTeam(team_code='SEA', team_name='Seahawks', city='Seattle', conference='NFC', division='West'),
            NFLTeam(team_code='TB', team_name='Buccaneers', city='Tampa Bay', conference='NFC', division='South'),
            NFLTeam(team_code='TEN', team_name='Titans', city='Tennessee', conference='AFC', division='South'),
            NFLTeam(team_code='WAS', team_name='Commanders', city='Washington', conference='NFC', division='East'),
        ]
        
        db.add_all(nfl_teams)
        
        # Add initial sources
        sources = [
            # Sleeper API sources
            Source(
                name='Sleeper League Data',
                source_type='league_data',
                data_method='api',
                specialty='league_management',
                update_frequency='hourly',
                api_base_url='https://api.sleeper.app/v1',
                requires_api_key=False,
                rate_limit_per_hour=1000,
                authentication_type='none',
                base_weight=1.00
            ),
            Source(
                name='Sleeper Player Data',
                source_type='rankings',
                data_method='api',
                specialty='player_data',
                update_frequency='daily',
                api_base_url='https://api.sleeper.app/v1',
                requires_api_key=False,
                rate_limit_per_hour=1000,
                authentication_type='none',
                base_weight=0.85
            ),
            
            # FantasyPros API v2 sources
            Source(
                name='FantasyPros API Consensus',
                source_type='consensus',
                data_method='api',
                specialty='rankings',
                update_frequency='daily',
                api_base_url='https://api.fantasypros.com/v2',
                requires_api_key=True,
                api_key_name='FANTASYPROS_API_KEY',
                api_version='v2',
                rate_limit_per_hour=200,
                authentication_type='api_key',
                base_weight=1.00
            ),
            Source(
                name='FantasyPros API Projections',
                source_type='rankings',
                data_method='api',
                specialty='projections',
                update_frequency='daily',
                api_base_url='https://api.fantasypros.com/v2',
                requires_api_key=True,
                api_key_name='FANTASYPROS_API_KEY',
                api_version='v2',
                rate_limit_per_hour=200,
                authentication_type='api_key',
                base_weight=0.95
            ),
            
            # Web scraping sources
            Source(
                name='FantasyPros Web Rankings',
                source_type='rankings',
                data_method='web_scraping',
                specialty='rankings',
                update_frequency='daily',
                url_template='https://fantasypros.com/nfl/rankings/{position}.php?week={week}&year={year}&scoring={scoring}',
                url_wildcards={
                    "required": ["position", "week", "year"],
                    "optional": ["scoring"],
                    "defaults": {"scoring": "PPR"},
                    "validation": {
                        "week": {"type": "int", "min": 1, "max": 18},
                        "year": {"type": "int", "min": 2020, "max": 2030},
                        "position": {"type": "enum", "values": ["qb", "rb", "wr", "te", "k", "dst"]},
                        "scoring": {"type": "enum", "values": ["STD", "HALF", "PPR"]}
                    }
                },
                url_type='templated',
                base_weight=0.90
            ),
            Source(
                name='ESPN Fantasy Web',
                source_type='rankings',
                data_method='web_scraping',
                specialty='general',
                update_frequency='daily',
                url_template='https://fantasy.espn.com/football/players/projections?scoringPeriodId={week}&seasonId={year}',
                url_wildcards={
                    "required": ["week", "year"],
                    "optional": ["leagueId"],
                    "defaults": {"leagueId": "0"}
                },
                url_type='templated',
                base_weight=0.85
            ),
            Source(
                name='Rotoworld News',
                source_type='news',
                data_method='web_scraping',
                specialty='injury_news',
                update_frequency='realtime',
                base_weight=0.90
            ),
        ]
        
        db.add_all(sources)
        db.commit()
        
        print("✅ Initial data populated successfully")
        print(f"   - Added {len(nfl_teams)} NFL teams")
        print(f"   - Added {len(sources)} data sources")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error populating initial data: {e}")
        raise
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🏈 Setting up Fantasy Football Dashboard Database...")
    
    try:
        create_database()
        populate_initial_data()
        print("\n🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and update with your API keys")
        print("2. Run: uvicorn app.main:app --reload")
        print("3. Visit: http://localhost:8000/docs for API documentation")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()