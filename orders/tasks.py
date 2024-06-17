from celery import shared_task
from .models import Order
import boto3
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from tempfile import NamedTemporaryFile
from django.core.files import File
import os

@shared_task
def process_video_and_update_order(order_id):
    order = Order.objects.get(id=order_id)
    video_url = order.blessn.url

    # Setup S3 client to download the video
    s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    bucket_name = video_url.split('/')[2].split('.')[0]  # Extract bucket name from URL
    key = '/'.join(video_url.split('/')[3:])  # Extract key from URL

    with NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        s3.download_file(bucket_name, key, tmp_file.name)
        clip = VideoFileClip(tmp_file.name)
        watermark = (ImageClip('logo.png', duration=clip.duration)
                     .set_opacity(0.5)
                     .resize(0.25)
                     .set_position(('right', 'bottom')))
        final_clip = CompositeVideoClip([clip, watermark])
        output_path = tmp_file.name.replace('.mp4', '_watermarked.mp4')
        final_clip.write_videofile(output_path, codec='libx264')

    # Prepare the new video file for saving to the FileField
    with open(output_path, 'rb') as file:
        django_file = File(file)
        order.blessn.save(os.path.basename(output_path), django_file, save=True)

    order.video_processing = False
    order.save()

    # Cleanup temporary files
    os.remove(tmp_file.name)
    os.remove(output_path)
