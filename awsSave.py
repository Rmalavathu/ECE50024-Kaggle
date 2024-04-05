#Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#PDX-License-Identifier: MIT-0 (For details, see https://github.com/awsdocs/amazon-rekognition-developer-guide/blob/master/LICENSE-SAMPLECODE.)

import boto3
import os
import csv
import random 

def recognize_celebrities(photo):
    
    session = boto3.Session(profile_name='default')
    client = session.client('rekognition')

    with open(photo, 'rb') as image:
        response = client.recognize_celebrities(Image={'Bytes': image.read()})

    return response['CelebrityFaces']

def extract_number(filename):
    # Extract the number from the filename
    return int(''.join(filter(str.isdigit, filename)))

def main():
    directory = 'testImages2_cropped/BradPitt'
    files= []
    for file in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, file)):
            files.append(file)
    files.sort(key=extract_number)
    print(len(files))
    name_map = {}
    id_map = {}

    # Open the CSV file
    with open('purdue-face-recognition-challenge-2024/category.csv', newline='') as csvfile:
        # Read the CSV file
        reader = csv.DictReader(csvfile)
        
        # Iterate over each row in the CSV file
        for row in reader:
            # Add the name to the dictionary with the number as key
            name_map[row['Category']] = int(row[''])
            id_map[int(row[''])] = row['Category']

    # print(name_map)
    print(id_map)

    # photo = 'testImages2_cropped/BradPitt/7.jpg'
    
    predictions = []
    for x in files:
        photo = os.path.join(directory, x)
        try:
            celeb = recognize_celebrities(photo)[0]
            if (len(celeb) == 1):
                if(str(celeb['Name']) in name_map.keys()):
                    celeb_name = str(celeb['Name'])
                    # celeb_name = name_map[celeb_name]
                else:
                    celeb_name = random.randint(0, 99)
                    celeb_name = id_map[celeb_name]
            elif (len(celeb) == 0):
                    celeb_name = random.randint(0, 99)
                    celeb_name = id_map[celeb_name]
            else:
                count = 0
                for celebrity in celeb:
                    if(str(celeb['Name']) in name_map.keys()):
                        celeb_name = str(celeb['Name'])
                        # celeb_name = name_map[celeb_name]
                        count += 1
                        break
                if count == 0:
                    celeb_name = random.randint(0, 99)
                    celeb_name = id_map[celeb_name]
        except:
            celeb_name = random.randint(0, 99)
            celeb_name = id_map[celeb_name]
        print(x)
        predictions.append(celeb_name)

    print(predictions)

    with open('predictions.csv', 'w', newline='') as csvfile:
        fieldnames = ['Id', 'Category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for idx in range(len(predictions)):
            # image, image_name = test_dataset[idx]  # Retrieve image and image name
            predicted_label = predictions[idx]
            writer.writerow({'Id': idx, 'Category': predicted_label})

    print(len(predictions))


if __name__ == "__main__":
    main()