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
            for one_news in reversed(await galnet.get_news()):
                title: str = one_news['attributes']['title']
                if not model.check_news(one_news['attributes']['field_galnet_guid']):
                    model.save_news(one_news)

                else:
                    continue

                print(f'Going to send {title!r}')

                body: str = one_news['attributes']['body']['value']
                galnet_date: str = galnet.russify_date(one_news['attributes']['field_galnet_date'])
                # galnet_image_url: str = galnet.BASE_PICTURES.format(picture=one_news['attributes']['field_galnet_image'])
                # published_at: str = one_news['attributes']['published_at']

                picture_discord_file = await galnet.get_picture(one_news['attributes']['field_galnet_image'])

                body = body.replace('\n', '\n\n')
                message = f"""⠀
```fix
{title}
{galnet.russify_date(galnet_date)}
``````
{body}
```"""
                if len(message) > 2000:
                    message = f'{title!r} > 2000 символов'
                    picture_discord_file = None

                await channel.send(message, file=picture_discord_file)

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
