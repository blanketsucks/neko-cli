from neko.providers import DanbooruProvider
import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        
        # All of the keys are optional except for the username and api_key.
        # To learn how to get an API key, visit https://danbooru.donmai.us/wiki_pages/help:api
        extras = {
            'username': 'username',
            'api_key': 'api-key',
            'tags': [], # A list of tags to search for.
            'rating': 'safe', # Must be one of safe, questionable, explicit.
            'limit': 30, # Must be between 1 and 200.
            'sort': {
                'by': 'popular', # Must be one of popular, curated, random, viewed.
                'scale': 'day', # Must be one of day, week, month.
                'date': '2022-01-01' # Must be a valid date.
            }
        }

        provider = DanbooruProvider(session, extras=extras)
        url = await provider.fetch_image()
        print(url)

        # Similar to the RedditProvider, this provider also caches images.
        # The `get_cached_images` method can be used to get the images.
        for image in provider.get_cached_images():
            print(image.file.url)

asyncio.run(main())