#!/usr/bin/env python3
"""Add or update a designer entry in the Google Fonts catalog.

Usage:
# Add or update a designer entry. User will need to hand complete the bio.html
$ gftools add-designer ~/Type/fonts/catalog/designers "Theo Salvadore" path/to/img.png

# Add or update a designer entry and use the spreadsheet to create the bio.html file
$ gftools add-designer ~/Type/fonts/catalog/designers "Theo Salvador" path/to/img.png --spreadsheet .GFDesigners.xlsx
"""
import argparse
import os
from PIL import Image
from gftools.designers_pb2 import DesignerInfoProto
from google.protobuf import text_format


def process_image(fp):
    if not os.path.isfile(fp):
        raise ValueError(f"{fp} is not a file")
    img = Image.open(fp)
    width, height = img.size
    if width != height:
        print("warning: img is rectangular when it should be square")
    if width < 300 or height < 300:
        print("warning: img is smaller than 300x300px")

    print("resizing image")
    img.thumbnail((300, 300))
    return img


def gen_info(designer, img_path, link=""):
    # Write info.pb
    info = DesignerInfoProto()
    info.designer = designer
    info.link = ""
    info.avatar.file_name = img_path

    text_proto = text_format.MessageToString(info, as_utf8=True, use_index_order=True)
    return text_proto


def parse_urls(string):
    urls = string.split()
    res = []
    for url in urls:
        if not url.startswith("http"):
            url = "https://" + url
        res.append(url)
    return res


def make_designer(
    designer_directory,
    name,
    img_path,
    bio=None,
    urls=None,
):
    designer_dir_name = name.lower().replace(" ", "").replace("-", "")
    designer_dir = os.path.join(designer_directory, designer_dir_name)
    if not os.path.isdir(designer_dir):
        print(f"{name} isn't in catalog. Creating new dir {designer_dir}")
        os.mkdir(designer_dir)

    print(f"processing image {img_path}")
    image = process_image(img_path)
    image_file = os.path.join(designer_dir, f"{designer_dir_name}.png")
    image.save(image_file)

    print(f"Generating info.pb file")
    info_pb = gen_info(name, os.path.basename(image_file))
    filename = os.path.join(designer_dir, "info.pb")
    with open(filename, "w") as f:
        f.write(info_pb)

    # write/update bio.html
    bio_file = os.path.join(designer_dir, "bio.html")
    html_text = None
    if bio:
        print("Generating bio.html")
        html_text = f"<p>{bio}</p>"
        if urls:
            hrefs = " | ".join(
                f"<a href={u}>{u.split('//')[1]}</a>" for u in urls
            )
            html_text += "\n" + f"<p>{hrefs}</p>"
    elif os.path.isfile(bio_file):
        print("Skipping. No bio text supplied but bio.html already exists")
    else:
        print(f"Please manually update the bio.html file")
        html_text = "N/A"
    if html_text:
        with open(bio_file, "w") as f:
            f.write(html_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("designers_directory")
    parser.add_argument("name")
    parser.add_argument("img_path")
    parser.add_argument(
        "--spreadsheet", help="Optional path to the Google Drive spreadsheet"
    )
    args = parser.parse_args()

    if args.spreadsheet:
        import pandas as pd

        df = pd.read_excel(args.spreadsheet)
        entry = df.loc[df["Name"] == args.name]
        bio = entry["Bio"].item()
        urls = entry["Link"].item()
        if urls:
            urls = parse_urls(urls)
    else:
        bio = None
        url = None

    make_designer(args.designers_directory, args.name, args.img_path, bio, urls)


if __name__ == "__main__":
    main()