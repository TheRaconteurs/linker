import datetime
import os
import re
import telebot
from pyppeteer import launch
from pyppeteer import chromium_downloader
from dotenv import load_dotenv


class LecturesBot:
    def __init__(self):
        a = chromium_downloader.chromium_executable()
        self.browser = None
        self.page = None

        load_dotenv("secret.env")
        self.token = os.getenv("TOKEN")
        self.login = os.getenv("LOGIN")
        self.password = os.getenv("PASSWORD")
        self.url = os.getenv("URL")
        # self.url = "https://ies.unitech-mo.ru/journal?group="

        self.utc = datetime.datetime.today()
        self.diff = datetime.timedelta(hours=3)  # Europe/Moscow timezone
        self.moscow_tz = self.utc + self.diff
        self.weekday = self.moscow_tz.strftime("%u")
        self.today = self.moscow_tz.strftime("%A")

    async def first_auth(self):
        await self.page.click(".log_in_link")

        await self.page.type("input.form-control:nth-child(1)", self.login)
        await self.page.type("input.form-control:nth-child(2)", self.password)
        await self.page.click(".stay_in_system_check_wraper > label:nth-child(2)")

        await self.page.click('#main_login_link')
        await self.page.waitFor(1300)

    async def auth(self):
        t = r"C:\Users\Stepan\AppData\Local\Chromium\User Data"

        self.browser = await launch({"headless": True, "userDataDir": t}, args=['--no-sandbox'])
        self.page = await self.browser.newPage()
        # await self.page.setViewport({"width": 800, "height": 1100})
        await self.page.waitFor(1000)
        await self.page.goto(self.url)
        await self.page.waitFor(1000)

        # await self.first_auth()

        # return self

        await self.search()

    async def search(self):
        total_lessons = 8
        column = self.weekday
        # column = 2
        count = 0
        links = ''

        for row in range(1, total_lessons + 1):
            lesson_selector = f"#stt_{row}_{column} > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)"
            lesson = await self.page.querySelector(lesson_selector)

            if lesson is not None:
                await lesson.click()

                popup = await self.page.querySelector(".popover-content")

                if popup is not None:
                    await self.page.click(".schedule_materials_open_btn")

                    dot_selector = "div.schedule_materials_item:nth-child(1) > span:nth-child(2) > a:nth-child(2)"
                    await self.page.waitFor(300)
                    dot = await self.page.querySelector(dot_selector)

                    if dot is not None:
                        count += 1
                        link = await self.page.evaluate("(dot) => dot.href", dot)
                        text = await self.page.evaluate("(popup) => popup.textContent", popup)
                        message = self.message_decorator(k=count, url=link, txt=text)
                        if count == 1:
                            links += f"Today is *{self.today}*\n\n"
                        links += f"{message}\n"
                        await self.page.click(dot_selector)
                        await self.page.waitFor(2000)
                        t = await self.browser.targets()[len(self.browser.targets()) - 1].page()
                        await t.close()

                    await self.page.click(".window_modal_close")
                    await lesson.click()
                    await self.page.waitFor(300)

        with open("last_links.txt", "r+", encoding="utf-8") as f:
            print(6)
            if len(links):
                if f.read() != links:
                    f.truncate(0)
                    f.write(links)
                    # print(links)
                    TelegramBot(self.token).send_msg(message=links)
                    return links
            else:
                emoji = u"\U0001F9DA"  # fairy
                msg = f"Today is *{self.today}*\n\nNo lectures, just\nchill & relax {emoji}"
                if f.read() != msg:
                    f.truncate(0)
                    f.write(msg)
                    # print(msg)
                    TelegramBot(self.token).send_msg(message=msg)
                    return msg

    @staticmethod
    def message_decorator(k, url, txt):
        pattern = r"[.][ ][^.]*"
        teacher_name = txt.split()[0]
        l = re.search(pattern, txt)
        t = l.group()[2:].split()
        if k == 1:
            s = rf"{k}\.  ["
        else:
            s = rf"{k}\. ["

        for i in t:
            if len(i) == 1:
                s += i[0]
            elif "-" in i:
                s += i[0] + i[i.find("-") + 1:i.find("-") + 2]
            else:
                s += i[0].upper()

        s += rf"]({url}) \- {teacher_name}"
        return s

    async def exit(self):
        await self.browser.close()


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.bot = None
        self.chat_id = 0

    def send_msg(self, message="_blank"):
        self.chat_id = "CHAT_ID"  # Your chat_id here
        self.bot = telebot.TeleBot(self.token)

        self.bot.send_message(chat_id=self.chat_id, text=message, disable_web_page_preview=True,
                              parse_mode="MarkdownV2")
