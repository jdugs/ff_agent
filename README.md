# Fantasy Football Dashboard 🏈

A comprehensive fantasy football data aggregation and analysis platform that combines real-time data from multiple sources with your actual Sleeper league data to provide intelligent rankings, projections, and start/sit recommendations.

## Features

- 🏆 **Real League Integration** - Sync your actual Sleeper fantasy leagues and rosters
- 📊 **Multi-Source Rankings** - Aggregate rankings from FantasyPros, ESPN, and other sources
- 🤖 **Smart Recommendations** - AI-powered start/sit advice based on consensus data
- 📰 **News Integration** - Real-time player news and injury updates
- 📈 **Performance Tracking** - Source reliability scoring and historical accuracy
- 🎯 **Team Dashboard** - Personalized view of your team with actionable insights

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM with PostgreSQL database
- **Celery** - Background task processing
- **Redis** - Caching and task queue
- **httpx** - Async HTTP client for API integrations

### Frontend (Coming Soon)
- **React 18** with TypeScript
- **Next.js 14** - Full-stack React framework
- **TailwindCSS** - Utility-first styling
- **Recharts** - Data visualization

### Data Sources
- **Sleeper API** - Real fantasy league data
- **FantasyPros API** - Expert rankings and projections
- **Web Scraping** - ESPN, Yahoo, and other fantasy sources

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd fantasy-football-dashboard

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your API keys and settings:

```bash
# Database
DATABASE_URL=postgresql://fantasy_user:fantasy_password@postgres:5432/fantasy_football

# API Keys
FANTASYPROS_API_KEY=your_fantasypros_api_key_here

# Sleeper Configuration  
SLEEPER_USER_ID=your_sleeper_user_id
SLEEPER_LEAGUE_ID=your_current_league_id

# Season Configuration
DEFAULT_SEASON=2025
AVAILABLE_SEASONS=2023,2024,2025

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 3. Start Services

```bash
# Start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Initialize Database

```bash
# Seed initial data (NFL teams and sources)
docker-compose exec backend python app/scripts/seed_data.py
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **Database Admin**: http://localhost:5050 (pgAdmin)
  - Email: `admin@admin.com`
  - Password: `admin`

## Sleeper Integration Setup

### 1. Find Your Sleeper User ID

```bash
# Replace YOUR_USERNAME with your Sleeper username
curl "http://localhost:8000/api/v1/sleeper/user/search/YOUR_USERNAME"
```

Save the `user_id` from the response.

### 2. Sync Your Leagues

```bash
# Replace USER_ID with your Sleeper user ID
curl -X POST "http://localhost:8000/api/v1/sleeper/user/USER_ID/sync?season=2025"
```

### 3. View Your Leagues

```bash
curl "http://localhost:8000/api/v1/sleeper/user/USER_ID/leagues"
```

### 4. Sync League Details

```bash
# Replace LEAGUE_ID with your league ID
curl -X POST "http://localhost:8000/api/v1/sleeper/league/LEAGUE_ID/sync?user_id=USER_ID"
```

### 5. View Your Team Dashboard

```bash
curl "http://localhost:8000/api/v1/team/LEAGUE_ID/USER_ID"
```

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Player Data

- `GET /api/v1/players` - List all players
- `GET /api/v1/players/{player_id}` - Get specific player
- `GET /api/v1/players/{player_id}/rankings` - Player rankings

### Sources

- `GET /api/v1/sources` - List data sources
- `GET /api/v1/sources/{source_id}` - Get specific source

### Dashboard

- `GET /api/v1/dashboard/stats` - Overall statistics
- `GET /api/v1/dashboard/top-players` - Top ranked players
- `GET /api/v1/dashboard/sleeper/leagues` - Sleeper league stats

### Sleeper Integration

- `GET /api/v1/sleeper/user/search/{username}` - Find user by username
- `POST /api/v1/sleeper/user/{user_id}/sync` - Sync user leagues
- `GET /api/v1/sleeper/user/{user_id}/leagues` - Get user's leagues
- `POST /api/v1/sleeper/league/{league_id}/sync` - Sync league data
- `GET /api/v1/sleeper/league/{league_id}/rosters` - Get league rosters

### Team Dashboard

- `GET /api/v1/team/{league_id}/{user_id}` - Comprehensive team dashboard
- `GET /api/v1/team/debug/{league_id}/{user_id}` - Debug team access

## Database Schema

The application uses a comprehensive database schema with the following key tables:

### Core Tables
- `players` - NFL player information
- `nfl_teams` - NFL team data
- `sources` - Data source configuration
- `rankings` - Player rankings from all sources
- `player_projections` - Statistical projections
- `news_events` - Player news and updates

### Sleeper Integration
- `sleeper_leagues` - Synced league information
- `sleeper_rosters` - Team rosters and records
- `sleeper_players` - Sleeper player database
- `sleeper_matchups` - Weekly matchup data
- `sleeper_player_stats` - Player statistics and fantasy points
- `sleeper_player_projections` - Player projections

### Analytics
- `source_performance_tracking` - Source accuracy metrics
- `player_id_mappings` - Player ID mapping between systems
- `api_call_logs` - API usage tracking

## Database Migrations

The application uses Alembic for database schema migrations.

### Running Migrations in Docker

When you make changes to database models, you'll need to create and apply migrations:

#### 1. Generate a New Migration

```bash
# Enter the backend container
docker exec -it <backend_container_name> bash

