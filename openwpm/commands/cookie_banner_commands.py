import logging
import time
from typing import List

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from openwpm.commands.types import BaseCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.socket_interface import ClientSocket


class CookieBannerCommand(BaseCommand):
    """Attempt to interact with cookie banners using a chosen action.

    The command looks for common banner elements such as ``<button>`` and
    ``<input type='button'|type='submit'>``. Additionally it searches for
    checkboxes, radio buttons and elements with a ``role`` of ``button`` or
    ``switch`` as well as ``<label>`` elements. Textual content for matching
    also includes the associated label text for form controls so cookie
    banner options provided via toggles can be triggered.
    """

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
            By.CSS_SELECTOR,
            "input[type='button'], input[type='submit'], input[type='checkbox'], input[type='radio']",
        )
        roles = webdriver.find_elements(By.CSS_SELECTOR, "[role='button'], [role='switch']")
        labels = webdriver.find_elements(By.TAG_NAME, "label")
        return buttons + inputs + roles + labels

    @staticmethod
    def _element_text(webdriver: Firefox, el) -> str:
        """Return textual context for ``el`` used for keyword matching."""
        text = (
            el.get_attribute("textContent")
            or el.get_attribute("value")
            or el.get_attribute("aria-label")
            or el.get_attribute("title")
            or ""
        )

        if not text and el.tag_name.lower() == "input" and el.get_attribute("type") in [
            "checkbox",
            "radio",
        ]:
            elem_id = el.get_attribute("id")
            if elem_id:
                labels = webdriver.find_elements(By.CSS_SELECTOR, f"label[for='{elem_id}']")
                if labels:
                    text = labels[0].get_attribute("textContent") or labels[0].text or ""
            if not text:
                try:
                    parent_label = el.find_element(By.XPATH, "./ancestor::label[1]")
                    text = parent_label.get_attribute("textContent") or parent_label.text or ""
                except Exception:
                    pass

        return text.strip().lower()

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
                text = self._element_text(webdriver, el)
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
