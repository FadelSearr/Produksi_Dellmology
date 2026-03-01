"""
Model Retrain Scheduler
Automated model retraining at scheduled intervals
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Callable

logger = logging.getLogger(__name__)


def schedule_retraining(job_func: Callable, schedule: str = "0 17 * * 1-5"):
    """
    Schedule model retraining
    
    Args:
        job_func: Function to execute
        schedule: Cron expression (default: 5 PM weekdays)
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_func, 'cron', hour=17, minute=0, day_of_week='0-4')
    scheduler.start()
    logger.info(f"Retraining scheduler started with schedule: {schedule}")
