from pathlib import Path
from PIL import Image

def split_images(input_folder, output_folder, rows, cols):

    # make python paths of the in/out directories
    in_directory = Path(input_folder)
    out_directory = Path(output_folder)

    # process each image
    exts = ('.jpg', '.jpeg', '.png')
    for img_path in in_directory.glob('*.*'):

        if img_path.suffix not in exts:
            continue

        split_image(img_path, out_directory, rows, cols)


def split_image(img_path, out_directory, rows, cols):
    # open image
    img = Image.open(img_path)
    width, height = img.size

    segmentWidth = width / cols
    segmentHeight = height / rows

    # make output directory
    out_directory.mkdir(exist_ok=True)

    # hold list of paths to images created
    split_image_paths = []

    # crop image into 3x3
    for row in range(rows):
        for col in range(cols):

            x = width - (cols - col) * segmentWidth
            y = height - (rows - row) * segmentHeight

            cropped = img.crop((x, y, x + segmentWidth, y + segmentHeight))

            # save file (e.g. CoolImage12.png)
            cropped_name = Path(f'{img_path.stem}{row}{col}{img_path.suffix}')
            cropped_fp = out_directory / cropped_name
            cropped.save(cropped_fp)
            split_image_paths.append(cropped_fp)

    return split_image_paths


if __name__ == '__main__':
    input_folder = 'transect' # folder, should be passed in as param
    output_folder = 'transect/split' # folder, should be optionally passed in as param
    rows = 3 # number of rows to split image into
    cols = 3 # number of columns to split image into

    split_images(input_folder, output_folder, rows, cols)
