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
from app.services.league_scoring_service import LeagueScoringService
from app.models.sleeper import PlayerStats
from app.config import settings
from sqlalchemy import and_

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

    async def recalculate_fantasy_points(self, league_id: str, week: int = None, season: str = None):
        """Recalculate fantasy points for a league"""
        season = season or settings.default_season

        try:
            scoring_service = LeagueScoringService(self.db)

            # Build query for stats to recalculate
            query = self.db.query(PlayerStats)

            if week:
                query = query.filter(PlayerStats.week == week)
            if season:
                query = query.filter(PlayerStats.season == season)

            stats_list = query.all()

            print(f"🧮 Recalculating fantasy points for {len(stats_list)} player stats in league {league_id}")

            recalculated_count = 0
            for stat in stats_list:
                result = scoring_service.calculate_and_store_fantasy_points(
                    league_id=league_id,
                    stat_id=stat.stat_id,
                    player_stats=stat,
                    force_recalculate=True
                )
                if result is not None:
                    recalculated_count += 1

            print(f"✅ Recalculated fantasy points for {recalculated_count} player stats")
            return recalculated_count

        except Exception as e:
            print(f"❌ Error recalculating fantasy points: {e}")
            return 0

async def main():
    parser = argparse.ArgumentParser(description='Sync fantasy football data')
    parser.add_argument('command', choices=['stats', 'projections', 'both', 'recalc-points'],
                       help='What to sync')
    parser.add_argument('--week', '-w', type=int,
                       help='NFL week number (required for stats/projections)')
    parser.add_argument('--season', '-s', type=str,
                       help=f'NFL season (default: {settings.default_season})')
    parser.add_argument('--league-id', '-l', type=str,
                       help='League ID (required for recalc-points)')

    args = parser.parse_args()

    # Validation
    if args.command in ['stats', 'projections', 'both'] and not args.week:
        parser.error(f"--week is required for {args.command}")
    if args.command == 'recalc-points' and not args.league_id:
        parser.error("--league-id is required for recalc-points")

    sync = SyncCommands()

    try:
        await sync._setup()

        if args.command == 'stats':
            await sync.sync_stats(args.week, args.season)
        elif args.command == 'projections':
            await sync.sync_projections(args.week, args.season)
        elif args.command == 'both':
            await sync.sync_both(args.week, args.season)
        elif args.command == 'recalc-points':
            await sync.recalculate_fantasy_points(args.league_id, args.week, args.season)

    except KeyboardInterrupt:
        print("\n⏹️  Sync cancelled by user")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        sys.exit(1)
    finally:
        await sync._cleanup()

if __name__ == "__main__":
    asyncio.run(main())