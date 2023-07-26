from PIL import Image
import os
def get_tweet_media(tweet):
    media_list = []
    if tweet.media.photos:
        for photo in tweet.media.photos:
            media_list.append(photo.url)
    if tweet.media.animated:
        for gif in tweet.media.animated:
            media_list.append(gif.thumbnailUrl)
    if tweet.media.videos:
        for vid in tweet.media.videos:
            media_list.append(vid.thumbnailUrl)
    return media_list
def get_tweet_links(tweet):
    links = []
    if tweet.links:
        for l in tweet.links:
            links.append(l.url)
    return links
def png_to_jpg(input_path):
    # Load the PNG image
    img = Image.open(input_path)

    # Get the file name without extension
    file_name_without_extension = os.path.splitext(input_path)[0]

    # Define the output path with the new extension (JPG)
    output_path = file_name_without_extension + '.jpg'

    # Convert and save the image as JPG
    img.convert('RGB').save(output_path)

    print(f"Conversion successful. Image saved as {output_path}")

    return output_path

def check_and_convert_to_jpg(picture_list):
    updated_picture_list = []
    for picture in picture_list:
        # Check if the file is a PNG image
        if picture.lower().endswith('.png'):
            converted_picture = png_to_jpg(picture)
            updated_picture_list.append(converted_picture)
        else:
            updated_picture_list.append(picture)

    return updated_picture_list
