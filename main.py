import time
import json
import PySimpleGUI as gui
import os
import io
from PIL import Image
import math
import random
from typing import Dict, List, Tuple


# Uppermost indexes of animation types
cast = (0, 6)
thrust = (39, 46)
walk = (104, 112)
slash = (156, 161)
shoot = (208, 220)

animation_starts = [cast[0], thrust[0], walk[0], slash[0], shoot[0]]
animation_ends = [cast[1], thrust[1], walk[1], slash[1], shoot[1]]


def section_data(data: Dict, section_name: str):
    # Returns the value of a key in a dictionary, with a check for if that key exists
    if section_name in data:
        return data[section_name]

    else:
        return None


def read_json(filepath: str) -> Dict:
    file = open(filepath)
    data = json.load(file)
    file.close()

    return data


def read_image(filepath: str) -> Image.Image:
    im = Image.open(filepath)

    return im 


# minimum_parts = [
#     "body/female/human",
#     "arms",
#     "bauldron",
#     "bracers",
#     "cape",
#     "eyes",
#     "facial",
#     "feet",
#     "gloves",
#     "hair",
#     "hat",
#     "head",
#     "legs",
#     "neck",
#     "quiver",
#     "shield",
#     "shoulders",
#     "torso",
#     "weapon",
#     ]

parts_variant_whitelist = {
    # "body_human": ['white']
}

parts_variant_blacklist = {
    "body_human": ['darkelf', 'darkelf_2', 'zombie'],
    "eyes": ["cyclope"]
    # "weapon_slash": ["pickaxe"]
}

minimum_parts = [
    "body/male/human",
    "eyes",
    "feet",
    "hair",
    "legs",
    "torso/armour",
    "torso/waist",
    "weapon"
]


forced_parts = [
    '/feet/armor'
    # '/feet/shoes'
]


part_blacklist = [
    '/feet/hoofs',
    '/hair/afro',
    '/hair/spiked_liberty',
    '/hair/spiked_liberty2',
    '/hair/spiked_beehive',
    '/hair/jewfro'
]

gendered_hair_blacklist = {
    "Male": ['long_tied', 'long_knot', 'loose', 'pigtail', 'pigtails_bangs', 'ponytail', 'princess', 'sara', 'shortknot', 'shoulderl', 'shoulderr', 'wavy', 'xlong', 'bangs_bun', 'long_messy', 'longknot', 'curtains_long', 'high_ponytail', 'curly', 'bangslong', 'long_messy2', 'long_band', 'lob', 'long_center_part', 'bob_side_part', 'ponytail2', 'curly_long', 'pigtails', 'braid', 'long', 'braid2', 'half_up', 'curly_short', 'bunches', 'bob'],
    "Female": ["afro", "balding", 'buzzcut', 'flat_top_fade', 'flat_top_straight', 'messy', 'messy1', 'messy2', 'messy3', 'natural', 'part2', 'single', 'spiked', 'spiked_porcupine', 'spiked2', 'twists_fade', 'twists_straight', 'curly', 'shorthawk', 'high_and_tight', 'longhawk']
}

def index_to_rect(image: Image.Image, index: int, section_size: int = 64) -> Tuple[int, int, int, int]:
    # Returns the rect of the index of a given image. Keep in mind this assumes the index lies within the given image, and that your section size is smaller than the image
    # Gets total number of sections in both dimensions
    total_x_sections = math.floor(image.width / section_size)

    # Gets the number of sections in each dimension corresponding to the desired index
    y_sections, x_sections = divmod(index, total_x_sections)

    # Gets the coordinates of the desired index's upper left corner
    origin_x = section_size * x_sections
    origin_y = section_size * y_sections

    return (origin_x, origin_y, origin_x + section_size, origin_y + section_size)


def image_to_frames(image: Image.Image, frame_numbers: List[int] = [104, 117, 130, 143]) -> List[Image.Image]:
    # Returns a list of frames from the given image
    # Gets the rectangle of every desired frame
    frame_rects = [index_to_rect(image, i) for i in frame_numbers]

    # Gets the regions from the image according to the frame rects
    frames = [image.crop(rect) for rect in frame_rects]

    return frames


