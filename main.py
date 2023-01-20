import requests
from bs4 import BeautifulSoup
import tweepy
import os
import logging
import json

logging.basicConfig(filename='logs.txt',
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s:%(message)s')


def scrape_text(url):
    logging.info("started Scrape Text")
    # Make an HTTP GET request to the web server
    response = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the text elements on the page
    text_elements = soup.find_all(text=True)

    # Filter out any elements that are contained within script or style tags
    text_elements = [elem for elem in text_elements if not any(parent.name in ["style", "script"] for parent in elem.parents)]

    # Extract the text from the text elements and return as a single string
    text = " ".join(text_elements)
    cleaned = remove_junk(text)
    return cleaned


def delete_before(string, target):
    logging.info("started Delete before")
    # Find the index of the target substring
    index = string.find(target)

    # If the target substring is not found, return the original string
    if index == -1:
        return string

    # Return the portion of the string after the target substring
    return string[index + len(target):]


def delete_all_before(string, target):
    logging.info("started delete all before")
    # Keep looping until the target substring is no longer present in the string
    while target in string:
        string = delete_before(string, target)
    return string


def delete_after(string, target):
    logging.info("started delete after")
    # Find the index of the target substring
    index = string.find(target)

    # If the target substring is not found, return the original string
    if index == -1:
        return string

    # Return the portion of the string before the target substring
    return string[:index]


def split_string(string):
    logging.info("started split string")
    # Initialize an empty list to store the pieces of the string
    pieces = []

    # Split the string into pieces of 280 characters or fewer
    for i in range(0, len(string), 256):
        pieces.append(string[i:i+256])

    return pieces


def remove_junk(string):
    logging.info("started remove newlines")
    # Replace all newline characters with an empty string
    newline = string.replace("\n", "")
    nbsp = newline.replace(" ", " ")
    return nbsp


def post_tweet(tweet,id=0):
    logging.info("started post tweet")

    twitterAuthKeys = getConfig("config.txt")

    auth = tweepy.OAuthHandler(
        twitterAuthKeys['consumer_key'],
        twitterAuthKeys['consumer_secret']
    )
    auth.set_access_token(
        twitterAuthKeys['access_token'],
        twitterAuthKeys['access_token_secret']
    )
    if id == 0:
        try:
            api = tweepy.API(auth)
            status = api.update_status(status=tweet)
            logging.debug(tweet)
            update_history(tweet)
            return status.id
        except tweepy.errors.TweepyException as e:
            logging.ERROR("Error posting tweet: ")
            logging.ERROR(e.text)
            return "Fail"
    else:
        try:
            api = tweepy.API(auth)
            status = api.update_status(status=tweet,
                                       in_reply_to_status_id=id,
                                       auto_populate_reply_metadata=True)
            logging.debug(tweet)
            return status.id
        except tweepy.errors.TweepyException as e:
            logging.ERROR("Error posting tweet: ")
            logging.ERROR(e.text)
            return "Fail"


def update_history(tweet):
    logging.info("started update history")
    # Open a file for writing
    f = open("history.txt", "w")

    # Write the string to the file
    f.write(tweet)

    # Close the file
    f.close()


def check_history(tweet):
    logging.info("started check history")
    # Open a file for writing
    if os.path.exists('history.txt'):
        # file exists
        f = open("history.txt", "r")
        history = f.read()
    # do something with the file
    else:
        # Open a file for writing
        f = open("history.txt", "w")
        # Write the string to the file
        f.write(tweet)
        # Close the file
        f.close()
        logging.debug("tweet not in history")
        return False

    # Write the string to the file
    logging.debug(history)
    logging.debug(tweet)
    if tweet in history:
        result = False
        logging.debug("tweet found in history")
    else:
        result = True
        logging.debug("tweet not in history")

    # Close the file
    f.close()
    return result

def export_json_to_txt(json_obj, file_path):
    with open(file_path, 'w') as outfile:
        json.dump(json_obj, outfile)


def thread3Pieces(string: str) -> tuple[str, str, str]:
    logging.info("starting thread 3 pieces")
    first_piece_end = string[:270].rfind(' ')
    logging.info(first_piece_end)

    temp_end = first_piece_end + 270
    second_piece_temp = string[first_piece_end:temp_end].rfind(' ')
    second_piece_end = first_piece_end + second_piece_temp
    logging.info(second_piece_end)

    temp_end = second_piece_end + 270
    third_piece_temp = string[second_piece_end:temp_end].rfind(' ')
    third_piece_end = second_piece_end + third_piece_temp
    logging.info(third_piece_end)

    temp_end = third_piece_end + 240
    fourth_piece_temp = string[third_piece_end:temp_end].rfind(' ')
    fourth_piece_end = third_piece_end + fourth_piece_temp
    logging.info(fourth_piece_end)

    first_piece = string[:first_piece_end]
    logging.info(first_piece)
    second_piece = string[first_piece_end:second_piece_end]
    logging.info(second_piece)
    third_piece = string[second_piece_end:third_piece_end]
    logging.info(third_piece)
    fourth_piece = string[third_piece_end:fourth_piece_end]
    return [first_piece, second_piece, third_piece, fourth_piece]


def getConfig(file_path):
    with open(file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data


def main():
    logging.info("started main")
    url = "https://www.skichinapeak.com/get-the-latest"
    ending = " bit.ly/ChinaPk"
    threadStyle = False
    fullSiteText = scrape_text(url)
    afterLatest = delete_all_before(fullSiteText, "... ")
    justLatest = delete_after(afterLatest, "PURCHASE TICKETS HERE")
    logging.info(justLatest)
    pieces = split_string(justLatest)
    if threadStyle:
        thread = thread3Pieces(justLatest)
        if check_history(thread[0]):
            r = 0
            for x in range(4):
                tweet = thread[x]
                logging.info(tweet)
                if x == 3:
                    tweet = thread[x] + "... Read More:" + ending
                    logging.info(tweet)
                r = post_tweet(tweet, r)
        else:
            logging.warning("tweet already exists")
    else:
        tweet = pieces[0] + ending
        logging.info(tweet)
        if check_history(tweet):
            logging.debug(tweet)
            r = post_tweet(tweet)
            logging.debug(r)
        else:
            logging.warning("tweet already exists")


if __name__ == "__main__":
    main()

