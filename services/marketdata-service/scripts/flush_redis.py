#!/usr/bin/env python3
"""
Utility script to flush Redis price cache
Usage: python scripts/flush_redis.py [--all|--ticker TICKER --exchange EXCHANGE]
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.cache import flush_all_price_cache, invalidate_price_cache, get_cache_stats
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Flush Redis price cache")
    parser.add_argument("--all", action="store_true", help="Flush all price caches")
    parser.add_argument("--ticker", type=str, help="Ticker symbol to flush")
    parser.add_argument("--exchange", type=str, help="Exchange code (required if ticker is provided)")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    
    args = parser.parse_args()
    
    if args.stats:
        stats = await get_cache_stats()
        print(f"Cache Statistics:")
        print(f"  Status: {stats.get('status')}")
        print(f"  Total keys: {stats.get('total_keys', 0)}")
        print(f"  Redis URL: {stats.get('redis_url', 'N/A')}")
        return
    
    if args.all:
        logger.info("Flushing all price caches from Redis...")
        success = await flush_all_price_cache()
        if success:
            print("✅ Successfully flushed all price caches")
        else:
            print("❌ Failed to flush cache")
            sys.exit(1)
    elif args.ticker and args.exchange:
        logger.info(f"Flushing cache for {args.ticker} on {args.exchange}...")
        await invalidate_price_cache(args.ticker, args.exchange)
        print(f"✅ Successfully flushed cache for {args.ticker} on {args.exchange}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