def elem_of_path(input: str, index: int = -1, symbol: str = "/") -> str:
    if input[0] == symbol:
        input = input[1:]

    split_list = input.split(symbol)

    return split_list[index]


def strip_list_strings(input: List[str], before_index: int = -1, symbol: str = '/') -> List[str]:
    input = [i[1:] for i in input.copy() if i[0] == symbol]

    stripped_list = []
    for i in input:
        split_i = i.split(symbol)
        del split_i[before_index]
        stripped_list.append(f'/{symbol.join(split_i)}')

    return stripped_list


def traverse_path(structure, path: str, symbol: str = '/'):
    category_list = path.split(symbol)
    del category_list[-1]

    for category in category_list:
        structure = section_data(structure, category)

    return structure


def recurse_category(structure, category: str, gender: str = "male", symbol: str = '/') -> str:
    # Traverses the folder structure randomly from a starting category, excluding entries that lack the desired gender or are blacklisted.
    structures = [structure]
    categories = [category]

    path = ''
    while True:
        if symbol in category:
            structure = traverse_path(structure, category)
            category = elem_of_path(category)

        subcategories = section_data(structure, category)
        path += f'/{category}'

        if type(subcategories) == dict:
            subcategories: dict
            children_keys = list(subcategories.keys())
            category = None

            keys_to_remove = []
            # Remove items that are blacklisted
            if path in strip_list_strings(part_blacklist):
                blacklist_keys = [elem_of_path(part) for part in part_blacklist]
                for c_key in children_keys:
                    if c_key in blacklist_keys:
                        keys_to_remove.append(c_key)

            # Force the whitelisted key
            if path in strip_list_strings(forced_parts):
                forced_keys = [elem_of_path(part) for part in forced_parts]
                for c_key in children_keys:
                    if c_key in forced_keys:
                        category = c_key

            # Remove keys who's JSON files lack our desired gender
            # if all([type(subcategories[c_key]) == str for c_key in children_keys]):
            for c_key in children_keys:
                if type(subcategories[c_key]) == str:
                    json_filepath = f'sheet_definitions/{subcategories[c_key]}'
                    json_data = read_json(json_filepath)

                    json_keys = list(json_data.keys())
                    layer_keys = [k for k in json_keys if "layer" in k]

                    for l in layer_keys:
                        layer_data: dict = json_data[l]
                        if gender not in layer_data:
                            # print(f'Remove: {c_key}')
                            keys_to_remove.append(c_key)
                            break

            # Remove keys from the list
            for key in keys_to_remove:
                if key in children_keys:
                    children_keys.remove(key)

            # If the category is not forced, choose a random one
            if not category and children_keys:
                category = random.choice(children_keys)

            # If there are no keys, go to start of path and recurse again
            elif not children_keys:
                structure = structures[0]
                category = categories[0]
                continue

            path += f'/{category}'
            structure = subcategories
            structures.append(structure)
            categories.append(category)

        else:
            return subcategories


def files_from_json(filepath: str, gender: str = "female") -> List[Tuple[str, int]]:
    # Outputs sprite filepaths and their z positions from a json
    stripped_filepath = filepath.replace('.json', '')
    json_data = read_json(f'sheet_definitions/{filepath}')
    json_keys = list(json_data.keys())
    layer_keys = [k for k in json_keys if "layer" in k]

    files = []
    for l in layer_keys:
        # Get filepath of gender from layer, z position, and file variants
        layer_data = json_data[l]
        # print(filepath)
        layer_filepath = layer_data[gender]
        z_pos = layer_data["zPos"]
        variants = json_data["variants"]

        # Reformat some variant names to be consistent with file naming
        for i, v in enumerate(variants.copy()):
            variants[i] = v.replace(' ', '_')

        # Remove blacklisted variants
        chosen_variant = None
        if stripped_filepath in parts_variant_blacklist:
            blacklist = parts_variant_blacklist[stripped_filepath]
            if blacklist:
                for v in variants.copy():
                    if v in blacklist:
                        variants.remove(v)

        # Force whitelisted variants
        if stripped_filepath in parts_variant_whitelist:
            whitelist = parts_variant_whitelist[stripped_filepath]
            if whitelist:
                for v in variants.copy():
                    if v in whitelist:
                        chosen_variant = v
                        break

        # If variant is not forced, choose a random one
        if not chosen_variant:
            chosen_variant = random.choice(variants)

        chosen_filepath = f'spritesheets/{layer_filepath}/{chosen_variant}.png'
        chosen_filepath = chosen_filepath.replace('//', '/')

        files.append((chosen_filepath, z_pos))

    return files