# Generate migration file
alembic revision --autogenerate -m "Description of your changes"
```

Or run directly without entering the container:
```bash
docker-compose exec backend alembic revision --autogenerate -m "Description of your changes"
```

#### 2. Review the Migration

Check the generated migration file in `backend/alembic/versions/` to ensure it contains the expected changes.

#### 3. Apply the Migration

```bash
# Apply the migration
docker exec -it <backend_container_name> alembic upgrade head

# Or directly
docker-compose exec backend alembic upgrade head
```

#### 4. Verify Changes

Check your database using pgAdmin or connect directly to verify the schema changes were applied.

### Migration Commands Reference

```bash
# Check current migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Upgrade to specific revision
docker-compose exec backend alembic upgrade <revision_id>

# Downgrade to previous revision
docker-compose exec backend alembic downgrade -1

# Show pending migrations
docker-compose exec backend alembic show <revision_id>
```

### Local Development Migrations

If running locally without Docker, update your `alembic.ini` to use `localhost` instead of `postgres` for the database host:

```ini
sqlalchemy.url = postgresql://fantasy_user:fantasy_password@localhost:5432/fantasy_football
```

Then run migrations normally:
```bash
cd backend
alembic revision --autogenerate -m "Your change description"
alembic upgrade head
```

## Development

### Local Development (Without Docker)

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Start Services**
```bash
# Start PostgreSQL and Redis locally
brew services start postgresql redis  # macOS
# OR
sudo service postgresql start && sudo service redis-server start  # Linux
```

3. **Run Application**
```bash
python scripts/run_local.py
```

### Adding New Data Sources

1. **Create Source Entry**
```python
# Add to seed_data.py or via API
source = Source(
    name="New Source",
    source_type="rankings",
    data_method="web_scraping",  # or "api"
    specialty="rankings",
    update_frequency="daily",
    url_template="https://example.com/rankings/{week}",
    base_weight=0.85
)
```

2. **Create Scraper/API Client**
```python
# backend/app/integrations/new_source_api.py
# or
# backend/app/scrapers/new_source_scraper.py
```

3. **Add Background Tasks**
```python
# backend/app/tasks/scraping_tasks.py
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | See docker-compose.yml |
| `FANTASYPROS_API_KEY` | FantasyPros API key | No | "" |
| `SLEEPER_USER_ID` | Your Sleeper user ID | No | "" |
| `SLEEPER_LEAGUE_ID` | Your primary league ID | No | "" |
| `DEFAULT_SEASON` | Default NFL season | No | "2025" |
| `REDIS_URL` | Redis connection string | Yes | redis://redis:6379/0 |
| `DEBUG` | Enable debug mode | No | true |

## Database Access

### pgAdmin Access
- URL: http://localhost:5050
- Email: `admin@admin.com`
- Password: `admin`

### Database Connection
- Host: `localhost` (or `postgres` from within Docker)
- Port: `5432`
- Database: `fantasy_football`
- Username: `fantasy_user`
- Password: `fantasy_password`

### Useful SQL Queries

```sql
-- Check data sync status
SELECT name, last_scraped, consecutive_failures FROM sources;

-- View your team
SELECT sp.full_name, sp.position, sp.team 
FROM sleeper_rosters sr
JOIN sleeper_players sp ON sp.sleeper_player_id = ANY(sr.player_ids::text[])
WHERE sr.league_id = 'YOUR_LEAGUE_ID' AND sr.owner_id = 'YOUR_SLEEPER_USER_ID';

-- Check ranking coverage
SELECT p.name, COUNT(r.ranking_id) as ranking_count
FROM players p
LEFT JOIN rankings r ON p.player_id = r.player_id
GROUP BY p.player_id, p.name
ORDER BY ranking_count DESC;
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all imports use full paths: `from app.models.players import Player`
   - Check that `__init__.py` files exist in all directories

2. **Database Connection**
   - Verify PostgreSQL is running: `docker-compose ps`
   - Check connection string in `.env`

3. **Sleeper Sync Fails**
   - Verify username exists on Sleeper
   - Check if user has leagues for the specified season
   - Review API logs: `SELECT * FROM api_call_logs ORDER BY timestamp DESC`

4. **No Rosters Found**
   - Ensure you've run league sync, not just user sync
   - Check `sleeper_rosters` table has data

### Logs and Debugging

```bash
# View backend logs
docker-compose logs backend

# View all service logs
docker-compose logs

# Check specific service
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f backend
```

### Reset Database

```bash
# Stop services and remove volumes
docker-compose down -v

# Rebuild and restart
docker-compose up --build

# Re-seed data
docker-compose exec backend python app/scripts/seed_data.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] Frontend React dashboard
- [ ] FantasyPros API integration
- [ ] ESPN web scraping
- [ ] Advanced analytics and trends
- [ ] Mobile app
- [ ] Multi-league management
- [ ] Trade analyzer
- [ ] Waiver wire recommendations
- [ ] Playoff projections

## Support

For questions and support:
- Check the [API documentation](http://localhost:8000/docs)
- Review the troubleshooting section above
- Open an issue on GitHub