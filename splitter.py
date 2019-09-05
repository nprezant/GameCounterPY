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
    row_paths = []

    # crop image into 3x3
    for row in range(rows):
        for col in range(cols):

            x = width - (cols - col) * segmentWidth
            y = height - (rows - row) * segmentHeight

            cropped = img.crop((x, y, x + segmentWidth, y + segmentHeight))

            # save file (e.g. CoolImage12.png)
            cropped_name = Path(f'{img_path.stem}_{row}{col}{img_path.suffix}')
            cropped_fp = out_directory / cropped_name
            cropped.save(cropped_fp)
            row_paths.append(cropped_fp)

        split_image_paths.append(row_paths.copy())
        row_paths.clear()

    return split_image_paths

def stitch_images_from_fp(img_paths):
    rows = []
    for img_path_row in img_paths:
        img_row = map(Image.open, img_path_row)
        rows.append(img_row)

    return stitch_images(rows)

def stitch_images(images):
    '''Stitches the gridded images back into one'''
    rows = []

    for img_row in images:
        combined_row = append_images(img_row, direction='horizontal')
        rows.append(combined_row)

    return append_images(rows, direction='vertical')

def append_images(images, direction='horizontal',
                  bg_color=(255,255,255, 0), aligment='center'):
    '''
    Appends images in horizontal/vertical direction.

    Args:
        images: List of PIL images
        direction: direction of concatenation, 'horizontal' or 'vertical'
        bg_color: Background color (default: white)
        aligment: alignment mode if images need padding;
           'left', 'right', 'top', 'bottom', or 'center'

    Returns:
        Concatenated image as a new PIL image object.
    '''
    widths, heights = zip(*(i.size for i in images))

    if direction=='horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)

    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)


    offset = 0
    for im in images:
        if direction=='horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1])/2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0])/2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]

    return new_im
    


if __name__ == '__main__':
    input_folder = 'transect' # folder, should be passed in as param
    output_folder = 'transect/split' # folder, should be optionally passed in as param
    rows = 3 # number of rows to split image into
    cols = 3 # number of columns to split image into

    split_images(input_folder, output_folder, rows, cols)
