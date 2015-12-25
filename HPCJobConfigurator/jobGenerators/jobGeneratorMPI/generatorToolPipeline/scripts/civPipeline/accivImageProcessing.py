# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os,re
import numpy as np
import h5py

from attrdict import AttrMap

import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import matplotlib.colors as colors


import scipy as scp

import skimage.exposure as exposure
from skimage.io import imread
from skimage.filters import *
from skimage.morphology import *
from skimage import data
from skimage import img_as_float, img_as_bool
from skimage.morphology import disk
from skimage import measure


class AccivImageConverter:
    
    def __init__(self, processFile, jobGenModules=None):
        
        self.processFile = AttrMap(processFile)
        
        self.pS = self.processFile.processSettings
        
        self.cS = self.pS.converterSettings
        self.fr = self.processFile.frames
        
        self.cf = jobGenModules["commonFunctions"]
    
    def loadImage(self,f):
      # average over all colors (as_gray = True, does something else, linear transform)
      return np.average(img_as_float(imread(f)),2)
      
        
    def doProcessing(self):
    
        print("========== AccivImageProcessing: Process Frames =========")
        
        # load experiment settings
        
        self.allExpSet = AttrMap(self.cf.jsonLoad(self.cS.experimentSettingsFile))
        ex = "%i" % self.cS.experimentNumber
        if ex not in self.allExpSet["experiments"]:
            raise ValueError("Experiment number %i not found in %s" % (self.cS.experimentNumber, self.cS.experimentSettingsFile))
        
        # make experiment settings
        self.expSet = AttrMap(self.allExpSet["experiments"][ex])
        
        print("Experiment Settings: ", self.expSet)
        
        # load intensity shift values if we have a numpy .npz file
        try:
          l=self.cf.jsonLoad(self.cS.intensityShift)
          self.intensityShift = dict(l)
          print("Loaded  %i intensity shift values" % len(self.intensityShift) )
        except:
          self.intensityShift = None
          print("No intensity shift values found! -> using none")
          
        # load background image
        # and try to shift intensity
        self.cS.background = self.loadImage( self.cS.backgroundFile )
        
        if self.intensityShift is not None and self.intensityShift:
          try:
            frameIdx = int(re.match(self.cS.frameExtractRegex, self.cS.backgroundFile).group(1))
            shiftI = self.intensityShift[frameIdx]
            print("Shift background intensity by -%f" % shiftI)
            self.cS.background -= shiftI;
          except:
            print("Did not shift background intensity")
        
        
        # load additional mask
        if "additionalMask" in self.cS and os.path.exists(self.cS.additionalMask):
            self.cS.additionalMask = img_as_bool(imread(self.cS.additionalMask))
        else:
            self.cS.additionalMask = None
        
        # set height/width
        self.cS.height  = self.cS.background.shape[0];
        self.cS.width   = self.cS.background.shape[1];
        self.cS.mask    = np.ones(self.cS.background.shape,np.uint8)
        
        # bounds (with x-Axis to the right, y-Axis up, like ACCIV)
        if "offsetZero" not in self.expSet:
            self.expSet.offsetZero = [0,0]
        
        min=self.expSet.aabbMeterCoordinates["minPoint"]
        max=self.expSet.aabbMeterCoordinates["maxPoint"]
        
        self.cS.bounds = np.array([ min[0], max[0], min[1],max[1] ] )
        
        
        # process all frames
        for frame in self.fr:
            self._processFrame(frame)
            
                    
        print("============== AccivImageProcessing: finished ===========")
    
    def _processFrame(self,frame):
        
        frameIdx = frame.frameIdx
        print("Process frame: %i" % frameIdx)
        
        inputFiles = frame.inputFiles
        inputFileIndices = np.array(frame.inputFileIndices)
        outputFiles = frame.outputFiles
        print("Input file indices: ", inputFileIndices)
        
        if len(inputFiles) != len(outputFiles) and len(inputFiles) != len(inputFileIndices) :
            raise ValueError("inputFiles not the same size as outputFiles/inputFileTimes for frameIdx : %i" % frameIdx)
        
        
        background = self.cS.background
        
        # an additional mask which is multiplied with the last modifcated image to get the final image
        additionalMask   = self.cS.additionalMask
        
        height = self.cS.height 
        width  = self.cS.width 
        bounds = self.cS.bounds
        
        inputFileTimes = inputFileIndices * self.allExpSet.deltaT;

        for inputFile,outputFile,time in zip(inputFiles,outputFiles,inputFileTimes) :
            
            if os.path.exists(outputFile):
                print("Skip existing inputFile: %s because output exists already!" % inputFile)
                continue
            
            print("Process image: %s" % inputFile)
            baseName,ext = os.path.splitext(outputFile)

            image =  self.loadImage(inputFile)
                        
            print("Image type:" , image.dtype)
            print("Index (0,0) (top-left):", image[0,0])
            print("Index (1,0):", image[1,0])
            
            
            # try to shift intensity
            if self.intensityShift is not None and self.intensityShift:
                try:
                  frameIdx = int(re.match(self.cS.frameExtractRegex, inputFile).group(1))
                except:
                  raise ValueError("Could not extract frameIdx from image %s with regex: %s " % (inputFile,self.cS.frameExtractRegex))
                shiftI = self.intensityShift[frameIdx]
                print("Shift intensity by -%f" % shiftI)
                image -= shiftI;
                
            
            if( image.shape != self.cS.background.shape ):
                raise ValueError("Background has other shape %s then the frame %s with shape %s!" % (str(self.cS.background.shape), inputFile,str(image.shape))) 

            # testing image processing stuff =================================================
            
            #p2, p98 = np.percentile(image, (2, 98))
            #image = exposure.rescale_intensity(image, in_range=(p2, p98))
            #image_clahe = exposure.equalize_adapthist(image,ntiles_x=16,ntiles_y=16);

            # background subtract 
            
            subtracted = np.abs(image - background)
            print("background image->subtracted:", subtracted.dtype)
            
            th = threshold_otsu(subtracted)
            # threshol with otsu
            binary = (subtracted > th).astype(np.uint8)
            print("threshold subtracted->binary:", binary.dtype)
            
            # do some opening (not used so far in the output)
            d = disk(5)
            binary2 = binary_opening(binary, d)
            print("morph. opening binary->binary2:", binary2.dtype)
            
            # do some thresholding value*otsu (boolean image)
            binary3 = subtracted > self.cS.otsuThMult*th
            print("threshold subtracted->binary3:", binary3.dtype)
            
            # remove small objects (boolean image)
            denoise = remove_small_objects(binary3,min_size=500) # inplace = True
            print("denoise binary3->denoise: ", denoise.dtype)
            
            # thicken up white area abit
            dilated = binary_dilation(denoise, disk(3))
            print("dilate denoise->dilated:", dilated.dtype)
            
            # blur the image (for contours)
            blurred = gaussian_filter(dilated,sigma=4) # inplace = True
            print("blur dilated->blurred:", blurred.dtype)
            
            # find max. length contour (interpolate)
            contours = measure.find_contours(blurred, 0.5)
            if contours :
                contourMax = np.array(max(contours,key=lambda x: x.shape[0]))
                tck,u = scp.interpolate.splprep([contourMax[:, 0], contourMax[:, 1]], s=3e4)
                unew = np.linspace(0, 1.0, 3000)
                contourInterp = scp.interpolate.splev(unew, tck)
            else:
                contourMax = None
                contourInterp = None
            
            # final mask should be uint8 (and 0 or 1)
            if additionalMask is not None:
                final_mask = additionalMask * denoise
            else:
                final_mask = denoise
            final_mask = final_mask.astype(np.uint8)
            # =================================================================================
            
            
            # Save some images ================================================================
            #skimage.io.imsave(baseName +"-clahe.jpg" , image_clahe )
            #skimage.io.imsave(baseName +"-masked.jpg" , image*final_mask )
            #skimage.io.imsave(baseName +"-subtracted.jpg" , subtracted )
            # =================================================================================
            
            # Plotting ========================================================================
            if self.cS.outputImgModSteps: 
                fig, axes = plt.subplots(ncols=3,nrows=3, figsize=(15, 8), sharex=True, sharey=True)
                fig.set_tight_layout(True)
                i = 1
                class ax: pass
                for row in axes:
                    for a in row:
                        setattr(ax,"ax%i" % i,  a)
                        i+=1
                
                #plt.matshow( image_clahe , cmap=cm.Greys_r, interpolation='none' );
                
                ax.ax1.imshow(image,cmap=cm.Greys_r)
                ax.ax1.set_title(r'original image')
                ax.ax1.axis('off')
                
                ax.ax2.imshow(subtracted,cmap=cm.Greys_r, interpolation='none')
                ax.ax2.set_title(r'image$\rightarrow$subtracted , background subtracted')
                ax.ax2.axis('off')
                              
                
                ax.ax3.imshow(binary,cmap=cm.Greys_r, interpolation='none')
                ax.ax3.set_title(r'subtracted$\rightarrow$binary , otsu threshold')
                ax.ax3.axis('off')
                
                ax.ax4.imshow(binary2,cmap=cm.Greys_r, interpolation='none')
                ax.ax4.set_title(r'binary$\rightarrow$binary2 ,  morph. opening')
                ax.ax4.axis('off')
                
                ax.ax5.imshow(binary3,cmap=cm.Greys_r, interpolation='none')
                ax.ax5.set_title(r'subtracted$\rightarrow$binary3 , ' + "%f*otsu threshold"  % self.cS.otsuThMult )
                ax.ax5.axis('off')

                
                ax.ax6.imshow(denoise,cmap=cm.Greys_r, interpolation='none')
                ax.ax6.axis('off')
                ax.ax6.set_title(r'binary3$\rightarrow$denoise, removed small objects')
                
                
                ax.ax7.imshow(dilated,cmap=cm.Greys_r, interpolation='none')
                ax.ax7.axis('off')
                ax.ax7.set_title(r'denoise$\rightarrow$dilated, dilation to thicken up')
                
                ax.ax8.imshow(blurred,cmap=cm.Greys_r, interpolation='none')
                ax.ax8.axis('off')
                ax.ax8.set_title(r'dilated$\rightarrow$blurred, gaussian filter')
                
                
                for n, contour in enumerate(contours):
                    ax.ax8.plot(contour[:, 1], contour[:, 0], 'r', linewidth=1)
                #ax3.plot(contourMax[:,1], contourMax[:,0], "bo", linewidth=2 ) 
                if contourInterp: 
                    ax.ax8.plot(contourInterp[1], contourInterp[0], "r", linewidth=2)    
                
                
                ax.ax9.imshow(image,cmap=cm.Greys_r, interpolation='none')

                ax.ax9.imshow(np.ma.masked_where(final_mask==0,final_mask),
                           cmap=cm.jet, alpha=0.8 ,interpolation='none')
                ax.ax9.axis('off')
                ax.ax9.set_title('masked')
                    
                fig.savefig(baseName +"-modficationSteps.jpg")
                plt.close(fig)
                f=None
                ax=None
                for ax in axes:
                    ax = None
            # =================================================================================
            
            
            # Make Contour Frames
            if self.cS.outputContour:
                dpi=100
                f = plt.figure(num=None, frameon=False, figsize=(background.shape[1]/dpi,background.shape[0]/dpi), dpi=dpi)
                ax = plt.Axes(f, [0., 0., 1., 1.])
                #ax.set_axis_off()
                f.add_axes(ax)
                ax.imshow(image,cmap=cm.Greys_r)
                ax.set_autoscalex_on(False)
                ax.set_autoscaley_on(False)
                if contourInterp:
                   ax.plot(contourInterp[1], contourInterp[0], "b", linewidth=2)
                f.savefig(baseName + "-contour.jpg")
                plt.close(f)
                f=None
                ax=None
            
            # Make Mask Frames
            if self.cS.outputMask:
                dpi=100
                f = plt.figure(num=None, frameon=False, figsize=(background.shape[1]/dpi,background.shape[0]/dpi), dpi=dpi)
                ax = plt.Axes(f, [0., 0., 1., 1.])
                #ax.set_axis_off()
                f.add_axes(ax)
                ax.imshow(binary3,cmap=cm.Greys_r)
                ax.set_autoscalex_on(False)
                ax.set_autoscaley_on(False)
                f.savefig(baseName + "-mask.jpg")
                plt.close(f)
                f=None
                ax=None
            
            if "h5Compression" in self.cS and self.cS.h5Compression:
                comp = self.cS.h5Compression
            else:
                comp=None
                
            
                
            h5File  = h5py.File(outputFile, 'w')
            dataset = h5File.create_dataset("bounds", data=np.array(bounds))
            dataset = h5File.create_dataset("data", data=np.flipud(image), compression=None) # flip image,mask for ACCIV
            dataset = h5File.create_dataset("mask", data=np.flipud(self.cS.mask), compression=None)
            dataset = h5File.create_dataset("finalMask", data=np.flipud(final_mask), compression=comp)
            dataset = h5File.create_dataset("contourX", data=contourInterp[0], compression=comp)
            dataset = h5File.create_dataset("contourY", data=contourInterp[1], compression=comp)
            dataset = h5File.create_dataset("time", data=np.array(time))
            h5File.close()


