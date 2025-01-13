#!/usr/bin/env python
# coding: utf-8

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

import PIL
from PIL import Image

import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut


def apply_lut(dcm, index=0):
    display_data = apply_voi_lut(dcm.pixel_array, dcm, index=index)
    return display_data


def get_filepaths(dicom_path, root_folder):
    file = dicom_path.split("/")[-1]
    folder = f"{root_folder}{'/'.join(dicom_path.split('/')[9:-1])}"
    return folder, file


def get_year(dicom_path):
    return dicom_path.split("/")[9]


def get_dicom(dicom_path):
    dicom = pydicom.dcmread(dicom_path)
    year = get_year(dicom_path)
    pid = dicom.PatientID
    acc = dicom.AccessionNumber
    filename = dicom.SOPInstanceUID
    return f"{pid}/{year}/{acc}", f"{filename}.png", dicom


def save_png(pixel_array, filename):
    im = Image.fromarray(pixel_array)
    im.save(filename)


def check_uint16(pixel_array):
    if hasattr(pixel_array, 'dtype'):
        if pixel_array.dtype!='uint16':
            return 0
        else:
            return 1
    else:
        print("No dtype")


def extract_png(dicom_path, output_png_folder, output_csv_folder):
    out_folder, out_file, dcm = get_dicom(dicom_path)
    png_path_folder = f"{output_png_folder}{out_folder}"
    final_png_path = f"{png_path_folder}/{out_file}"   

    img = apply_lut(dcm)

    # if check_uint16(img):
    if not os.path.exists(png_path_folder):
        os.makedirs(png_path_folder)         
    img = img.astype(np.float32)
    img16 = (65535*((img - img.min())/img.ptp())).astype(np.uint16)

    im16 = Image.fromarray(img16)
    im16.save(final_png_path)

    pd.DataFrame({"AccessionNumber_anon": [dcm.AccessionNumber], "anon_dicom_path": [dicom_path], "png_path_anon": [final_png_path], "ViewPosition": [dcm.ViewPosition]}).to_csv(f"{output_csv_folder}{out_file[:-4]}.csv", index=False)


if __name__=="__main__":
    
    import argparse

    parser = argparse.ArgumentParser(description='Extract 16-bit PNG from DICOM')
    parser.add_argument('year', metavar='Y', type=int,
                        help='Year of the Cohort')
    
    args = parser.parse_args()
    
    df = pd.read_csv(f"~/CXR/meta_anon/meta_{args.year}_anon.csv", dtype=str)
    output_png_folder = "~/CXR/REEXTRACT/PNG/"
    output_csv_folder = "~/CXR/REEXTRACT/CSV/"
    original = df.loc[(df.ImageType.str.contains("Original", case=False)) & (df.ImageType.str.contains("primary", case=False))]
    for i in tqdm(range(len(original))):
        try:
            dicom_path = original.dicom_paths.iloc[i]
            extract_png(dicom_path, output_png_folder, output_csv_folder)
            
        except Exception as e:
            print(e)

