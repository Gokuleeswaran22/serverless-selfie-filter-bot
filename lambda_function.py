import json
import boto3
from PIL import Image, ImageDraw, ImageFont
import io
import os

SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET_NAME')
DESTINATION_BUCKET = os.environ.get('DESTINATION_BUCKET_NAME')

s3_client = boto3.client('s3')

FONT_PATH = '/opt/python/lib/python3.12/site-packages/Pillow/Fonts/FreeMono.ttf' 

def lambda_handler(event, context):
    try:
        record = event['Records'][0]['s3']
        source_bucket_name = record['bucket']['name']
        object_key = record['object']['key']
        
        print(f"Processing image: {object_key} from bucket: {source_bucket_name}")

        if source_bucket_name != SOURCE_BUCKET:
            print(f"Ignoring event from non-source bucket: {source_bucket_name}")
            return {'statusCode': 200, 'body': json.dumps('Ignored.')}

        response = s3_client.get_object(Bucket=source_bucket_name, Key=object_key)
        image_content = response['Body'].read()
        image = Image.open(io.BytesIO(image_content))

        processed_image = image.convert("L") 

        draw = ImageDraw.Draw(processed_image)
        text = "SERVERLESS FILTER BOT"
        font_size = 40
        
        try:
            font = ImageFont.truetype(FONT_PATH, font_size) 
        except IOError:
            font = ImageFont.load_default() 

        textwidth = draw.textlength(text, font)
        
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        textheight = bottom - top
        
        width, height = processed_image.size
        x = width - textwidth - 20
        y = height - textheight - 20
        
        draw.text((x, y), text, font=font, fill=(255)) 

        output_buffer = io.BytesIO()
        processed_image.save(output_buffer, format=image.format if image.format else 'PNG')
        output_buffer.seek(0)

        destination_key = "filtered-" + object_key
        s3_client.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=destination_key,
            Body=output_buffer,
            ContentType=image.info.get('ContentType', 'image/png')
        )
        
        print(f"Successfully filtered {object_key} and uploaded to {DESTINATION_BUCKET}/{destination_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Image processed successfully!', 'output_key': destination_key})
        }
        
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e