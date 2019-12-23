import argparse
from datetime import datetime
from utils import makedir
from google_utils import list_blobs
from ffmpeg_utils import concat_videos


CRAIG_THE_POET_BUCKET = 'craig-the-poet'
CRAIGSLIST_ADS_DIR = 'craigslist'
POEM_DIR = 'poems'

FFMPEG_CONFIG = {'loglevel': 'panic', 'safe': 0, 'hide_banner': None, 'y': None}

def datetime_matches_craigslist_date(date, datetime_string):
    date_obj = datetime_string.split('T')[0]
    year, month, day = date_obj.split('-')
    datetime_obj = valid_date(f'{month}-{day}-{year}')
    return date == datetime_obj



def poem_stitcher(bucket_dir, min_length=None, max_length=None, date=None, all_for_day=False, preserve=False, **kwargs):
    # Get all blobs in the bucket
    blobs = list_blobs(CRAIG_THE_POET_BUCKET)

    # Filter to only the poems for this bucket_dir
    poems_dir = f'{POEM_DIR}/{bucket_dir}'
    poem_blobs = [blob for blob in blobs if poems_dir in blob.name]

    # Filter to poems from the given date, if given
    if date:
        poem_blobs = [blob for blob in poem_blobs if datetime_matches_craigslist_date(date, blob.metadata['posted_time'])]

    # Check current sum of poem run time
    total_poem_time = sum(float(blob.metadata['length']) for blob in poem_blobs)




    if total_poem_time < min_length:
        # TODO: Do something to get more runtime, or raise error
        return

    # TODO: Make selections of poems to stitch
    selected_poem_blobs = []
    if all_for_day:
        # Just concat all the poems we have
        selected_poem_blobs = poem_blobs
    else:
        pass


    makedir('poems')
    local_poem_filepaths = []
    for i, blob in enumerate(selected_poem_blobs):
        local_poem_filepath = f'poems/poem-{i}.mp4'
        blob.download_to_filename(local_poem_filepath)
        local_poem_filepaths += [local_poem_filepath]

    concat_videos(local_poem_filepaths, 'out.mp4')



    # TODO: In upload process, allow kwargs to set all YT stuff

#    for blob in selected_poem_blobs:
#        blob.metadata = {'used': 'true'}
#        blob.patch()

    pass


def valid_date(s):
    try:
        return datetime.strptime(s, "%m-%d-%Y")
    except ValueError:
        msg = f"Not a valid date: {s}"
        raise argparse.ArgumentTypeError(msg)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket-dir', required=True)

    # Min/Max output video length -- time in seconds
    parser.add_argument('--min-length', type=float)
    parser.add_argument('--max-length', type=float)

    parser.add_argument('--date', type=valid_date)
    parser.add_argument('--all-for-day', action='store_true')

    parser.add_argument('--preserve', action='store_true')

    args = parser.parse_args()

    poem_stitcher(**vars(args))
