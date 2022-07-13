from neko.providers import RedditProvider
import asyncio
import aiohttp

async def main(subreddit: str, sort_by: str) -> None:
    async with aiohttp.ClientSession() as session:
        # The reddit provider is the only provider that uses extra information.
        # The subreddit key is required and the sort is optional.
        # Any extra arguments will be passed in as parameters during the request.
        provider = RedditProvider(session, {'subreddit': subreddit, 'sort': sort_by})

        # RedditProvider doesn't need a type, so we just pass in an empty string.
        url = await provider.fetch_image('')
        print(url)

        # To avoid alot of requests, the provider caches the first 30 images
        # which can be accessed with the `get_cached_images` method.
        for (url, name) in provider.get_cached_images():
            # If you notice many URLs under the same name, that means that that was a gallery.
            print(f'{name}: {url}')

asyncio.run(main('aww', 'hot'))