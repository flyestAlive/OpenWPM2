import argparse
from pathlib import Path
from typing import List, Literal

from custom_command import LinkCountingCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.commands.cookie_banner_commands import CookieBannerCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager

AVAILABLE_ACTIONS = ["accept", "reject", "functional", "performance", "marketing"]


def parse_actions(user_arg: List[str] | None) -> List[str]:
    if user_arg:
        return [a.lower() for a in user_arg]
    print("Available cookie banner options: " + ", ".join(AVAILABLE_ACTIONS))
    inp = input("Enter comma separated options to test or 'all': ").strip().lower()
    if inp == "all" or inp == "":
        return AVAILABLE_ACTIONS
    return [x.strip() for x in inp.split(",") if x.strip()]


def run_crawl(selection: str, sites: List[str], headless: bool) -> None:
    display_mode: Literal["native", "headless", "xvfb"] = "native"
    if headless:
        display_mode = "headless"
    manager_params = ManagerParams(num_browsers=1)
    browser_params = [BrowserParams(display_mode=display_mode)]
    for bp in browser_params:
        bp.http_instrument = True
        bp.cookie_instrument = True
        bp.navigation_instrument = True
        bp.js_instrument = True
        bp.dns_instrument = True

    datadir = Path(f"./datadir_{selection}/")
    datadir.mkdir(parents=True, exist_ok=True)
    manager_params.data_directory = datadir
    manager_params.log_path = datadir / "openwpm.log"

    with TaskManager(
        manager_params,
        browser_params,
        SQLiteStorageProvider(datadir / "crawl-data.sqlite"),
        None,
    ) as manager:
        for index, site in enumerate(sites):

            def callback(success: bool, val: str = site) -> None:
                print(
                    f"[{selection}] CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
                )

            command_sequence = CommandSequence(site, site_rank=index, callback=callback)
            command_sequence.append_command(GetCommand(url=site, sleep=3), timeout=60)
            command_sequence.append_command(
                CookieBannerCommand(action=selection, sleep=2), timeout=30
            )
            command_sequence.append_command(LinkCountingCommand())
            manager.execute_command_sequence(command_sequence)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("actions", nargs="*", help="Cookie banner actions to test")
    args = parser.parse_args()

    sites = [
        "http://www.example.com",
        "http://www.princeton.edu",
        "http://citp.princeton.edu/",
    ]

    actions = parse_actions(args.actions)
    for action in actions:
        run_crawl(action, sites, args.headless)


if __name__ == "__main__":
    main()
