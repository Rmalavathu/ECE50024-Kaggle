from facenet_pytorch import MTCNN, InceptionResnetV1, fixed_image_standardization, training
import torch
from torch.utils.data import DataLoader, SubsetRandomSampler
from torch.utils.data import Dataset
from torchvision import datasets
import numpy as np
import pandas as pd
import os
from PIL import Image
import cv2
import torchvision.transforms as transforms
from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import MultiStepLR
from torch import optim
import csv

workers = 0
batch_size = 64
epochs = 12

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
# # print('Running on device: {}'.format(device))

# mtcnn = MTCNN(select_largest=False, device=device)

# # # image_path = "testImages2/BradPitt/133.jpg"

# # # image = cv2.imread(image_path)
# # # image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
# # # pil_image = Image.fromarray(image_rgb)

# # # resized_image = pil_image.resize((512, 512), Image.ANTIALIAS)

# # # mtcnn(resized_image, save_path="test2.jpg")

data_dir = "train"

dataset = datasets.ImageFolder(data_dir, transform=transforms.Resize((512, 512)))

# # print(len(dataset))
# # # dataset.samples = [
# # #     (p, p.replace(data_dir, data_dir + '_cropped'))
# # #         for p, _ in dataset.samples
# # # ]
        
# # # loader = DataLoader(
# # #     dataset,
# # #     num_workers=workers,
# # #     batch_size=batch_size,
# # #     collate_fn=training.collate_pil
# # # )

# # # for i, (x, y) in enumerate(loader):
# # #     for image, save_path in zip(x,y):
# # #         mtcnn(image, save_path=save_path)
# # #     print('\rBatch {} of {}'.format(i + 1, len(loader)), end='')
    
# # # # Remove mtcnn to reduce GPU memory usage
# # # del mtcnn

resnet = InceptionResnetV1(
    classify=True,
    pretrained='vggface2',
    num_classes=100
).to(device)

print(len(dataset.class_to_idx))
optimizer = optim.Adam(resnet.parameters(), lr=0.001)
scheduler = MultiStepLR(optimizer, [4, 8])

trans = transforms.Compose([
    np.float32,
    transforms.ToTensor(),
    fixed_image_standardization
])
dataset = datasets.ImageFolder(data_dir + '_cropped', transform=trans)
img_inds = np.arange(len(dataset))
np.random.shuffle(img_inds)
train_inds = img_inds[:int(0.8 * len(img_inds))]
val_inds = img_inds[int(0.8 * len(img_inds)):]

print(dataset.class_to_idx)

# output_file = "actors.csv"

# # Write the dictionary to a CSV file
# with open(output_file, 'w', newline='') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow(['Name', 'Number'])  # Write header
#     for name, number in dataset.class_to_idx.items():
#         writer.writerow([name, number])

train_loader = DataLoader(
    dataset,
    num_workers=workers,
    batch_size=batch_size,
    sampler=SubsetRandomSampler(train_inds)
)
val_loader = DataLoader(
    dataset,
    num_workers=workers,
    batch_size=batch_size,
    sampler=SubsetRandomSampler(val_inds)
)

loss_fn = torch.nn.CrossEntropyLoss()
metrics = {
    'fps': training.BatchTimer(),
    'acc': training.accuracy
}

writer = SummaryWriter()
writer.iteration, writer.interval = 0, 10

print('\n\nInitial')
print('-' * 10)
resnet.eval()
training.pass_epoch(
    resnet, loss_fn, val_loader,
    batch_metrics=metrics, show_running=True, device=device,
    writer=writer
)

for epoch in range(epochs):
    print('\nEpoch {}/{}'.format(epoch + 1, epochs))
    print('-' * 10)

    resnet.train()
    training.pass_epoch(
        resnet, loss_fn, train_loader, optimizer, scheduler,
        batch_metrics=metrics, show_running=True, device=device,
        writer=writer
    )

    resnet.eval()
    training.pass_epoch(
        resnet, loss_fn, val_loader,
        batch_metrics=metrics, show_running=True, device=device,
        writer=writer
    )

writer.close()

resnet.eval()

resnet = torch.load('saved_model_big.pth')  # Load your model here

# Set the model to evaluation mode
resnet.eval()

# predictions = []

# image_path = "testImages2_cropped/BradPitt/7.jpg"

# image = cv2.imread(image_path)
# image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
# pil_image = Image.fromarray(image_rgb)

# trans = transforms.Compose([
#     np.float32,
#     transforms.ToTensor(),
#     fixed_image_standardization
# ])
# transo = trans(image)
# print(resnet(transo))

data_dir = "testImages2_cropped"


# trans = transforms.Compose([
#     np.float32,
#     transforms.ToTensor(),
#     fixed_image_standardization
# ])

# Create the test dataset
test_dataset = datasets.ImageFolder(data_dir, transform=trans)

# Create a data loader
batch_size = 64
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

with torch.no_grad():
    for images, _ in test_loader:
        images = images.to(device)
        outputs = resnet(images)
        _, predicted = torch.max(outputs, 1)
        # Get the file names corresponding to the current batch
        file_names = [test_dataset.imgs[i][0] for i in range(len(test_dataset.imgs))]
        
        # Add file names and predictions to the predictions list
        for file_name, prediction in zip(file_names, predicted.cpu().numpy()):
            predictions.append((file_name, prediction))
print(predictions)

