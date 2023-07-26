import asyncio
from twscrape import API, gather
from twscrape.logger import set_log_level
from twscrape.imap import add_imap_mapping
import time
import json
from bsky_post import bsky_post
from media import get_tweet_media, get_tweet_links
async def main():
    eapi = API()  # or API("path-to.db") - default is `accounts.db`
    set_log_level("DEBUG")
    with open("tw_scrape_accounts.json", 'r') as file:
        scraper_account = json.load(file)
    # ADD ACCOUNTS (for CLI usage see BELOW))
    for username, info in scraper_account.items():
        await eapi.pool.add_account(username, info['pw'], info['email'], info['email_pw'])

    await eapi.pool.login_all()

    # API USAGE


    import re
    def replace_usernames(text):
        pattern = r'@(\w+)'
        replaced_text = re.sub(pattern, r'AT(\1)', text)
        return replaced_text
    import re
    def remove_last_link(text):
        # Regular expression to match URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        # Find all URLs in the text
        urls = re.findall(url_pattern, text)

        # Check if there are any URLs to remove
        if urls:
            # Find the last URL in the text
            last_url = urls[-1]

            # Replace the last URL with an empty string to remove it
            text = text.replace(last_url, "")

        return text
    def replace_links_with_order(text, replacements):
        # Regular expression to match URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

        # Find all URLs in the text
        urls = re.findall(url_pattern, text)

        # Initialize lists to store replaced text and unused replacements
        replaced_text = text
        unused_replacements = []

        # Replace the URLs with the replacements from the list
        for i, url in enumerate(urls):
            if i < len(replacements):
                replacement = replacements[i]
                replaced_text = replaced_text.replace(url, replacement)
            else:
                unused_replacements.append(url)

        return replaced_text, unused_replacements

    def clean_tweet(text):
        return remove_last_link(replace_usernames(text))
    from datetime import datetime, timezone
    #TEST with "latest": datetime(2023, 5, 3)
    with open("accounts.json", 'r') as file:
        accounts = json.load(file)
    for account, inf in accounts.items():
        if "latest" in inf.keys():
            accounts[account]['latest'] = accounts[account]['latest'].replace(tzinfo=timezone.utc)
    import requests, os
    def extract_file_name_from_url(url):
        # Split the URL to get the file name
        file_name = os.path.split(url)[-1]
        return file_name

    def save_image_from_url(url, file_path):
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
    for username in accounts.keys():
        uid = await eapi.user_by_login(username)
        accounts[username]["user_id"] = uid.id
    while True:
        for username, ai in accounts.items():
            user_id = ai['user_id']
            user_tweets = await gather(eapi.user_tweets_and_replies(user_id, limit=10))  # list[Tweet]
            #print(user_tweets)
            if "latest" not in ai.keys():
                lat = None
                for tweet in user_tweets:
                    if not lat or tweet.date > lat:
                        lat = tweet.date
                        txt_info = tweet.rawContent

                accounts[username]["latest"] = lat
                print(f"Start, latest for @{username} is {accounts[username]['latest']}", txt_info)
            else:

                for tweet in reversed(user_tweets):

                    if tweet.date > ai["latest"]:
                        if tweet.user.id == user_id and not tweet.inReplyToTweetId:
                            accounts[username]['latest'] = tweet.date
                            media_list = []
                            vid_list = []
                            links = []
                            if not tweet.retweetedTweet:
                                #print(tweet.rawContent)
                                new_text = clean_tweet(tweet.rawContent)
                                links += get_tweet_links(tweet)
                                media_list += get_tweet_media(tweet)
                            if tweet.quotedTweet:
                                new_text += f"\n\nQT AT({tweet.quotedTweet.user.username}) \"{clean_tweet(tweet.quotedTweet.rawContent)}\""
                                media_list += get_tweet_media(tweet.quotedTweet)
                                links += get_tweet_links(tweet.quotedTweet)
                            if tweet.retweetedTweet:
                                new_text = f"\n\nRT AT({tweet.retweetedTweet.user.username}) \"{clean_tweet(tweet.retweetedTweet.rawContent)}\""
                                media_list += get_tweet_media(tweet.retweetedTweet)
                                links += get_tweet_links(tweet.retweetedTweet)
                            new_text, unused_links  = replace_links_with_order(new_text, links)
                            #print(links, unused_links)
                            for link in unused_links:
                                    new_text += f" {link}"
                            #print("NEW", new_text)
                            image_files = []
                            #print(media_list)
                            new_text = new_text.strip()
                            if len(new_text) > 300:
                                new_text = new_text.replace("\n\n", "\n")
                            if len(new_text) > 300:
                                new_text = new_text[0:296] + "..."
                            for media in media_list:
                                file_name = extract_file_name_from_url(media)
                                save_image_from_url(media, file_name)
                                image_files.append(file_name)
                            from media import check_and_convert_to_jpg
                            image_files = check_and_convert_to_jpg(image_files)
                            print("NEW", new_text, "LINKS:", links, "MEDIA:", image_files)
                            bsky_post(ai["bsky_u"], ai["bsky_p"], new_text, image_files, links)
            print("\nWaiting 5 sec\n")
            time.sleep(5)
        print("Sleeping........")
        time.sleep(5*120)
        print("New Check")





    # change log level, default info


    # Tweet & User model can be converted to regular dict or json, e.g.:
    #doc = await eapi.user_by_id(user_id)  # User
    #doc.dict()  # -> python dict
    #doc.json()  # -> json string

if __name__ == "__main__":
    asyncio.run(main())