#!/usr/bin/env python3
"""
Centralized sync commands for fantasy football data

Usage examples:
    python sync_commands.py stats --week 3
    python sync_commands.py projections --week 3
    python sync_commands.py both --week 3
    python sync_commands.py stats --week 3 --season 2023
"""

import asyncio
import argparse
import sys
from app.database import get_db
from app.services.stats_service import StatsService
from app.config import settings

class SyncCommands:
    def __init__(self):
        self.db = None
        self.service = None

    async def _setup(self):
        """Initialize database connection and service"""
        self.db = next(get_db())
        self.service = StatsService(self.db)

    async def _cleanup(self):
        """Clean up connections"""
        if self.service:
            await self.service.close()
        if self.db:
            self.db.close()

    async def sync_stats(self, week: int, season: str = None):
        """Sync player stats for the specified week"""
        season = season or settings.default_season

        try:
            print(f"🏈 Syncing player stats for Week {week}, {season} season...")
            count = await self.service.sync_player_stats(week=week, season=season)
            print(f"✅ Successfully synced {count} player stats")
            return count
        except Exception as e:
            print(f"❌ Error syncing stats: {e}")
            return 0

    async def sync_projections(self, week: int, season: str = None):
        """Sync player projections for the specified week"""
        season = season or settings.default_season

        try:
            print(f"📊 Syncing player projections for Week {week}, {season} season...")
            count = await self.service.sync_player_projections(week=week, season=season)
            print(f"✅ Successfully synced {count} player projections")
            return count
        except Exception as e:
            print(f"❌ Error syncing projections: {e}")
            return 0

    async def sync_both(self, week: int, season: str = None):
        """Sync both stats and projections"""
        season = season or settings.default_season

        print(f"🔄 Syncing both stats and projections for Week {week}, {season} season")

        stats_count = await self.sync_stats(week, season)
        projections_count = await self.sync_projections(week, season)

        total = stats_count + projections_count
        print(f"\n🎉 Sync complete! Total records synced: {total}")
        return total

async def main():
    parser = argparse.ArgumentParser(description='Sync fantasy football data')
    parser.add_argument('command', choices=['stats', 'projections', 'both'],
                       help='What to sync')
    parser.add_argument('--week', '-w', type=int, required=True,
                       help='NFL week number')
    parser.add_argument('--season', '-s', type=str,
                       help=f'NFL season (default: {settings.default_season})')

    args = parser.parse_args()

    sync = SyncCommands()

    try:
        await sync._setup()

        if args.command == 'stats':
            await sync.sync_stats(args.week, args.season)
        elif args.command == 'projections':
            await sync.sync_projections(args.week, args.season)
        elif args.command == 'both':
            await sync.sync_both(args.week, args.season)

    except KeyboardInterrupt:
        print("\n⏹️  Sync cancelled by user")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        sys.exit(1)
    finally:
        await sync._cleanup()

if __name__ == "__main__":
    asyncio.run(main())