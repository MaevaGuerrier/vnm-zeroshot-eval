import os
from PIL import Image
import torchvision.transforms as T
import argparse
import random
import shutil

import albumentations as A
import cv2


def get_transform(augmentation_type: str):
    if "_" in augmentation_type:
        # The augmentation type may have a specific suffix, e.g., "rain_heavy"
        # We only want the main type, e.g., "rain"
        # The specific suffix is handled in the transform function
        augmentation_type = augmentation_type.split("_")[0]

    specific_transform = globals()[f"insert_{augmentation_type}"]
    print(f"Using transform: {specific_transform}")
    return specific_transform

class TrajectoryImageAugmentor:
    def __init__(self, topomap_dir:str, topomap_name:str, augmentation_type:str, seed:int=42):
        """
        Args:
            topomap_dir (str): Path to the topomap directory.
            transforms_dict (dict): Maps transform name to a torchvision transform.
                                    Example: {'brightness': brightness_transform, ...}
        """
        self.topomap_dir = topomap_dir
        self.topomap_name = topomap_name
        self.augmentation_type = augmentation_type
        self.transform = get_transform(augmentation_type)
        self.seed = seed
        

    def _sort_frame_paths(self, frame_path):
        """
        Sorts frame paths based on the numeric part of the filename.
        Assumes filenames are in the format 'image1.{extension}', 'image2.{extension}', etc.
        """
        return sorted(frame_path, key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('.')[0]))

    def augment_and_save(self):
        # Go through each trajectory directory_name/traj_name_dir
        img_to_process = os.path.join(self.topomap_dir, self.topomap_name)

        # Retrieve all image files in the trajectory directory
        frame_paths = sorted([
            os.path.join(img_to_process, fname)
            for fname in os.listdir(img_to_process)
            if fname.endswith((".png", ".jpg", ".jpeg"))
        ])

        frame_paths = self._sort_frame_paths(frame_paths)

        new_dir_name = f"{self.topomap_name}_{self.augmentation_type}"
        output_dir = os.path.join(self.topomap_dir, new_dir_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if "_" in self.augmentation_type:
            extra_aug = self.augmentation_type.split("_")[1] 
        else:
            extra_aug = None

        for frame_path in frame_paths:
            # print(f"frame path {frame_path}")
            # image = Image.open(frame_path) #.convert("RGB")
            image = cv2.imread(frame_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_aug = Image.fromarray(self.transform(image_rgb, **({"extra_type": extra_aug} if extra_aug else {})))
            frame_filename = os.path.basename(frame_path)
            image_aug.save(os.path.join(output_dir, frame_filename))


        print(f"[✓] Saved: {output_dir}")


def paste_object(orig_image, object_image, max_scale=0.5):
    """
    Args:
        background (PIL.Image): the trajectory frame
        object_image (PIL.Image): RGBA image (with alpha channel)
        max_scale (float): max size of pasted object relative to background

    Returns:
        Composited image
    """
    bg_w, bg_h = orig_image.size
    obj_w, obj_h = object_image.size

    # Scale object randomly (not too large)
    scale_factor = random.uniform(0.2, max_scale)
    new_w = int(bg_w * scale_factor)
    new_h = int(obj_h * (new_w / obj_w))
    object_image = object_image.resize((new_w, new_h), resample=Image.BILINEAR)

    # Choose random location
    x = random.randint(0, bg_w - new_w)
    y = random.randint(0, bg_h - new_h)

    # Paste with transparency
    orig_image.paste(object_image, (x, y), object_image)  # third arg = mask from alpha
    return orig_image


# Image data augmentation functions
def insert_human(image):
    pass


def insert_object(object_folder, max_scale=0.5):
    """
    Returns a transform that pastes a random object from `object_folder` onto an image.
    """

    object_paths = [
        os.path.join(object_folder, f)
        for f in os.listdir(object_folder)
        if f.endswith(('.png', '.jpg', '.jpeg'))
    ]

    def transform(background):
        bg = background.convert("RGB")
        obj_path = random.choice(object_paths)
        obj = Image.open(obj_path).convert("RGBA")

        # Optional: segmentation mask if needed
        if obj.mode != "RGBA":
            obj = obj.convert("RGBA")

        return paste_object(bg, obj, max_scale=max_scale)

    return transform


# BLUR APPEARS TO BE TOO SIMILAR TO DEGRADATION OF IMAGE DUE TO DOWNSCALING WITH VALUE 13, 23, trying stronger values
def insert_blur(image:Image, blur_intensity:int=33):
    # assert blur_intensity > 0, and must be odd
    assert blur_intensity > 0 and blur_intensity % 2 == 1, "Blur intensity must be a positive odd integer."
    transform = A.Compose([
        A.Blur(
            blur_limit=[blur_intensity, blur_intensity], # Blur limit must be 0 or odd. see https://errors.pydantic.dev/2.10/v/value_error
            p=1, # Ensure is always applied (Probability of applying the transform)
        )
    ])
    return transform(image=image)["image"]

def insert_fog(image:Image):
    transform = A.Compose([
        A.RandomFog(
            alpha_coef=0.25,
            fog_coef_range=[0.5, 0.7],
            p=1, # Ensure is always applied (Probability of applying the transform)
        )
    ])
    return transform(image=image)["image"]

# https://explore.albumentations.ai/transform/RandomRain
# drop_lenght of 50 appears to be a good default for realistic rain
def insert_rain(image:Image, rain_type:str='default', drop_length:int=50, **kwargs):

    if kwargs.get("extra_type") is not None:
        rain_type = kwargs["extra_type"]
        
    assert rain_type in ['default', 'heavy', 'drizzle', 'torrential'], "Invalid rain type specified. Use one of: default, heavy, drizzle, torrential."
    transform = A.Compose(
        
        [A.RandomRain(
            slant_range=[-1, 1],
            drop_length=drop_length,
            drop_width=1,
            drop_color=[200, 200, 200],
            blur_value=7,
            brightness_coefficient=0.7,
            rain_type=rain_type,
            p=1, # Ensure rain is always applied (Probability of applying the transform)
            
        )],
        
    )

    return transform(image=image)["image"] # https://github.com/albumentations-team/albumentations?tab=readme-ov-file#a-simple-example


def insert_brightness(image:Image):
    transform = A.Compose([
        A.RandomBrightnessContrast(
            brightness_limit=[-0.2, 0.2],
            contrast_limit=[-0.2, 0.2],
            brightness_by_max=True,
            ensure_safe_range=False,
            p=1, # Ensure is always applied (Probability of applying the transform)
        )
    ])
    return transform(image=image)["image"]

def insert_sunFlare(image:Image, method:str="overlay", **kwargs):

    if kwargs.get("extra_type") is not None:
        method = "physics_based" if "physic" in kwargs["extra_type"] else kwargs["extra_type"]
    assert method in ["overlay", "physics_based"], "Invalid method specified. Use 'overlay' or 'physics_based'."

    transform = A.Compose([
        A.RandomSunFlare(
            flare_roi=[0, 0, 1, 0.5],
            src_radius=400,
            src_color=[255, 255, 255],
            angle_range=[0, 1],
            num_flare_circles_range=[6, 10],
            method=method,
            p=1, # Ensure is always applied (Probability of applying the transform)
        )
    ])
    return transform(image=image)["image"]




# Add new custom transforms here


# TODO HANDLE LOGIC FOR TOPOMAP IMAGE ONLY MAKE IT MANDATORY HAS IT DEPENDS ON ALGO MAYBE 

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visual Navigation Transformer")

    # Logic here is augmentation type with custom choices eg rain types used the notation augType_specific
    # Note that the transform method should handle the specific suffixes names if it differs from the choices
    # e.g, sun_physic, thus physic which is the extra type is actually named physics_based in the transform function (see Albumentations docs)
    # However, the main type is still the same, e.g., rain, sun, etc.
    choices=["brightness", "human", "object", "blur", "fog", "sunFlare_overlay", "sunFlare_physic", "rain", "rain_heavy", "rain_drizzle", "rain_torrential", "all"]

    # project setup
    parser.add_argument(
        "--augmentation_type",
        "-a",
        default="all",
        type=str,
        help="Type of augmentation to apply (e.g., brigh, noise, human, object, blur, all)",
        choices=choices
    )

    parser.add_argument(
        "--topomap_dir",
        "-d",
        type=str,
        required=True,
        help="Path to folder containing the topomap."
    )

    parser.add_argument(
        "--topomap_name",
        "-n",
        type=str,
        required=True,
        help="Specific topomap (image) to augment."
    )


    args = parser.parse_args()

    assert args.augmentation_type in choices, "Invalid augmentation type specified."
    # if args.augmentation_type in ["human", "object"]:
    #     # TODO USE PATH LIB TO NOT HARDCORE PATH 
    #     # TODO AUTO CHECK with train/vint_train/data/data_config.yaml check camera intrinsic
    #     assert args.topomap_dir.lower() in ["recon"], "Human and object augmentation only supported for dataset with camera intrinsic provided."


    # TODO Handle the all logic here instead of in the augmentor class

    # topomap_dir = os.path.join(args.topomap_dir, args.specific_dataset) if args.specific_dataset != "all" else args.topomap_dir
    # if not os.path.exists(topomap_dir):
    #     raise FileNotFoundError(f"Dataset directory {topomap_dir} does not exist.")

    augmentor = TrajectoryImageAugmentor(
        topomap_dir=args.topomap_dir,
        topomap_name=args.topomap_name,
        augmentation_type=args.augmentation_type
    )

    augmentor.augment_and_save()

