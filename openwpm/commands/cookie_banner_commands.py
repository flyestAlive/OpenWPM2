import logging
import time
from typing import List

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


class CookieBannerCommand(BaseCommand):
    """Attempt to interact with cookie banners using a chosen action."""

    def __init__(self, action: str, sleep: float = 1.0) -> None:
        self.action = action.lower()
        self.sleep = sleep
        self.logger = logging.getLogger("openwpm")

    def __repr__(self) -> str:  # pragma: no cover - just for logging
        return f"CookieBannerCommand({self.action})"

    @staticmethod
    def _find_elements(webdriver: Firefox) -> List:
        buttons = webdriver.find_elements(By.TAG_NAME, "button")
        inputs = webdriver.find_elements(
            By.CSS_SELECTOR, "input[type='button'], input[type='submit']"
        )
        return buttons + inputs

    def execute(
        self,
        webdriver: Firefox,
        browser_params: BrowserParams,
        manager_params: ManagerParams,
        extension_socket: ClientSocket,
    ) -> None:
        keywords_map = {
            "accept": ["accept", "akzeptieren", "zustimmen", "allow", "agree"],
            "reject": ["reject", "ablehnen", "decline"],
            "functional": ["functional", "essentiell", "necessary", "notwendig"],
            "performance": ["performance", "statistics"],
            "marketing": ["marketing", "advertising", "ads"],
        }
        keywords = keywords_map.get(self.action, [self.action])
        try:
            for el in self._find_elements(webdriver):
                text = (
                    el.get_attribute("textContent") or el.get_attribute("value") or ""
                ).lower()
                if any(k in text for k in keywords):
                    try:
                        el.click()
                        time.sleep(self.sleep)
                        return
                    except Exception as e:  # pragma: no cover - log only
                        self.logger.error("Error clicking cookie banner: %s", e)
                        return
        except Exception as e:  # pragma: no cover - log only
            self.logger.error("Error finding cookie banner elements: %s", e)
            return