# predictions = [60, 34, 50, 7, 58, 85, 59, 85, 75, 62, 50, 35, 92, 52, 41, 13, 19, 8, 4, 86, 72, 70, 54, 94, 7, 69, 19, 84, 37, 61, 11, 57, 0, 11, 89, 97, 98, 3, 48, 7, 20, 58, 29, 17, 36, 99, 49, 90, 45, 33, 91, 38, 91, 24, 40, 58, 88, 30, 40, 7, 48, 31, 90, 30, 11, 82, 70, 45, 35, 53, 77, 89, 13, 85, 24, 3, 84, 88, 1, 56, 74, 73, 8, 41, 67, 74, 29, 22, 19, 65, 70, 69, 22, 67, 58, 48, 69, 34, 31, 24, 3, 6, 6, 41, 65, 75, 80, 74, 62, 66, 60, 56, 18, 62, 77, 98, 89, 98, 44, 96, 99, 14, 70, 38, 2, 35, 10, 84, 60, 53, 82, 62, 57, 51, 87, 26, 80, 57, 57, 30, 19, 79, 31, 57, 28, 12, 23, 44, 80, 91, 46, 30, 58, 5, 98, 62, 2, 4, 87, 52, 1, 90, 36, 98, 68, 68, 22, 70, 65, 40, 93, 73, 25, 71, 42, 15, 45, 80, 58, 87, 97, 21, 3, 87, 45, 57, 6, 6, 33, 45, 68, 76, 14, 81, 57, 75, 76, 58, 54, 98, 57, 72, 51, 7, 14, 12, 93, 77, 80, 96, 0, 30, 58, 21, 26, 98, 98, 45, 32, 88, 36, 48, 54, 16, 92, 58, 74, 50, 15, 39, 75, 78, 22, 96, 35, 34, 72, 14, 82, 79, 1, 57, 67, 94, 35, 73, 32, 1, 48, 29, 46, 51, 75, 88, 25, 75, 62, 76, 27, 97, 93, 3, 15, 67, 1, 35, 29, 72, 38, 60, 94, 84, 72, 27, 93, 92, 55, 91, 49, 62, 90, 76, 72, 75, 1, 30, 45, 64, 48, 92, 47, 42, 87, 43, 76, 24, 61, 50, 58, 70, 39, 0, 25, 35, 43, 66, 70, 2, 88, 35, 35, 54, 4, 86, 0, 58, 36, 93, 67, 27, 33, 86, 71, 53, 95, 14, 98, 65, 77, 91, 37, 67, 44, 41, 98, 74, 75, 48, 68, 8, 17, 57, 5, 76, 97, 80, 5, 58, 28, 18, 7, 14, 1, 0, 23, 24, 64, 72, 50, 74, 28, 75, 93, 94, 92, 51, 99, 44, 56, 42, 83, 33, 2, 62, 79, 14, 50, 55, 50, 51, 65, 62, 22, 2, 97, 52, 46, 89, 78, 90, 77, 6, 92, 3, 89, 84, 21, 62, 94, 30, 19, 89, 30, 59, 25, 42, 57, 47, 68, 69, 67, 72, 6, 17, 52, 48, 49, 59, 0, 7, 80, 11, 25, 57, 6, 97, 96, 93, 50, 32, 74, 32, 38, 41, 37, 77, 80, 9, 44, 95, 3, 38, 33, 57, 97, 41, 85, 5, 89, 67, 73, 16, 25, 28, 65, 2, 93, 15, 32, 91, 95, 40, 60, 21, 8, 87, 87, 9, 83, 59, 4, 14, 72, 82, 99, 78, 43, 41, 82, 49, 55, 36, 60, 63, 77, 45, 18, 85, 77, 40, 92, 18, 90, 24, 84, 82, 96, 88, 50, 7, 43, 20, 84, 35, 65, 39, 8, 46, 20, 23, 74, 11, 87, 98, 1, 60, 23, 7, 97, 2, 11, 29, 2, 64, 48, 30, 34, 90, 53, 3, 8, 77, 93, 77, 25, 41, 16, 39, 3, 46, 19, 11, 80, 92, 90, 6, 1, 44, 14, 83, 98, 8, 66, 43, 47, 22, 27, 86, 17, 87, 21, 64, 56, 83, 87, 27, 90, 74, 11, 2, 45, 84, 80, 86, 74, 74, 14, 63, 22, 92, 98, 95, 92, 41, 23, 2, 0, 43, 14, 81, 83, 2, 67, 85, 8, 39, 11, 69, 36, 20, 27, 4, 80, 37, 58, 96, 48, 22, 80, 75, 75, 46, 32, 86, 48, 97, 78, 45, 70, 20, 72, 47, 39, 68, 3, 6, 36, 16, 80, 64, 20, 67, 46, 29, 11, 88, 97, 18, 34, 82, 41, 0, 34, 82, 66, 82, 84, 9, 15, 96, 31, 15, 24, 92, 44, 4, 74, 51, 32, 50, 54, 73, 15, 79, 17, 14, 32, 28, 19, 31, 61, 98, 58, 16, 52, 41, 80, 96, 84, 66, 17, 37, 90, 60, 15, 72, 35, 53, 84, 62, 88, 50, 19, 4, 71, 49, 98, 26, 14, 9, 73, 59, 20, 46, 63, 32, 41, 25, 34, 60, 53, 21, 94, 10, 37, 97, 59, 14, 90, 66, 65, 47, 94, 67, 35, 53, 80, 57, 10, 7, 60, 61, 85, 42, 63, 4, 41, 92, 33, 71, 41, 32, 79, 12, 30, 34, 40, 14, 90, 64, 63, 86, 7, 41, 52, 56, 52, 80, 82, 76, 10, 5, 51, 94, 90, 51, 2, 82, 12, 15, 99, 61, 6, 47, 44, 60, 4, 78, 36, 14, 28, 37, 63, 35, 40, 15, 89, 72, 97, 79, 87, 6, 32, 53, 94, 33, 47, 4, 27, 34, 69, 48, 21, 96, 28, 72, 80, 27, 79, 77, 20, 24, 49, 17, 3, 87, 46, 63, 7, 55, 33, 47, 34, 8, 90, 81, 41, 34, 2, 28, 34, 69, 75, 47, 9, 57, 70, 71, 36, 32, 80, 19, 1, 44, 20, 5, 55, 89, 17, 55, 40, 21, 52, 81, 11, 99, 95, 31, 97, 99, 40, 13, 7, 98, 2, 11, 19, 59, 68, 37, 98, 27, 17, 97, 36, 53, 79, 24, 83, 75, 84, 38, 97, 87, 87, 48, 75, 41, 30, 54, 10, 16, 95, 32, 26, 85, 20, 19, 40, 85, 71, 76, 36, 66, 33, 42, 72, 68, 90, 27, 16, 98, 10, 41, 78, 98, 17, 23, 6, 24, 6, 21, 93, 60, 29, 22, 49, 77, 93, 44, 81, 54, 41, 45, 10, 22, 47, 42, 98, 35, 4, 94, 38, 98, 60, 21, 21, 22, 11, 95, 43, 95, 99, 10, 7, 8, 64, 60, 16, 81, 78, 19, 60, 57, 34, 66, 16, 94, 38, 44, 20, 1, 71, 58, 34, 49, 31, 19, 50, 83, 13, 33, 45, 44, 97, 42, 74, 27, 30, 1, 40, 39, 99, 81, 61, 8, 72, 98, 44, 34, 22, 37, 86, 20, 71, 92, 31, 33, 70, 29, 77, 88, 34, 28, 31, 36, 83, 15, 6, 58, 79, 5, 34, 45, 57, 52, 35, 78, 55, 15, 90, 81, 53, 1, 20, 56, 51, 13, 99, 5, 89, 52, 60, 26, 85, 53, 51, 51, 64, 7, 64, 90, 32, 41, 1, 96, 38, 23, 94, 13, 35, 4, 66, 40, 4, 52, 89, 3, 34, 2, 33, 71, 26, 52, 14, 24, 60, 88, 72, 46, 75, 74, 8, 35, 45, 18, 12, 79, 63, 83, 14, 47, 49, 20, 51, 93, 6, 30, 33, 70, 97, 71, 75, 62, 27, 64, 72, 24, 54, 42, 79, 83, 9, 67, 68, 39, 30, 22, 24, 78, 81, 27, 55, 81, 90, 98, 80, 6, 60, 19, 10, 76, 59, 16, 26, 47, 63, 5, 93, 88, 11, 56, 47, 51, 62, 49, 90, 19, 31, 33, 8, 33, 35, 96, 82, 72, 89, 98, 80, 89, 90, 34, 79, 49, 30, 22, 72, 69, 18, 91, 64, 36, 77, 67, 57, 91, 55, 40, 96, 23, 1, 99, 29, 66, 38, 34, 21, 90, 99, 4, 29, 58, 38, 87, 38, 53, 47, 91, 5, 93, 57, 78, 89, 23, 11, 47, 93, 79, 43, 80, 43, 76, 21, 33, 53, 0, 0, 32, 94, 94, 47, 50, 63, 62, 68, 42, 97, 73, 57, 38, 29, 52, 87, 12, 33, 72, 98, 67, 98, 19, 72, 62, 80, 91, 4, 2, 32, 97, 31, 65, 83, 44, 84, 19, 0, 97, 49, 65, 28, 56, 84, 59, 41, 57, 17, 34, 79, 95, 65, 90, 1, 91, 43, 86, 1, 1, 52, 58, 87, 75, 27, 26, 65, 9, 46, 8, 43, 75, 19, 68, 93, 33, 18, 35, 29, 91, 60, 8, 71, 36, 92, 18, 1, 44, 49, 35, 16, 4, 26, 36, 69, 65, 82, 82, 1, 21, 65, 76, 5, 98, 25, 32, 5, 60, 96, 68, 30, 63, 95, 19, 4, 91, 54, 36, 73, 83, 50, 34, 48, 23, 8, 48, 31, 58, 58, 87, 14, 3, 94, 64, 68, 55, 37, 38, 53, 87, 65, 67, 91, 8, 82, 88, 6, 70, 27, 42, 94, 41, 85, 5, 40, 11, 76, 19, 59, 74, 73, 21, 71, 28, 48, 6, 50, 98, 59, 15, 81, 5, 86, 84, 70, 83, 65, 12, 58, 99, 17, 97, 39, 45, 61, 62, 52, 68, 76, 23, 90, 8, 23, 32, 78, 65, 59, 34, 11, 36, 63, 15, 90, 22, 23, 5, 67, 17, 9, 64, 92, 26, 51, 91, 60, 73, 63, 23, 0, 53, 79, 28, 36, 24, 39, 76, 21, 31, 36, 9, 5, 16, 66, 93, 1, 22, 81, 22, 68, 65, 25, 73, 63, 32, 7, 9, 59, 61, 0, 24, 3, 59, 50, 35, 43, 6, 11, 96, 76, 45, 66, 76, 46, 5, 35, 89, 88, 22, 97, 0, 47, 3, 58, 90, 80, 73, 77, 76, 58, 11, 21, 19, 63, 50, 59, 73, 53, 55, 98, 4, 14, 85, 96, 74, 50, 68, 67, 8, 34, 55, 30, 85, 46, 90, 78, 44, 46, 94, 7, 28, 17, 18, 31, 66, 37, 11, 88, 95, 36, 5, 31, 62, 8, 2, 42, 68, 59, 60, 93, 42, 72, 89, 36, 3, 1, 28, 41, 30, 3, 15, 34, 68, 97, 20, 87, 45, 57, 94, 94, 49, 20, 15, 90, 60, 55, 5, 69, 8, 51, 3, 89, 3, 97, 0, 52, 35, 71, 56, 68, 58, 87, 66, 97, 81, 45, 76, 65, 40, 85, 91, 15, 89, 25, 64, 40, 32, 81, 3, 39, 97, 3, 62, 38, 10, 74, 42, 65, 22, 33, 83, 31, 47, 83, 28, 70, 11, 53, 20, 93, 80, 17, 50, 66, 8, 73, 39, 60, 93, 45, 11, 84, 9, 41, 44, 35, 19, 48, 3, 74, 34, 42, 96, 43, 9, 49, 13, 46, 83, 86, 85, 70, 84, 21, 67, 71, 45, 42, 74, 77, 57, 48, 74, 15, 0, 31, 24, 41, 53, 48, 2, 20, 93, 28, 39, 65, 51, 22, 69, 63, 37, 76, 61, 91, 45, 88, 50, 35, 36, 74, 76, 27, 92, 45, 76, 80, 45, 48, 34, 55, 14, 39, 90, 80, 84, 92, 78, 69, 6, 74, 38, 33, 54, 39, 26, 24, 56, 86, 36, 84, 50, 83, 14, 74, 57, 20, 75, 51, 6, 28, 66, 60, 68, 32, 19, 67, 81, 77, 75, 89, 98, 67, 94, 0, 69, 67, 53, 30, 13, 64, 39, 21, 39, 32, 27, 70, 71, 75, 49, 12, 11, 15, 71, 52, 3, 95, 2, 75, 61, 8, 59, 53, 99, 8, 66, 22, 31, 11, 58, 57, 31, 70, 87, 9, 76, 13, 69, 18, 36, 20, 95, 51, 7, 97, 53, 82, 25, 32, 71, 43, 5, 41, 73, 60, 20, 17, 18, 27, 73, 42, 70, 42, 70, 72, 80, 12, 56, 1, 30, 82, 52, 10, 45, 38, 72, 49, 94, 15, 81, 51, 94, 38, 41, 76, 2, 52, 47, 46, 24, 75, 80, 74, 51, 43, 27, 19, 33, 63, 90, 4, 29, 75, 94, 50, 53, 0, 14, 18, 34, 15, 19, 37, 63, 33, 84, 86, 86, 67, 16, 56, 5, 23, 94, 12, 83, 6, 59, 30, 30, 41, 86, 67, 79, 89, 74, 1, 53, 42, 1, 20, 16, 47, 26, 30, 75, 78, 95, 39, 90, 22, 73, 61, 31, 38, 8, 58, 39, 75, 90, 3, 93, 3, 50, 79, 91, 34, 83, 41, 83, 19, 33, 15, 3, 52, 32, 27, 23, 45, 30, 13, 17, 32, 91, 85, 31, 93, 92, 28, 71, 3, 97, 84, 10, 12, 45, 79, 3, 60, 7, 98, 64, 75, 40, 59, 95, 98, 54, 51, 32, 87, 24, 87, 32, 90, 45, 46, 65, 49, 27, 73, 33, 53, 20, 1, 74, 54, 1, 76, 72, 9, 74, 23, 33, 17, 23, 56, 86, 18, 0, 55, 34, 81, 31, 58, 58, 80, 9, 7, 18, 3, 34, 54, 51, 9, 10, 99, 51, 20, 32, 1, 69, 95, 48, 11, 90, 44, 24, 48, 9, 42, 24, 41, 41, 14, 29, 37, 40, 18, 64, 0, 60, 95, 15, 37, 49, 53, 31, 72, 22, 32, 47, 5, 93, 77, 49, 42, 43, 18, 80, 98, 52, 26, 37, 67, 55, 64, 34, 95, 34, 17, 30, 86, 42, 41, 86, 16, 39, 31, 59, 80, 21, 40, 85, 78, 54, 37, 49, 8, 86, 18, 98, 37, 73, 55, 89, 57, 83, 38, 53, 74, 90, 71, 66, 76, 44, 91, 20, 10, 19, 73, 88, 35, 91, 31, 7, 9, 49, 42, 21, 50, 44, 60, 66, 83, 66, 65, 40, 69, 80, 92, 57, 71, 31, 76, 71, 8, 69, 53, 73, 87, 99, 5, 21, 74, 55, 75, 25, 64, 1, 33, 40, 91, 34, 47, 68, 25, 17, 36, 60, 15, 70, 85, 99, 32, 50, 4, 8, 63, 20, 91, 1, 61, 16, 46, 59, 82, 28, 29, 1, 76, 51, 6, 38, 23, 35, 14, 99, 82, 22, 61, 38, 48, 49, 97, 56, 46, 53, 75, 31, 14, 90, 85, 84, 70, 66, 50, 20, 33, 13, 15, 69, 42, 83, 15, 24, 3, 28, 41, 25, 91, 99, 14, 0, 63, 1, 30, 44, 25, 6, 47, 17, 5, 61, 98, 91, 49, 58, 21, 6, 99, 34, 96, 66, 7, 96, 18, 95, 69, 61, 85, 21, 3, 31, 23, 47, 63, 69, 94, 58, 28, 14, 59, 17, 63, 38, 64, 49, 75, 59, 42, 96, 24, 49, 14, 33, 96, 5, 97, 30, 42, 43, 80, 7, 32, 64, 12, 52, 76, 37, 74, 20, 84, 60, 58, 18, 9, 36, 29, 41, 61, 35, 72, 83, 69, 16, 42, 95, 27, 91, 2, 69, 7, 57, 77, 2, 58, 16, 2, 50, 79, 52, 65, 94, 35, 65, 83, 37, 27, 62, 52, 88, 73, 44, 11, 41, 85, 84, 78, 68, 69, 73, 0, 50, 79, 30, 91, 61, 19, 53, 96, 90, 90, 43, 50, 56, 93, 98, 3, 23, 62, 35, 12, 56, 1, 48, 56, 19, 77, 8, 62, 33, 19, 85, 85, 93, 22, 52, 99, 9, 90, 27, 27, 15, 79, 27, 96, 15, 49, 44, 27, 2, 62, 61, 22, 42, 47, 41, 77, 73, 54, 61, 48, 1, 63, 12, 82, 10, 19, 4, 38, 25, 27, 21, 60, 61, 51, 62, 98, 54, 58, 68, 34, 86, 77, 39, 68, 8, 29, 80, 51, 54, 10, 17, 70, 14, 38, 51, 21, 5, 64, 70, 33, 84, 90, 62, 43, 84, 6, 92, 94, 67, 33, 56, 17, 99, 55, 22, 7, 83, 33, 87, 78, 88, 26, 18, 13, 39, 95, 21, 18, 63, 16, 13, 54, 9, 18, 20, 92, 41, 17, 44, 69, 24, 52, 84, 42, 75, 84, 88, 96, 98, 66, 89, 56, 24, 63, 62, 9, 25, 51, 93, 83, 37, 43, 60, 72, 10, 70, 25, 21, 40, 25, 37, 69, 22, 7, 51, 64, 88, 82, 20, 18, 99, 10, 67, 76, 43, 2, 41, 76, 63, 85, 61, 58, 94, 11, 30, 34, 5, 61, 92, 46, 82, 35, 97, 72, 60, 59, 11, 76, 12, 73, 22, 48, 32, 68, 77, 34, 58, 74, 11, 66, 11, 39, 60, 52, 13, 42, 5, 42, 29, 53, 84, 12, 23, 35, 52, 7, 9, 6, 65, 69, 32, 76, 20, 85, 51, 36, 60, 69, 28, 95, 62, 24, 99, 32, 64, 94, 6, 71, 87, 38, 37, 29, 59, 91, 18, 51, 1, 90, 97, 9, 90, 99, 88, 98, 36, 58, 62, 53, 71, 52, 43, 31, 63, 22, 11, 73, 54, 72, 50, 80, 22, 60, 25, 20, 87, 48, 15, 46, 84, 85, 1, 12, 91, 0, 84, 97, 12, 21, 60, 8, 98, 57, 9, 58, 37, 35, 39, 60, 53, 10, 21, 68, 68, 93, 5, 37, 95, 36, 1, 17, 95, 40, 41, 0, 84, 24, 34, 80, 11, 39, 27, 84, 46, 0, 50, 87, 50, 24, 71, 35, 76, 86, 90, 27, 27, 13, 56, 73, 62, 84, 79, 80, 90, 81, 19, 42, 55, 68, 27, 29, 80, 81, 0, 63, 74, 23, 46, 22, 25, 3, 80, 89, 44, 66, 1, 1, 82, 22, 12, 36, 16, 23, 22, 69, 6, 85, 63, 95, 55, 73, 23, 43, 8, 96, 73, 11, 45, 8, 1, 78, 85, 60, 38, 1, 29, 48, 12, 88, 93, 41, 37, 53, 50, 22, 9, 4, 6, 66, 46, 88, 63, 85, 36, 39, 18, 43, 90, 7, 6, 53, 23, 49, 39, 3, 87, 22, 79, 62, 24, 50, 81, 49, 70, 5, 42, 3, 66, 97, 50, 15, 12, 78, 47, 79, 42, 69, 27, 17, 41, 22, 63, 59, 46, 55, 84, 25, 98, 22, 35, 91, 39, 63, 37, 46, 35, 25, 34, 85, 23, 91, 72, 94, 89, 69, 13, 83, 97, 89, 40, 8, 26, 84, 3, 53, 8, 10, 88, 74, 66, 74, 53, 60, 98, 59, 34, 52, 89, 44, 76, 57, 36, 42, 32, 49, 57, 59, 26, 58, 84, 15, 47, 80, 90, 37, 42, 96, 25, 14, 15, 68, 43, 1, 30, 50, 77, 14, 70, 80, 84, 43, 94, 39, 4, 40, 3, 19, 21, 80, 7, 9, 92, 63, 3, 60, 49, 76, 62, 38, 37, 92, 88, 69, 90, 25, 89, 57, 88, 79, 29, 33, 89, 27, 49, 97, 97, 19, 38, 35, 89, 60, 54, 48, 48, 18, 87, 74, 53, 94, 48, 54, 40, 82, 52, 30, 88, 61, 58, 85, 91, 63, 66, 63, 81, 36, 50, 37, 63, 23, 40, 23, 35, 97, 62, 2, 17, 91, 17, 6, 28, 16, 12, 47, 73, 76, 72, 76, 24, 44, 55, 65, 84, 42, 74, 28, 34, 24, 60, 93, 60, 54, 78, 3, 5, 16, 95, 25, 83, 61, 8, 74, 37, 85, 93, 31, 70, 86, 38, 39, 47, 8, 79, 19, 46, 66, 21, 76, 40, 65, 37, 82, 73, 89, 83, 67, 69, 19, 78, 81, 81, 80, 38, 66, 37, 94, 16, 1, 0, 43, 43, 77, 28, 29, 51, 98, 11, 89, 39, 26, 80, 93, 14, 69, 76, 2, 74, 78, 77, 44, 31, 50, 16, 27, 37, 46, 14, 48, 96, 40, 0, 69, 30, 28, 36, 90, 13, 34, 67, 53, 13, 78, 68, 90, 67, 40, 15, 42, 87, 78, 64, 53, 8, 51, 50, 43, 35, 22, 3, 81, 28, 56, 68, 17, 95, 21, 41, 14, 52, 4, 7, 76, 82, 15, 45, 15, 98, 53, 72, 74, 32, 83, 64, 85, 92, 36, 33, 30, 69, 67, 28, 9, 78, 94, 6, 57, 0, 31, 18, 27, 20, 92, 77, 28, 87, 61, 90, 54, 58, 61, 58, 7, 66, 87, 21, 30, 76, 87, 94, 19, 88, 81, 43, 38, 32, 50, 78, 78, 39, 70, 20, 71, 71, 65, 4, 82, 50, 74, 61, 73, 62, 91, 56, 50, 9, 55, 24, 53, 33, 57, 23, 18, 93, 82, 51, 16, 43, 54, 37, 52, 99, 90, 54, 64, 13, 8, 80, 13, 8, 12, 57, 84, 3, 20, 56, 74, 92, 53, 48, 63, 28, 23, 32, 14, 84, 65, 9, 91, 19, 14, 86, 36, 44, 50, 58, 35, 87, 24, 14, 17, 17, 61, 3, 38, 52, 45, 57, 7, 53, 75, 42, 62, 0, 7, 43, 65, 98, 26, 11, 21, 51, 27, 88, 6, 69, 26, 50, 68, 75, 14, 73, 61, 78, 41, 40, 50, 84, 33, 59, 21, 15, 18, 69, 10, 4, 13, 19, 20, 81, 66, 21, 45, 47, 68, 3, 14, 71, 73, 60, 34, 45, 17, 86, 6, 99, 8, 49, 86, 76, 46, 64, 95, 82, 77, 14, 53, 78, 4, 13, 55, 49, 89, 6, 61, 2, 15, 27, 25, 55, 19, 88, 81, 5, 89, 69, 3, 82, 50, 24, 16, 94, 61, 53, 30, 13, 31, 75, 6, 36, 93, 44, 21, 77, 10, 9, 87, 57, 40, 61, 53, 76, 12, 1, 17, 65, 80, 36, 56, 14, 82, 49, 0, 16, 20, 81, 34, 94, 17, 66, 64, 95, 42, 95, 57, 64, 81, 22, 66, 66, 61, 56, 73, 27, 61, 4, 71, 62, 98, 9, 60, 51, 95, 22, 85, 17, 11, 38, 23, 91, 15, 70, 68, 66, 76, 11, 34, 42, 58, 40, 98, 76, 90, 14, 38, 35, 6, 50, 32, 48, 88, 67, 87, 74, 95, 52, 79, 74, 31, 74, 77, 73, 76, 74, 21, 17, 16, 95, 67, 45, 32, 95, 99, 72, 26, 53, 13, 66, 94, 55, 46, 98, 43, 1, 7, 27, 57, 65, 76, 7, 7, 36, 12, 26, 63, 9, 58, 52, 43, 89, 54, 70, 93, 13, 5, 19, 20, 64, 44, 18, 71, 65, 21, 44, 7, 24, 80, 76, 86, 41, 91, 99, 9, 55, 41, 57, 82, 30, 5, 73, 75, 22, 44, 99, 14, 99, 7, 28, 0, 81, 27, 32, 50, 71, 35, 67, 43, 27, 71, 23, 82, 31, 99, 55, 98, 69, 45, 77, 15, 75, 76, 16, 86, 43, 24, 14, 68, 95, 25, 74, 14, 22, 87, 60, 25, 92, 68, 59, 22, 61, 81, 2, 22, 49, 22, 80, 89, 21, 99, 88, 86, 69, 60, 68, 93, 11, 98, 60, 92, 29, 67, 41, 2, 31, 75, 47, 58, 19, 13, 6, 37, 98, 87, 3, 13, 22, 24, 27, 24, 78, 78, 75, 46, 65, 45, 10, 26, 60, 70, 77, 14, 48, 74, 90, 30, 38, 37, 79, 49, 86, 12, 42, 37, 66, 53, 66, 10, 80, 60, 59, 45, 15, 87, 85, 56, 59, 65, 80, 32, 55, 11, 92, 12, 33, 47, 91, 15, 43, 89, 75, 69, 87, 39, 2, 54, 85, 37, 6, 79, 22, 96, 5, 50, 53, 78, 48, 80, 31, 61, 27, 6, 47, 20, 49, 57, 42, 56, 40, 45, 71, 95, 47, 62, 26, 74, 61, 81, 67, 90, 20, 62, 24, 12, 79, 0, 27, 81, 0, 91, 71, 33, 27, 69, 93, 25, 52, 42, 4, 81, 12, 85, 58, 87, 51, 53, 4, 85, 80, 15, 6, 23, 93, 20, 61, 43, 91, 74, 68, 10, 20, 41, 60, 89, 85, 97, 57, 92, 90, 82, 73, 9, 83, 82, 22, 64, 98, 29, 37, 13, 74, 45, 49, 96, 97, 68, 92, 28, 15, 97, 31, 55, 35, 48, 37, 27, 68, 80, 14, 90, 79, 41, 85, 11, 92, 81, 80, 87, 8, 83, 33, 60, 30, 30, 79, 8, 89, 34, 75, 56, 98, 10, 89, 22, 18, 14, 74, 1, 25, 32, 55, 21, 33, 72, 9, 35, 24, 38, 4, 22, 20, 81, 92, 81, 70, 71, 28, 39, 39, 40, 25, 17, 44, 15, 18, 1, 97, 33, 12, 98, 73, 78, 86, 68, 86, 42, 10, 94, 60, 24, 78, 71, 85, 76, 64, 64, 3, 69, 53, 55, 86, 7, 88, 66, 69, 75, 80, 62, 70, 13, 65, 28, 70, 12, 49, 68, 11, 34, 67, 97, 1, 45, 1, 10, 96, 59, 92, 87, 45, 15, 65, 74, 86, 99, 41, 28, 32, 17, 44, 45, 67, 73, 4, 17, 24, 5, 5, 34, 47, 92, 3, 11, 81, 49, 7, 70, 72, 55, 21, 66, 26, 71, 81, 60, 24, 67, 80, 16, 38, 47, 79, 69, 2, 80, 34, 32, 5, 73, 77, 19, 27, 26, 9, 30, 90, 21, 2, 9, 42, 31, 80, 8, 47, 55, 32, 69, 80, 93, 17, 88, 31, 45, 99, 21, 72, 54, 30, 76, 85, 10, 71, 87, 41, 77, 23, 68, 74, 28, 35, 12, 71, 86, 86, 17, 88, 91, 34, 53, 19, 80, 46, 95, 99, 57, 0, 67, 20, 41, 25, 75, 86, 25, 33, 48, 19, 24, 73, 9, 44, 80, 18, 27, 31, 23, 27, 5, 8, 11, 75, 55, 27, 1, 49, 10, 58, 9, 31, 41, 49, 35, 37, 54, 89, 26, 90, 83, 96, 9, 24, 49, 89, 63, 7, 0, 24, 80, 72, 40, 27, 7, 48, 42, 63, 96, 47, 72, 53, 49, 50, 66, 68, 79, 73, 29, 0, 15, 72, 27, 50, 24, 89, 63, 83, 68, 43, 66, 54, 2, 74, 60, 91, 78, 86, 81, 34, 0, 19, 38, 9, 54, 56, 45, 76, 70, 2, 15, 55, 23, 24, 91, 8, 31, 91, 16, 46, 90, 30, 31, 60, 39, 31, 7, 53, 14, 86, 77, 11, 31, 78, 8, 48, 15, 60, 41, 86, 15, 81, 91, 11, 6, 22, 93, 15, 29, 23, 71, 99, 7, 11, 8, 5, 52, 52, 3, 86, 12, 55, 36, 89, 38, 11, 54, 44, 89, 73, 97, 60, 86, 36, 16, 94, 64, 80, 82, 83, 86, 55, 51, 76, 73, 78, 7, 24, 36, 34, 72, 43, 14, 59, 86, 58, 87, 31, 41, 82, 12, 5, 87, 93, 52, 27, 97, 95, 87, 57, 70, 0, 20, 75, 64, 39, 3, 72, 82, 70, 23, 62, 13, 9, 97, 9, 53, 8, 68, 10, 79, 80, 93, 63, 33, 73, 6, 12, 79, 24, 26, 34, 15, 32, 94, 21, 67, 26, 76, 30, 9, 83, 12, 73, 99, 14, 83, 38, 70, 31, 73, 3, 78, 68, 14, 55, 72, 43, 42, 50, 92, 57, 6, 47, 67, 77, 45, 77, 49, 96, 51, 78, 44, 63, 91, 71, 82, 62, 80, 43, 17, 4, 22, 99, 52, 69, 28, 75, 9, 33, 3, 1, 57, 96, 79, 34, 87, 51, 34, 0, 27, 3, 42, 64, 11, 15, 50, 89, 22, 12, 92, 32, 15, 21, 79, 40, 75, 34, 95, 53, 38, 54, 57, 59, 50, 65, 77, 26, 54, 26, 7, 7, 54, 64, 73, 63, 78, 61, 21, 33, 41, 15, 23, 5, 19, 18, 79, 80, 63, 43, 53, 90, 28, 29, 6, 61, 19, 86, 1, 71, 90, 21, 94, 97, 97, 11, 87, 0, 24, 71, 42, 28, 68, 78, 6, 35, 29, 80, 2, 0, 89, 34, 77, 58, 94, 73, 19, 71, 94, 29, 74, 40, 54, 1, 77, 11, 96, 91, 57, 48, 12, 4, 69, 81, 57, 67, 11, 69, 47, 49, 21, 45, 77, 76, 91, 50, 93, 49, 17, 24, 21, 93, 28, 84, 49, 24, 18, 11, 56, 14, 41, 66, 63, 96, 21, 36, 54, 74, 30, 92, 29, 99, 62, 40, 2, 1, 18, 37, 46, 34, 75, 14, 40, 54, 85, 99, 73, 63, 73, 2, 98, 73, 12, 53, 48, 17, 81, 6, 74, 82, 14, 92, 81, 91, 71, 93, 17, 4, 77, 40, 49, 3, 54, 81, 13, 79, 5, 66, 87, 50, 41, 10, 37, 82, 81, 78, 26, 99, 66, 37, 25, 97, 8, 83, 43, 11, 52, 43, 21, 40, 92, 5, 13, 83, 60, 10, 65, 85, 6, 43, 20, 82, 41, 20, 17, 51, 48, 77, 46, 37, 78, 94, 38, 94, 88, 45, 38, 26, 37, 76, 91, 12, 56, 18, 18, 12, 77, 16, 78, 70, 67, 91, 99, 4, 31, 32, 37, 0, 13, 57, 51, 3, 29, 32, 65, 19, 53, 64, 3, 5, 80, 90, 62, 32, 72, 86, 89, 66, 72, 15, 33, 84, 97, 16, 86, 8, 13, 61, 86, 53, 59, 16, 61, 42, 7, 5, 20, 72, 68, 94, 43, 9, 34, 63, 45, 33, 95, 74, 40, 25, 40, 0, 69, 96, 24, 36, 35, 21, 50, 63, 87, 10, 39, 31, 56, 6, 71, 75, 43, 93, 57, 83, 80, 21, 37, 42, 55, 25, 49, 8, 60, 28, 83, 34, 22, 35, 55, 24, 75, 80, 0, 93, 59, 75, 23, 46, 3, 95, 93, 45, 45, 50, 77, 40, 18, 55, 5, 16, 75, 16, 86, 72, 45, 48, 64, 91, 1, 27, 83, 27, 38, 96, 66, 16, 34, 59, 56, 60, 81, 36, 40, 1, 71, 10, 1, 65, 32, 52, 5, 84, 5, 78, 34, 71, 7, 58, 27, 53, 73, 97, 20, 62, 42, 80, 66, 31, 26, 86, 32, 88, 10, 48, 66, 10, 52, 79, 59, 63, 79, 60, 98, 78, 76, 99, 57, 80, 40, 22, 51, 30, 28, 66, 3, 95, 68, 55, 68, 68, 85, 77, 59, 20, 19, 81, 67, 12, 39, 46, 73, 95, 30, 9, 55, 99, 50, 55, 51, 93, 64, 71, 38, 73, 28, 34, 78, 89, 89, 73, 11, 52, 49, 36, 0, 54, 33, 47, 11, 58, 27, 39, 8, 99, 78, 48, 59, 81, 53, 75, 76, 55, 3, 8, 30, 51, 44, 11, 54, 71, 57, 62, 80, 52, 39, 42, 44, 81, 28, 44, 20, 3, 57, 85, 63, 89, 19, 28, 73, 43, 99, 46, 75, 1, 43, 49, 84, 64, 2, 48, 4, 46, 90, 74, 42, 94, 0, 57, 20, 84, 14, 35, 82, 41, 58, 63, 6, 48, 49, 69, 17, 82, 87, 80, 0, 34, 35, 40, 65, 73, 75, 76, 13, 50, 68, 52, 59, 83, 78, 61, 19, 63, 19, 76, 86, 75, 39, 35, 73, 67, 20, 3, 54, 62, 34, 87, 96, 52, 63, 57, 27, 42, 84, 64, 45, 60, 84, 72, 53, 27, 69, 15, 33, 31, 84, 63, 57, 5, 66, 23, 49, 32, 12, 14, 20, 47, 35, 24, 0, 58, 38, 97, 94, 30, 60, 26, 68, 8, 10, 25, 94, 79, 69, 64, 6, 6, 27, 55, 22, 82, 11, 45, 96, 10, 97, 99, 76, 29, 31, 1, 32, 93, 68, 69, 58, 17, 27, 34, 81, 35, 11, 30, 57, 6, 5, 19, 72, 88, 51, 60, 60, 13, 42, 51, 79, 36, 27, 61, 34, 11, 32, 74, 12, 69, 23, 50, 26, 50, 27, 78, 32]
# print(len(predictions))
# print(type(dataset.class_to_idx))
# print()

# reversed_dict = {}
# for key, value in dataset.class_to_idx.items():
#     reversed_dict[value] = key
# print(reversed_dict)
# with open('predictions.csv', 'w', newline='') as csvfile:
#     fieldnames = ['Id', 'Category']
#     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#     writer.writeheader()
#     for idx in range(len(test_dataset)):
#         # image, image_name = test_dataset[idx]  # Retrieve image and image name
#         predicted_label = predictions[idx]
#         print(predicted_label, reversed_dict[predicted_label])
#         writer.writerow({'Id': idx, 'Category': reversed_dict[predicted_label]})



# torch.save(resnet, "saved_model_big.pth")