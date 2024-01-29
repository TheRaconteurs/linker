import time
import asyncio
import schedule
from script import LecturesBot


def run_bot():
    asyncio.run(LecturesBot().first_auth())


def main():
    schedule.every().hour.do(run_bot)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # main()  # run loop
    run_bot()  # run once
