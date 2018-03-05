#!/usr/bin/python
################################################################################
#
# Author:  Mondejar-Guerra V.
#
# Create at 5 Feb 2018
# Last modification: 5 Feb 2018
################################################################################

import numpy as np
import cv2
from os import listdir
from os.path import isfile, join
import os
import random
import sys
from draw_corners_on_marker import *

""" 
This code prepares the data for train the model.
Given two directories, the first one with the markers and the second one with the background images.
This code creates a file with:
	- N transformations for each marker M over N different images 
	- The 4 coordinates that enclose each marker M on the image	    		

python marker_dataset_path img_dataset_path number_transforms patch_size
				
Example call:

"""


# Generate a random affine transform over the four corners
def affine_transform(img, mask_img, patchSize, marker_corners, randomDispFactor ):
	 
	# To warp the full image (including white borders)
	corners = np.float32([[0, 0], [0, patchSize], [patchSize, 0], [patchSize, patchSize]])
	cornersT = np.float32([[0, 0], [0, 0], [0, 0], [0, 0]])

	w = int(round(randomDispFactor * patchSize))
	h = int(round(randomDispFactor * patchSize))

	for p in range(0,4):
		randValue = random.uniform(0.0, 1.0)
		x =  int(round(((w * randValue)))  + corners[p][0])
		randValue = random.uniform(0.0, 1.0)
		y = int(round(((h * randValue))) + corners[p][1])
		cornersT[p] = np.float32([x, y])

	# Norm to make the patch be centered
	cornersT[:,0] = cornersT[:,0] - np.min(cornersT, 0)[0]
	cornersT[:,1] = cornersT[:,1] - np.min(cornersT, 0)[1]

	maxW = np.max(cornersT, 0)[0] - np.min(cornersT, 0)[0]
	maxH = np.max(cornersT, 0)[1] - np.min(cornersT, 0)[1]

	persT = cv2.getPerspectiveTransform(corners, cornersT)
	warp_img = cv2.warpPerspective(img, persT, (maxH, maxW), flags=cv2.INTER_LINEAR)#, borderMode=cv2.BORDER_CONSTANT)

	# Set mask for only select the marker affine
	warp_mask_img = cv2.warpPerspective(mask_img, persT, (maxH, maxW), flags=cv2.INTER_LINEAR)#, borderMode=cv2.BORDER_CONSTANT)

	marker_corners = np.array([marker_corners])
	marker_corners_T = cv2.perspectiveTransform(marker_corners, persT)

	return warp_img, warp_mask_img, marker_corners_T

def dynamic_range_compression(img):
	
	randValue = random.uniform(0.0, 1.0)
	a = (0.6 * randValue) + 0.4 #[0.4, 1]
	
	randValue = random.uniform(0.0, 1.0)
	b = 25.0 * randValue#[0,100]	

	rows, cols = img.shape
	for r in range(rows):
		for c in range(cols):
			val = img[r,c]
			img[r,c] = int( np.min([255, a * val + b]))

	return img


def blurring(img):
	x_value = random.uniform(1.0, 9.0)
	y_value = random.uniform(1.0, 9.0)

	img = cv2.blur(img, (int(x_value), int(y_value)), 0)

	return img

# Put the marker in the background image
# This function is needed for the affine transform
# Mask contains the pixels of the marker with 255
#
#   Marker corners:
#
#     0----1
#     |    |
#     2----3
#


