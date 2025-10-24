from datetime import datetime, timedelta, timezone
import logging

from Sources.ConfigLoader import ParserConfig
from Sources.Pipeline import Pipeline

log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S'
    )

    config = ParserConfig()
    
    yesterday = config.TARGET_DATE or (datetime.now(timezone.utc).date() + timedelta(days = -1)).isoformat()
    today     = config.TARGET_DATE or (datetime.now(timezone.utc).date() + timedelta(days =  0)).isoformat()

    Pipeline(config).Run(day = yesterday, nextDay = today)
