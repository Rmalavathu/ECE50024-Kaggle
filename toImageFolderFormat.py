import os
import shutil
import pandas as pd

# Path to the folder containing the images
image_folder_path = "train"

# Path to the CSV file containing the labels corresponding to the images
labels_csv_path = "purdue-face-recognition-challenge-2024/train.csv"

# Path to the CSV file containing all categories
categories_csv_path = "purdue-face-recognition-challenge-2024/category.csv"

# Read labels CSV file
labels_df = pd.read_csv(labels_csv_path)

# Read categories CSV file
categories_df = pd.read_csv(categories_csv_path)

# Create folders for each category
for category in categories_df["Category"]:
    os.makedirs(os.path.join(image_folder_path, category), exist_ok=True)

# Move images to respective folders based on the label-to-category mapping
for index, row in labels_df.iterrows():
    file_name = row["File Name"]
    category_name = row["Category"]

    print(file_name, category_name)
    
    source_path = os.path.join(image_folder_path, file_name)
    destination_path = os.path.join(image_folder_path, category_name, file_name)
    shutil.move(source_path, destination_path)
