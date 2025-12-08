#!/usr/bin/env python3
"""
Utility script to flush Redis price cache for marketdata-service

This script must be run using Poetry to ensure dependencies are available:
  cd services/marketdata-service && poetry run python scripts/flush_redis.py [options]
  
Or use the wrapper script:
  ./services/marketdata-service/scripts/flush_redis.sh [options]
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Get the service directory (parent of scripts directory)
script_dir = Path(__file__).parent
service_dir = script_dir.parent

# Add service directory to path
sys.path.insert(0, str(service_dir))

try:
    from app.core.cache import flush_all_price_cache, invalidate_price_cache, get_cache_stats
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("\n💡 This script must be run using Poetry:")
    print("   cd services/marketdata-service")
    print("   poetry run python scripts/flush_redis.py [options]")
    print("\n   Or use the wrapper script:")
    print("   ./services/marketdata-service/scripts/flush_redis.sh [options]")
    sys.exit(1)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Flush Redis price cache for marketdata-service")
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
