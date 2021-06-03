"""Create CSV for timing data (true frame and predicted frames)"""

import pandas as pd
import os
import config
import loader
from algorithms import funcs as funcs
import collections
import cv2
from ast import literal_eval
from tqdm import tqdm
import find_peaks
import csv

# Returns dictionary with predicted frames
def gatherTimingPredictions(inputFolder="Control-Videos-Segmented", outputFolder="control_video_frames",
                            CSVName="Frame Timing Predictions.csv", createFrames=False):
  """Function to predict end-systolic and end-diastolic timings for each video
  Args:
      inputFolder (str): Folder containing the segmented videos
      outputFolder (str): Output directory to save all frames of each video.
      CSVName (str): Name of the CSV file to export
      createFrames (bool): Determines whether to create frames for each video or not
  Returns:
      None
  """

  root=config.CONFIG.DATA_DIR
  videoPath = os.path.join(root, inputFolder)

  dataList = []
  
  logFileName = os.path.join(root, CSVName)
  
  for videoName in tqdm(os.listdir(videoPath)):
    if "avi" in videoName:
      ES_frame, ED_frame = find_peaks.returnPeaks(videoName=os.path.splitext(videoName)[0],
                                        inputFolderName=inputFolder, outputFolderName=outputFolder, makeFrames=createFrames)
        
      #ES_frame, ED_frame = prediction_frames[0], prediction_frames[1] # predicted timings
      #true_ES_frame, true_ED_frame = true_frames[0], true_frames[1] # true timings

      videoData = {"Video Name": videoName, "Predicted ESV": ES_frame, "Predicted EDV": ED_frame}
                  #"True ESV": true_ES_frame, "True EDV": true_ED_frame}

      dataList.append(videoData)
  
  df = pd.DataFrame(dataList) # convert to dataframe
  df.to_csv(logFileName) # export to CSV


gatherTimingPredictions(inputFolder="Segmentation", outputFolder="Netherlands", createFrames=True)