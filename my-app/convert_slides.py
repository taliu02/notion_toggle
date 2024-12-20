from openai import OpenAI
from notion_client import Client
import os
from pdf2image import convert_from_path
import json
import ast
import boto3
import tiktoken
from collections import defaultdict
import sys
from config import (
    NOTION_TOKEN,
    OPENAI_API_KEY,
    NOTION_PAGE_ID,
    IMGUR_CLIENT_ID,
    PDF_PATH,
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
)


def generate_presigned_url(file_name):
    try:
        response = s3_client.generate_presigned_post(
            Bucket="notion-ppt", Key=file_name, ExpiresIn=3600
        )
        return response
    except Exception as e:
        print(f"Error generating presigned URL: {str(e)}")
        return None


s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)


client = OpenAI(api_key=OPENAI_API_KEY)


def group_slides_by_title(pages, slide_titles):
    grouped_slides = defaultdict(list)
    for i, (page, title) in enumerate(zip(pages, slide_titles)):
        grouped_slides[title].append((i, page))
    return grouped_slides


def count_tokens(text):
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def extract_titles_with_token_limit(text_list):
    current_tokens = 0
    current_batch = []
    all_titles = []

    for text in text_list:
        tokens = count_tokens(text)
        if current_tokens + tokens > 1990:  # Leave room for response
            titles = extract_title_with_gpt(current_batch)
            actual_list = ast.literal_eval(titles)
            print(actual_list, type(actual_list))
            print(all_titles, type(all_titles))
            all_titles.extend(actual_list)
            print(all_titles)
            current_batch = [text]
            current_tokens = tokens
        else:
            current_batch.append(text)
            current_tokens += tokens

    if current_batch:
        titles = extract_title_with_gpt(current_batch)
        actual_list = ast.literal_eval(titles)
        all_titles.extend(actual_list)

    return all_titles


def extract_title_with_gpt(slides):

    # Convert the list of slides to a JSON-like string
    slides_json = json.dumps(slides)
    # Call GPT with instructions
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You will receive a JSON array where each element is a text block representing a slide. "
                    "Extract the main title from each slide. The title is typically found in the first or second line, "
                    "but it may extend further if necessary. Return the titles as a JSON array."
                ),
            },
            {"role": "user", "content": slides_json},
        ],
        temperature=0,
    )

    # Parse and return the response
    return response.choices[0].message.content.strip()


def extract_text_with_pypdf2(pdf_path):
    # Read your PDF text into a string first using pdftotext
    with open("output.txt", "r", encoding="utf-8") as f:
        text = f.read()
    # Split text by new lines into a list of lines

    lines = text.split("\n\n")

    titles = extract_titles_with_token_limit(lines)
    return titles


def convert_pdf_and_upload_to_notion(
    pdf_path, notion_page_id, notion_token, imgur_client_id
):
    # Initialize clients
    notion = Client(auth=notion_token)
    # imgur = pyimgur.Imgur(imgur_client_id)

    # Get slide titles
    print("Extracting titles from PDF...")
    slide_titles = extract_text_with_pypdf2(pdf_path)

    # Convert PDF to images
    print(f"Converting {pdf_path} to images...")
    pages = convert_from_path(pdf_path, dpi=300)

    # Create temporary directory for images
    temp_dir = "temp_slides"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Group slides by title
    grouped_slides = group_slides_by_title(pages, slide_titles)

    try:
        # For each unique title
        for title, slides in grouped_slides.items():
            print(f"Processing slides with title: {title}")

            toggle_block = {
                "children": [
                    {
                        "object": "block",
                        "type": "toggle",
                        "toggle": {
                            "rich_text": [
                                {"type": "text", "text": {"content": title[:2000]}}
                            ],
                            "children": [],
                        },
                    }
                ]
            }

            # Process each slide with the same title
            for i, page in slides:
                image_path = f"{temp_dir}/slide_{i+1}.png"
                page.save(image_path, "PNG")
                try:
                    # Upload to S3
                    s3_key = f"slides/slide_{i+1}.png"
                    s3_client.upload_file(
                        image_path, "notion-ppt", s3_key  # your bucket name
                    )

                    # Generate a URL for the uploaded image
                    url = s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": "notion-ppt", "Key": s3_key},
                        ExpiresIn=3600 * 24 * 7,  # URL valid for 7 days
                    )

                    # Add image to toggle block
                    toggle_block["children"][0]["toggle"]["children"].append(
                        {
                            "object": "block",
                            "type": "image",
                            "image": {
                                "type": "external",
                                "external": {"url": url},
                            },
                        }
                    )
                # try:
                #     # Upload to Imgur
                #     uploaded_image = imgur.upload_image(
                #         image_path, title=f"Slide {i+1}"
                #     )
                #     image_url = uploaded_image.link

                #     # Add image to toggle block
                #     toggle_block["children"][0]["toggle"]["children"].append(
                #         {
                #             "object": "block",
                #             "type": "image",
                #             "image": {
                #                 "type": "external",
                #                 "external": {"url": image_url},
                #             },
                #         }
                #     )

                except Exception as e:
                    print(f"Error processing slide {i+1}: {str(e)}")
                    continue

                finally:
                    # Clean up temporary image
                    if os.path.exists(image_path):
                        os.remove(image_path)

            # Append the toggle block to the page
            notion.blocks.children.append(block_id=notion_page_id, **toggle_block)
            print(f"Created toggle block with title: {title}")

    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except OSError:
                print("Warning: Could not remove temporary directory")

    print("Upload complete!")


# Usage
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python convert_slides.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    convert_pdf_and_upload_to_notion(
        pdf_path=pdf_path,
        notion_page_id=NOTION_PAGE_ID,
        notion_token=NOTION_TOKEN,
        imgur_client_id=IMGUR_CLIENT_ID,
    )