def sort_by_z(input_list: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    # Sorts a list of filepath/z_pos tuples by the z_pos, ascending
    sorted_list = []
    for item in input_list:
        if sorted_list:
            for i, l in enumerate(sorted_list.copy()):
                _, z = l
                _, item_z = item
                if item_z > z and item not in sorted_list:
                    sorted_list.insert(i, item)

        else:
            sorted_list.append(item)

    sorted_list.reverse()
    return sorted_list


def random_sprite(part_structure: dict, parts: List[str] = minimum_parts, gender: str = "male"):
    gender = gender.lower()
    part_files = []
    for part in parts:
        part_json = recurse_category(part_structure, part, gender)
        part_files += files_from_json(part_json, gender)

    sorted_files = sort_by_z(part_files)
    return sorted_files


def list_to_field(input_list: List[str], seperator: str = '\n') -> str:
    return seperator.join(input_list)


def field_to_list(input_str: str, seperator: str = '\n') -> List[str]:
    if input_str:
        return input_str.split(seperator)
    else:
        return list()


def dict_to_field(input_dict: Dict[str, List[str]], key_seperator: str = ': ', line_seperator: str = '\n') -> str:
    input_keys = list(input_dict.keys())
    # print(input_keys)
    output_str = ''
    for i in input_keys:
        output_str += f'{i}{key_seperator}{input_dict[i]}{line_seperator}'
        # print(output_str)

    return output_str


def field_to_dict(input_str: str, key_seperator: str = ':', line_seperator: str = '\n') -> Dict[str, List[str]]:
    if input_str:
        dict_items = input_str.split(line_seperator)
        # print(dict_items)
        output_dict = {}
        for item in dict_items:
            stripped_item = item.replace(': ', ':')
            if stripped_item:
                item_data = stripped_item.split(key_seperator)
                list_value = item_data[1].strip('][').split(', ')
                for i, v in enumerate(list_value.copy()):
                    list_value[i] = v.replace("'", "")
                output_dict[item_data[0]] = list_value

        return output_dict

    else:
        return dict()


def image_from_parts(input_list: List[Image.Image]) -> Image.Image:
    output_image: Image.Image = None
    for i, img in enumerate(input_list):
        img = img.convert("RGBA")
        if i == 0:
            output_image = img
        else:
            output_image = output_image.convert("RGBA")
            output_image.paste(img, mask=img)
            # output_image = ImageChops.add(output_image, img)

    return output_image


def image_to_bytes(input_img: Image.Image):
    buf = io.BytesIO()
    input_img.save(buf, format=f'PNG')
    return buf.getvalue()


parts_layout = [
    [gui.Text('Base Parts')],
    [gui.Multiline(default_text=list_to_field(minimum_parts), size=(20, 3), key='parts')],
    [gui.Text('Parts Blacklist')],
    [gui.Multiline(default_text=list_to_field(part_blacklist), size=(20, 3), key='parts_blacklist')],
    [gui.Text('Forced Parts')],
    [gui.Multiline(default_text=list_to_field(forced_parts), size=(20, 3), key='forced_parts')],
    [gui.Text('Variant Blacklist')],
    [gui.Multiline(default_text=dict_to_field(parts_variant_blacklist), size=(20, 3), key='blacklist')],
    [gui.Text('Forced Variants')],
    [gui.Multiline(default_text=dict_to_field(parts_variant_whitelist), size=(20, 3), key='whitelist')]
]

part_structure = read_json('relevant_parts.json')
sprite_parts = random_sprite(part_structure, minimum_parts, "male")
sprite_images = [read_image(img) for img, _ in sprite_parts]
image = image_from_parts(sprite_images)
frames = image_to_frames(image)

preview_layout = [
    [gui.Image(image_to_bytes(frames[0]), key='Image0')],
    [gui.Image(image_to_bytes(frames[1]), key='Image1')],
    [gui.Image(image_to_bytes(frames[2]), key='Image2')],
    [gui.Image(image_to_bytes(frames[3]), key='Image3')],
    [gui.Text('Gender:'), gui.Combo(['Male', 'Female', 'Random'], default_value='Male', key='Gender')],
    [gui.Text('Prefix:'), gui.InputText(r'%Enemy-', key='FilePrefix', size=(10, 1))],
    [gui.Text('Amount:'), gui.InputText(1, key='SpritesToGen', size=(3, 1))],
    [gui.Checkbox('Gender Hairstyle Matching', True, key='hair')],
    [gui.Button('Preview'), gui.Button('Save') , gui.Button('Generate')]
]

gui_layout = [
    [gui.Frame('Body Parts', parts_layout), gui.Frame('Image Preview', preview_layout)],
    [gui.Text('Made by slackaduts')],
    [gui.Text("Made using sanderfrenken's fork of Gaurav0's LPC Generator")]
]


def main():
    sheet_frames: List[Image.Image] = []
    image: Image.Image = None

    def update_images():
        nonlocal sheet_frames
        nonlocal image
        global minimum_parts
        global part_blacklist
        global forced_parts
        global parts_variant_blacklist
        global parts_variant_whitelist
        minimum_parts = field_to_list(values['parts'])
        part_blacklist = field_to_list(values['parts_blacklist'])
        forced_parts = field_to_list(values['forced_parts'])
        parts_variant_blacklist = field_to_dict(values["blacklist"])
        parts_variant_whitelist = field_to_dict(values['whitelist'])

        genders = ['Male', 'Female']
        if values['Gender'] == 'Random':
            
            gender = random.choice(genders)
        else:
            gender = values['Gender']

        if values['hair']:
            for part in gendered_hair_blacklist[gender]:
                part_path = f'/hair/{part}'
                if part_path not in part_blacklist:
                    part_blacklist.append(part_path)

        else:
            for part in gendered_hair_blacklist[gender]:
                part_path = f'/hair/{part}'
                if part_path in part_blacklist:
                    part_blacklist.remove(part_path)

        sprite_parts = random_sprite(part_structure, minimum_parts, gender)
        # print(sprite_parts)
        sprite_images = [read_image(img) for img, _ in sprite_parts]
        image = image_from_parts(sprite_images)
        sheet_frames = image_to_frames(image)

        for i, img in enumerate(sheet_frames):
            window[f'Image{i}'].update(image_to_bytes(img))

    def save_image(index: int = 0):
        nonlocal image
        prefix = values['FilePrefix']
        gender = values['Gender']
        filepath = f'output/{prefix}{gender}{index}.png'
        if os.path.exists(filepath):
            os.remove(filepath)
            time.sleep(0.1)
        image.save(filepath)
        print(f'{prefix}{gender}{index}.png saved to /output/{prefix}{gender}{index}.png')

    gui.theme('Black')
    window = gui.Window('LPC Sprite Creator', gui_layout)

    event, values = window.read(timeout=0.1)
    update_images()
    while True:
        event, values = window.read()
        match event:
            case gui.WIN_CLOSED:
                break

            case 'Preview':
                update_images()

            case 'Generate':
                iterations = int(values['SpritesToGen'])
                for i in range(iterations):
                    update_images()
                    save_image(i)

                if iterations > 1:
                    print(f'--FINISHED SAVING {iterations} IMAGES--')
                else:
                    print('--FINISHED SAVING 1 IMAGE--')

            case 'Save':
                save_image()
                print('--FINISHED SAVING 1 IMAGE--')


if __name__ == "__main__":
    main()