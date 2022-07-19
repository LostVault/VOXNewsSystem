import os
import traceback
import signal
import asyncio

import discord
import discord.ext.tasks

import galnet
from model import model


class VOXGalactica(discord.Client):
    def __init__(self, channel_id: int, *args, **kwargs):
        super().__init__(**kwargs)
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        print('Shutdown callbacks registered')
        self.channel_id = channel_id
        self.task_started = False

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        if not self.task_started:
            self.notifier_background_task.start()
            self.task_started = True

    def shutdown(self, sig, frame):
        print(f'Shutting down by signal: {sig}')
        asyncio.create_task(self.close())

    @discord.ext.tasks.loop(seconds=float(os.environ['VOX_NEWS_PULL_INTERVAL']))
    async def notifier_background_task(self):
        print('Starting the pull')
        try:
            channel: discord.channel.TextChannel = self.get_channel(self.channel_id)
            for one_news in reversed(await galnet.get_news(10)):
                if model.check_news(one_news):
                    continue

                model.save_news(one_news)

                print(f'Going to send {one_news.title!r}')
                formatted_msg = await galnet.format_news(one_news)

                for part in formatted_msg:
                    await channel.send(**part)

        except Exception as e:
            print(traceback.format_exc())
            raise e

    @notifier_background_task.before_loop
    async def notifier_wait_ready(self):
        await self.wait_until_ready()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = VOXGalactica(int(os.environ['VOX_DISCORD_CHANNEL_ID']), loop=loop)
    loop.run_until_complete(client.start(os.environ['VOX_DISCORD_TOKEN']))
