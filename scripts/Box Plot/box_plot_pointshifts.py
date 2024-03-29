"""Echonet Function Evaluation comparisons of different methods' 
percent change in task to compare the volume vs. ground truth"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import config
import loader
from algorithms import funcs as funcs
from algorithms import volume_tracings_calculations as tracings
from ast import literal_eval
from tqdm import tqdm

# Return dictionary of volume data calculated from coordinates given in VolumeTracings
def sortFrameVolumesFromTracings(method):
  _, df = loader.dataModules()
  calculatedVolumeFromGroundTruth={}
  
  print("\nCalculating volumes from VolumeTracings coordinates")
  for i in tqdm(range(len(df))):
    videoName = df.iloc[i, 0] + ".avi"
    
    x1 = list(literal_eval(df.iloc[i, 2])) # x1 coords
    y1 = list(literal_eval(df.iloc[i, 3])) # y1 coords
    x2 = list(literal_eval(df.iloc[i, 4])) # x2 coords
    y2 = list(literal_eval(df.iloc[i, 5])) # y2 coords
    
    number = len(x1) - 1

    maxX1, maxY1, maxX2, maxY2, lowerInterceptAveragePoints, higherInterceptAveragePoints = tracings.calcParallelAndMaxPoints(x1, y1, x2, y2)

    if number < 22:
      if method == "Method of Disks":
        ground_truth_volume = funcs.volumeMethodOfDisks(maxX1, maxY1, maxX2, maxY2, number, lowerInterceptAveragePoints, higherInterceptAveragePoints)
      elif method == "Prolate Ellipsoid":
        ground_truth_volume = funcs.volumeProlateEllipsoidMethod(maxX1, maxY1, maxX2, maxY2, lowerInterceptAveragePoints, higherInterceptAveragePoints)
      elif method == "Bullet Method":
        ground_truth_volume = funcs.volumeBulletMethod(maxX1, maxY1, maxX2, maxY2, lowerInterceptAveragePoints, higherInterceptAveragePoints)

      if videoName not in calculatedVolumeFromGroundTruth:
        calculatedVolumeFromGroundTruth[videoName] = []
      
      calculatedVolumeFromGroundTruth[videoName].append(ground_truth_volume)
  return calculatedVolumeFromGroundTruth

# Returns dictionary with calculated volumes (received from CSV)
def getCalculationsFromCSV(shifts):
  root, _ = loader.dataModules() # get path data
  calculatedVolumes = {}

  df = pd.read_csv(os.path.join(root, "Main Axis Top Shift.csv")) # reading in CSV
  df = df.astype(str).groupby(['Video Name']).agg(','.join).reset_index() # group based on file name

  for i in tqdm(range(len(df))): # iterates through each row of data frame
    videoName = df.iloc[i, 0] # name of video
    
    for x in range(shifts):
      shift = list(literal_eval((df.iloc[i, 2])))[x] # degree change

      calculatedESV = float(list(literal_eval((df.iloc[i, 4])))[x]) # ESV calculation
      calculatedEDV = float(list(literal_eval((df.iloc[i, 5])))[x]) # EDV calculation

      if videoName not in calculatedVolumes:
        calculatedVolumes[videoName] = {}
      if shift not in calculatedVolumes[videoName]:
        calculatedVolumes[videoName][shift] = [calculatedESV, calculatedEDV]
  
  return calculatedVolumes

# Return dictionary of volume data from FileList
def sortVolumesFromFileList(root=config.CONFIG.DATA_DIR):
  givenTrueDict={}

  df = pd.read_csv(os.path.join(root, "FileList.csv"), ) # reading in FileList.csv

  print("\nGathering volumes from FileList")
  for i in tqdm(range(len(df))):
    videoName = df.iloc[i, 0]
    ground_truth_ESV = df.iloc[i, 2]
    ground_truth_EDV = df.iloc[i, 3]

    if videoName not in givenTrueDict:
      givenTrueDict[videoName] = []
    
    givenTrueDict[videoName] = [ground_truth_ESV, ground_truth_EDV]

  return givenTrueDict

# Compare volumes using calculated main axis point shifts against FileList or VolumeTracings
def compareVolumePlot(inputFolder, method, volumeType, fromFile, shifts, root=config.CONFIG.DATA_DIR):
  
  all_volumes = getCalculationsFromCSV(shifts)

  if fromFile is "VolumeTracings":
    true_volumes = sortFrameVolumesFromTracings(method)
  else:
    true_volumes = sortVolumesFromFileList()

  changesInVolumesDict = {}
  for videoName in true_volumes:
    volumeData = true_volumes[videoName]

    ground_truth_ESV = min(volumeData) # true ESV value
    ground_truth_EDV = max(volumeData) # true EDV value
    ground_truth_EF = (1 - (ground_truth_ESV/ground_truth_EDV)) * 100 # true EF value (calculated)

    if videoName in all_volumes:
      print(all_volumes[videoName])
      EDV = all_volumes[videoName][0][1] # calculated EDV for 0th point shift
      zero_ESV = all_volumes[videoName][0][0] # calculated ESV for given point shift
      zero_EF = (1 - (zero_ESV/EDV)) * 100 # calculated EF for given point shift

      for shift in all_volumes[videoName].keys():
        if shift not in changesInVolumesDict:
          changesInVolumesDict[shift] = []
      
        volumes = all_volumes[videoName][shift] # volumes of given point shift

        ESV = min(volumes) # calculated ESV for given point shift
        EF = (1 - (ESV/EDV)) * 100 # calculated EF for given point shift

        diff_EF = ((EF - zero_EF)/zero_EF) * 100 # difference in calculated EF and true EF
        diff_EDV = ((EDV-ground_truth_EDV)/ground_truth_EDV) * 100 # difference in calculated EDV and true EDV
        diff_ESV = ((ESV-ground_truth_ESV)/ground_truth_ESV) * 100 # difference in calculated ESV and true ESV
      
        if volumeType is "EF" and 20 > shift > -20:
          changesInVolumesDict[shift].append(diff_EF)
        elif volumeType is "ESV":
          changesInVolumesDict[shift].append(diff_ESV)
        elif volumeType is "EDV":
          changesInVolumesDict[shift].append(diff_EDV)

  return changesInVolumesDict

# Create box plot by calling functions and graphing data
def createBoxPlot(inputFolder="Masks_From_VolumeTracing", method="Method of Disks", volumeType="EF",
                  fromFile="FileList", shifts=5):
  differenceInVolumes = compareVolumePlot(inputFolder, method, volumeType, fromFile, shifts)
  labels = []

  differenceInVolumes = {k: v for k, v in differenceInVolumes.items() if len(v) >= 40} # rmemoving shifts with low values

  differenceInVolumes = {key:value for key, value in sorted(differenceInVolumes.items(), key=lambda item: int(item[0]))} # sorting numerically

  for i in differenceInVolumes.keys():
    labels.append(i)

  # figure related code
  loader.latexify()
  fig = plt.figure()
  #fig.suptitle('Comparison', fontsize=14, fontweight='bold')
  
  _, data = differenceInVolumes.keys(), differenceInVolumes.values()

  ax = fig.add_subplot(111)
  ax.boxplot(data, showfliers=False)

  #ax.set_title('Difference in Calculated ' + volumeType + ' against ' + fromFile + ' using Erosion and Dilation')
  ax.set_xlabel('% Decrease in LV Longitudinal Axis Due to MV Annulus Level Error')

  if volumeType is "ESV" or volumeType is "EDV":
    ax.set_ylabel('% Change in ' + volumeType)
  else:
    ax.set_ylabel('% Change in Ejection Fraction')

  ax.set_xticklabels(labels)
  
  # show plot
  plt.show()

createBoxPlot(method="Method of Disks", volumeType="EF", inputFolder="frames", fromFile="VolumeTracings",
              shifts=9)
#createBoxPlot(method="Method of Disks", volumeType="EF", inputFolder="frames", fromFile="VolumeTracings")
#createBoxPlot(method="Method of Disks", volumeType="ESV", inputFolder="frames", fromFile="VolumeTracings")
#createBoxPlot(method="Method of Disks", volumeType="EDV", inputFolder="frames", fromFile="VolumeTracings")