def create_dataset(marker_dataset, img_dataset, numWarps, patchSize, outImPath, valFilename, trainFilename, verbose):

	if not os.path.exists(outImPath):
		os.mkdir(outImPath)

	if not os.path.exists(outImPath + 'train_data'):
		os.mkdir(outImPath + 'train_data')

	if not os.path.exists(outImPath + 'val_data'):
		os.mkdir(outImPath + 'val_data')


	# create file
	fileList_Train = open(trainFilename,'w') 
	fileList_Val = open(valFilename,'w') 

	imMarkers = [f for f in listdir(marker_dataset) if isfile(join(marker_dataset, f))]
	imBackgrounds = [f for f in listdir(img_dataset) if isfile(join(img_dataset, f))]
	
	numIm = 0

	train_val_factor = 0.1 # 10% of the warps are exported on the validation folder

	for imMarker in imMarkers:
		# Read marker
		print(marker_dataset + imMarker)
		marker_orig = cv2.imread(marker_dataset + imMarker, 0)

		for w in range(0, numWarps):

			# Pick a random background image
			imBackground = random.choice(imBackgrounds)
			back_img = cv2.imread(img_dataset + imBackground, 0)

			if not back_img is None:
							
				# Resample the background image to the double of patch size
				train_img = cv2.resize(back_img, ( 2 * patchSize, 2 * patchSize)) 	

				# TODO: 
				# Scale the marker at some size between 10-50% of the specified size
				scale_factor = random.uniform(0.3, 0.7)#0.1, 0.5
				marker_size = int(patchSize * scale_factor)
				marker_scale = cv2.resize(marker_orig, (marker_size, marker_size))

				# 1 Put the marker in the image and add a white border
				x_pos = np.random.randint(patchSize/2, (patchSize + patchSize/2) - marker_size - 1)
				y_pos = np.random.randint(patchSize/2, (patchSize + patchSize/2) - marker_size - 1)		

				mask_img = np.zeros((2*patchSize, 2*patchSize))
				whit_pix = int(marker_size * 0.1)

				mask_img[x_pos:x_pos+marker_size, y_pos:y_pos+marker_size] = np.ones((marker_size, marker_size)) * 255
				train_img[x_pos-whit_pix:x_pos+marker_size+whit_pix, y_pos-whit_pix:y_pos+marker_size+whit_pix] = np.ones((marker_size + 2*whit_pix, marker_size + 2*whit_pix)) * 255
				train_img[x_pos:x_pos+marker_size, y_pos:y_pos+marker_size] = marker_scale


				marker_corners = np.array([[y_pos, x_pos], [y_pos+marker_size, x_pos], [y_pos, x_pos+marker_size], [y_pos+marker_size, x_pos+marker_size]], dtype='float32')


				# Apply affine transform and crop!
				train_img, mask_img, marker_corners = affine_transform(train_img, mask_img, patch_size*2, marker_corners, 0.3)

				# Crop the generated regions
				train_img = train_img[patch_size/5:(2*patch_size) -patch_size/5, patch_size/5:(2*patch_size) -patch_size/5]
				mask_img = mask_img[patch_size/5:(2*patch_size) - patch_size/5, patch_size/5:(2*patch_size) -patch_size/5]			
				marker_corners= marker_corners-int(patch_size/5)


				# Add extra transforms:
				# Blurring
				# Not apply always the bluring!
				apply_blur = random.uniform(0.0, 1.0)
				if apply_blur > 0.5:
					train_img = blurring(train_img)
					

				# Light ? 

				cv2.namedWindow('train_img', cv2.WINDOW_NORMAL)
				cv2.imshow('train_img',train_img)

				cv2.namedWindow('mask_img', cv2.WINDOW_NORMAL)
				cv2.imshow('mask_img', mask_img)
				
				cv2.namedWindow('mask_img_C', cv2.WINDOW_NORMAL)
				cv2.imshow('mask_img_C', draw_corners_on_marker(train_img, marker_corners.flatten()))
				cv2.waitKey(0)


				# then apply the scale, dynamic, blurring, ilumination and affine transform!
				



				"""




				# gray level?
				marker_scale = dynamic_range_compression(marker_scale)

				# blurring: to the marker or to the global image?

				# Ilumination? non uniform?

				# affine transform
				white_border = 10 # pixels
				marker_affin, persT, mask_perspect, image_corners, gt_corners = affine_transform(marker_size, white_border, marker_scale, 0.3)

				rows_marker, cols_marker = marker_affin.shape
			    # and place randomly over the background image
				x_pos = np.random.randint(0, patchSize - cols_marker - 1)
				y_pos = np.random.randint(0, patchSize - rows_marker - 1)				

				train_img, mask_train_img = merge_images(train_img, x_pos, y_pos, marker_affin, mask_perspect, patchSize)


				# Export the image and write the four corners on the file
				gt_corners[:,0] = gt_corners[:,0] + x_pos
				gt_corners[:,1] = gt_corners[:,1] + y_pos

				# Last  numWarps - (train_val_factor * numWarps) for validation
				if w > (numWarps - (train_val_factor * numWarps)):
					nameTrainImg = outImPath + 'val_data/' + imMarker[:-5] + "_" + str(w) + '.png'
					nameMaskImg = outImPath + 'val_data/' + imMarker[:-5] + "_" + str(w) + '_mask.png'

					# add line to file
					fileList_Val.write( nameTrainImg + ' ' + nameMaskImg)

					for p in range(0, 4):	
						fileList_Val.write(' ' + str(gt_corners[p][0]) + ' ' + str(gt_corners[p][1]))
					fileList_Val.write('\n')

				else:
					nameTrainImg = outImPath + 'train_data/' + imMarker[:-5] + "_" + str(w) + '.png'
					nameMaskImg = outImPath + 'train_data/' + imMarker[:-5] + "_" + str(w) + '_mask.png'

					# add line to file
					fileList_Train.write( nameTrainImg + ' ' + nameMaskImg)

					for p in range(0, 4):	
						fileList_Train.write(' ' + str(gt_corners[p][0]) + ' ' + str(gt_corners[p][1]))
					fileList_Train.write('\n')	

				# Export patch warp
				cv2.imwrite( nameTrainImg, train_img)

				cv2.imwrite( nameMaskImg, mask_train_img)	

				# Export segmented mask!

				# Write .bin files for use with caffe 
				if verbose:
					cv2.namedWindow('train_img', cv2.WINDOW_NORMAL)
					cv2.imshow('train_img', train_img)

					cv2.namedWindow('mask_train_img', cv2.WINDOW_NORMAL)
					cv2.imshow('mask_train_img', mask_train_img)

					cv2.namedWindow('train_img_corners', cv2.WINDOW_NORMAL)
					cv2.imshow('train_img_corners', draw_corners_on_marker(train_img, gt_corners.flatten()))

					cv2.waitKey(0)
					cv2.destroyAllWindows()


				if w % 1000 == 0:
					print(str(w) + '/' + str(numWarps))
				"""
			else:
				print("Warning: It could not be load background image: " + imBackground)
				w = w-1


	
	fileList_Train.close()
	fileList_Val.close()













if __name__ == "__main__":

	# NOTE
	# check this path dirs!
	patch_size = 128

	# Dir in which the new patches are saved 
	outImPath = 'data/' + str(patch_size) +'/' 

	# Full file path referencing the patches and ground truth
	valFilename = 'data/' + str(patch_size) +'/val_data_list.txt' 
	trainFilename = 'data/' + str(patch_size) +'/train_data_list.txt' 

	verbose = False	# set True to display the process

	create_dataset('/home/mondejar/dataset/markers/', '/home/mondejar/dataset/mirflickr/', 50000, patch_size, outImPath, valFilename, trainFilename, verbose)
    