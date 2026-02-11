"""Scheduler pour le briefing matinal automatique."""

import asyncio
import threading
import time

import schedule

from alita.briefing.generator import run_briefing, get_config_value
from alita.utils.logger import logger


class BriefingScheduler:
    """Gère la planification du briefing matinal."""

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self._thread: threading.Thread | None = None
        self._running = False

    def _job(self):
        """Job exécuté par le scheduler."""
        logger.info("⏰ Déclenchement briefing planifié")
        future = asyncio.run_coroutine_threadsafe(run_briefing(), self._loop)
        try:
            future.result(timeout=300)  # 5 min max
        except Exception as e:
            logger.error("Erreur exécution briefing planifié : %s", e)

    def _run_scheduler(self):
        """Boucle du scheduler dans un thread séparé."""
        while self._running:
            schedule.run_pending()
            time.sleep(30)

    def start(self):
        """Démarre le scheduler."""
        heure = get_config_value("briefing_heure", "07:30")

        schedule.clear()
        schedule.every().day.at(heure).do(self._job)

        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()

        logger.info("Scheduler démarré : briefing quotidien à %s", heure)

    def stop(self):
        """Arrête le scheduler."""
        self._running = False
        schedule.clear()
        logger.info("Scheduler arrêté")

    def reschedule(self, nouvelle_heure: str):
        """Replanifie le briefing à une nouvelle heure."""
        schedule.clear()
        schedule.every().day.at(nouvelle_heure).do(self._job)
        logger.info("Briefing replanifié à %s", nouvelle_heure)
