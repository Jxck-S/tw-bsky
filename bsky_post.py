from datetime import datetime
from atproto import Client, models
def bsky_post_xp(client, image_files, text, links):
    if image_files:
        post_images = []
        for image_file in image_files:
            print("Creating image upload for", image_file)
            with open(image_file, 'rb') as f:
                img_data = f.read()
                upload = client.com.atproto.repo.upload_blob(img_data)
                # TODO image alt texts, copy from Twitter?
                post_images.append(models.AppBskyEmbedImages.Image(alt='Img alt', image=upload.blob))


        embed = models.AppBskyEmbedImages.Main(images=post_images)
    else:
        embed = None
    facets = []
    for link in links:
        if text.find(link) != -1:
            print("Creating facet for", link)
            # Find the starting index of the URL
            start_index = text.find(link)

            # Calculate the byte start and byte end
            byte_start = len(text[:start_index].encode('utf-8'))
            byte_end = byte_start + len(link.encode('utf-8'))
            #print(byte_start, byte_end)
            facets.append(
                        models.AppBskyRichtextFacet.Main(
                features=[models.AppBskyRichtextFacet.Link(uri=link)],
                index=models.AppBskyRichtextFacet.ByteSlice(byteStart=byte_start, byteEnd=byte_end),
            )
            )


    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,
            collection=models.ids.AppBskyFeedPost,
            record=models.AppBskyFeedPost.Main(
                createdAt=datetime.now().isoformat(), text=text, embed=embed, facets=facets
            ),
        )
    )

def bsky_post(user, pw, text, image_files, links):
    client = Client()
    client.login(user, pw)
    bsky_post_xp(client, image_files, text, links)



