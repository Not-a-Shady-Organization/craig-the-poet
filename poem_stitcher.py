import argparse
from datetime import datetime
from utils import makedir, convert_to_date, LogDecorator, craigslist_format_to_date, craigslist_format_to_datetime
from google_utils import list_blobs
from ffmpeg_utils import concat_videos
import os
from async_utils import handle_requests



CRAIG_THE_POET_BUCKET = 'craig-the-poet'
POEM_DIR = 'poems'
AD_DIR = 'craigslist'

FFMPEG_CONFIG = {'loglevel': 'panic', 'safe': 0, 'hide_banner': None, 'y': None}

POEM_MAKER_ENDPOINT = os.environ['POEM_MAKER_ENDPOINT']


# TODO: Q Do we need to keep a source_poem_bucket_dir?  Maybe on crash we could have videos orphaned there

def poem_stitcher(source_ad_bucket_dir, source_poem_bucket_dir, dont_post_if_under=None, min_length=None, max_length=None, date=None, all_of_day=False, preserve=False, **kwargs):
    dont_post_if_under = float(dont_post_if_under) if dont_post_if_under else None

    # Get all blobs in the bucket (ads & poems)
    blobs = list_blobs(CRAIG_THE_POET_BUCKET)

    ################
    # FILTER BLOBS #
    ################

    # Filter to only the ads for this bucket_dir
    ads_dir = f'{AD_DIR}/{source_ad_bucket_dir}'
    ad_blobs = [blob for blob in blobs if ads_dir in blob.name and 'ledger.txt' not in blob.name]

    # Filter to blobs from the given date, if date was given
    if date:
        ad_blobs = [blob for blob in ad_blobs if craigslist_format_to_date(blob.metadata['ad-posted-time']) == date]


    ##################
    # GENERATE POEMS #
    ##################

    if all_of_day:
        # The All Of Day option means we should generate a poem for every ad
        # from the specified day within the specified bucket directory

        # Request poem for each blob which hasn't failed a run
        request_list = []

        # Note: This DOESNT discount used blobs
        safe_ad_blobs = [blob for blob in ad_blobs if blob.metadata['failed'] != 'true']
        for blob in safe_ad_blobs:
            request_list.append({
                'method': 'POST',
                'url': POEM_MAKER_ENDPOINT,
                'json': {
                    'bucket_path': blob.name,
                    'destination_bucket_dir': source_poem_bucket_dir
                }
            })

        for request in request_list:
            print(f'POSTing request: {request}')

        responses = handle_requests(request_list)

        for response in responses:
            print(f'Response received: {response}')


    else:
        print('Not yet handling cases other than --all-of-day. Exiting...')
        exit()


    ################
    # SELECT POEMS #
    ################
    # Find all poems available on the bucket

    # Get all blobs in the bucket (ads & poems)
    blobs = list_blobs(CRAIG_THE_POET_BUCKET)

    # Filter to only the poems for this bucket_dir
    poems_dir = f'{POEM_DIR}/{source_poem_bucket_dir}'
    poem_blobs = [blob for blob in blobs if poems_dir in blob.name]

    # Filter to blobs from the given date, if date was given
    if date:
        poem_blobs = [blob for blob in poem_blobs if craigslist_format_to_date(blob.metadata['ad-posted-time']) == date]


    selected_poem_blobs = []

    if all_of_day:
        # Concat all the poems we have for the day in the bucket directory
        selected_poem_blobs = poem_blobs

        # Order the blobs by time of post
        selected_poem_blobs = sorted(selected_poem_blobs, key=lambda x: craigslist_format_to_datetime(x.metadata['ad-posted-time']))

    else:
        print('Not yet handling cases other than --all-of-day. Exiting...')
        exit()


    ############
    # VALIDATE #
    ############

    # Check current sum of poem run time
    total_runtime = sum(float(blob.metadata['runtime']) for blob in selected_poem_blobs)

    # Create poems until we've got enough
#    while min_length and total_poem_time < min_length:
        # TODO: Do something to get more runtime, or raise error
#        print(f'Total runtime {total_poem_time} seconds, need {min_length} seconds')
#        print(f'Requesting more poems')
#        request_poem_creation(source_bucket_dir)

#    print('Min poem runtime met')

    if all_of_day:
        if total_runtime < dont_post_if_under:
            print('Minimum runtime length not met. Exiting...')
            exit()


    ################
    # CONCAT POEMS #
    ################

    # Download all poems that we've selected
    makedir('poems')
    local_poem_filepaths = []
    for i, blob in enumerate(selected_poem_blobs):
        local_poem_filepath = f'poems/poem-{i}.mp4'
        blob.download_to_filename(local_poem_filepath)
        local_poem_filepaths += [local_poem_filepath]

    # Concat all the poem into one
    concat_videos(local_poem_filepaths, 'out.mp4', **FFMPEG_CONFIG)

    print('Concatenation complete')

    #####################
    # UPLOAD TO YOUTUBE #
    #####################

    # TODO: In upload process, allow kwargs to set all YT stuff

#    for blob in selected_poem_blobs:
#        blob.metadata = {'used': 'true'}
#        blob.patch()

    pass




if __name__ == '__main__':
    '''
    TODO

    Get modes working for these use cases
        handled
              None

        handling
              create & upload video of all ads for the day

        unhandled
              create & upload video of length > 10min
              create & upload video of length > 10min for given day
              create & upload video with 3 long ads
              create & upload video with 1 long, 1 medium, 1 short, and 1 long ad
              Set ranges for short, medium, and longness (as word count)

    '''


    parser = argparse.ArgumentParser()
    parser.add_argument('--source-ad-bucket-dir', required=True)
    parser.add_argument('--source-poem-bucket-dir', required=True)

    parser.add_argument('--dont-post-if-under', type=float)

    # Min/Max output video length -- time in seconds
    parser.add_argument('--min-length', type=float)
    parser.add_argument('--max-length', type=float)

    parser.add_argument('--date', help='Filter to only posts from this date. Format: mm-dd-yyyy', type=convert_to_date)
    parser.add_argument('--all-of-day', action='store_true')

    parser.add_argument('--preserve', action='store_true')

    args = parser.parse_args()


    # Toss invalid combinations of args...
    if args.all_of_day and not args.date:
        print('Must specify date to use --all-of-day flag. Exiting...')
        exit()


    poem_stitcher(**vars(args))
