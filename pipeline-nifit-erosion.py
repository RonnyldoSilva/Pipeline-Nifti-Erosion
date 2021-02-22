import os, shutil, cv2
import numpy as np
from distutils.dir_util import copy_tree
from tqdm import tqdm

path = os.getcwd()
dataset_path = os.path.join(path, "Dataset_lesion")
result_path = os.path.join(path, "Results_lesion")
gt_path = os.path.join(path, 'gt')
img_path = os.path.join(path, 'img')

px_1mm = 4
px_3mm = 11
px_4mm = 15

def delete_files(folder):
	for filename in tqdm(os.listdir(folder)):
		file_path = os.path.join(folder, filename)
		try:
        		if os.path.isfile(file_path) or os.path.islink(file_path):
        			os.unlink(file_path)
        		elif os.path.isdir(file_path):
        			shutil.rmtree(file_path)
		except Exception as e:
        		print('Failed to delete %s. Reason: %s' % (file_path, e))


def dilate(gt_path, px):
	kernel = np.ones((px, px),np.uint8)
	for image in tqdm(os.listdir(gt_path)):
		name = os.path.join(gt_path, image)
		img = cv2.imread(name, cv2.IMREAD_GRAYSCALE)
		dilation = cv2.dilate(img, kernel)
		cv2.imwrite(name, dilation)

def erode(gt_path, px):
	kernel = np.ones((px, px),np.uint8)
	for image in os.listdir(gt_path):
		name = os.path.join(gt_path, image)
		img = cv2.imread(name, cv2.IMREAD_GRAYSCALE)
		erosion = cv2.erode(img,kernel,iterations = 1)
		cv2.imwrite(name, erosion)
		
def write_gt_and_flip(source_gt, destiny_gt):
	print("Deleting previous ground truths")
	delete_files(destiny_gt)
	
	print("Copying new ground truths")
	copy_tree(source_gt, destiny_gt)
	
	print("fliping images")
	os.system("python3 flip.py")
	
def write_dcm(source_dcm, destiny_dcm):
	print("Deleting previous DICOMs")
	delete_files(destiny_dcm)
	
	print("Copying new DICOMs")
	copy_tree(source_dcm, destiny_dcm)
	
def convert_to_rt(rt_path, patient):
	os.system("python3 conversion2.py ./img ./gt '{}' '{}'".format(rt_path, patient))

def write_nii(rt_path, rt_file, destiny_dcm, nii_path):
	nii_path = os.path.join(rt_path, nii_path)
	os.system("dcmrtstruct2nii convert --rtstruct '{}' --dicom '{}' --output '{}' --convert-original-dicom False".format(rt_file, destiny_dcm, nii_path))

if __name__=="__main__":
	try:
		os.makedirs(result_path)
	except:
		print("result path done")
#	MODIFY HOSPITAL IF NECESSARY
	for hospital in os.listdir(dataset_path):
		hospital_path = os.path.join(dataset_path, hospital)
		output_hospital = os.path.join(result_path)

		try:
			os.makedirs(output_hospital)
		except:
			print("result path done")

		pct_hospital = os.path.join(hospital_path, 'PCT')
		gt_hospital = os.path.join(hospital_path, 'masks')

		for i, patient in enumerate(sorted(os.listdir(gt_hospital))):
			dcm_path_pct = os.path.join(pct_hospital, sorted(os.listdir(pct_hospital))[i])
			print(dcm_path_pct)
			patient_lesions = os.path.join(gt_hospital, patient)
			write_dcm(dcm_path_pct, img_path)

			for j, lesion in enumerate(os.listdir(patient_lesions)):
				lesion_path = os.path.join(patient_lesions, lesion)
				print(lesion_path)
				rt_path = os.path.join(result_path, hospital, patient, lesion)
				
				try:
					os.makedirs(rt_path)
				except:
					print("result patient folder done")
				#FAZER COM QUE CADA LESÃO TENHA UMA PASTA COM OS TRES NIFTIS
				rt_file = rt_path+'/{}'.format(patient)

				print("ORIGINAL NII")
				write_gt_and_flip(lesion_path, gt_path)
				convert_to_rt(rt_path, patient)
				write_nii(rt_path, rt_file, img_path, 'original')
				
				print("ERODED 3MM")
				erode(gt_path, px_3mm)
				convert_to_rt(rt_path, patient)
				write_nii(rt_path, rt_file, img_path, 'eroded_3mm')
				
				print("ERODED 4MM")
				erode(gt_path, px_1mm)
				convert_to_rt(rt_path, patient)
				write_nii(rt_path, rt_file, img_path, 'eroded_4mm')

			
