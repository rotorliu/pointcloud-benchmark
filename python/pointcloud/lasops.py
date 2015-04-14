#!/usr/bin/env python
################################################################################
#    Created by Oscar Martinez                                                 #
#    o.rubi@esciencecenter.nl                                                  #
################################################################################
import os
import utils
from osgeo import osr
import liblas

#
# This module contains methods that use LAStools, GDAL, lasLib to interact 
# with LAS/LAZ in the most efficient manner depending on the exact operation
#

# Check the LAStools is installed and that it is in PATH before libLAS
if utils.shellExecute('lasinfo -version').count('LAStools') == 0:
    raise Exception("LAStools is not found!. Please check that it is in PATH and that it is before libLAS")

def getSRID(absPath):
    """ Gets the SRID of a LAS/LAZ file (using liblas and GDAL, hence it is not fast)"""
    lasHeader = liblas.file.File(absPath, mode='r').header
    osrs = osr.SpatialReference()
    osrs.SetFromUserInput(lasHeader.get_srs().get_wkt())
    #osrs.AutoIdentifyEPSG()
    return osrs.GetAttrValue( 'AUTHORITY', 1 )

def getNumPoints(absPath):
    """ Get the number of points of a LAS/LAZ (using LAStools, hence it is fast)"""
    return getPCFileDetails(absPath)[0]
        
def getPCFileDetails(absPath):
    """ Get the details (count numPoints and extent) of a LAS/LAZ file (using LAStools, hence it is fast)"""
    count = None
    (minX, minY, minZ, maxX, maxY, maxZ) = (None, None, None, None, None, None)
    (scaleX, scaleY, scaleZ) = (None, None, None)
    (offsetX, offsetY, offsetZ) = (None, None, None)
    
    srid = getSRID(absPath)
    
    outputLASInfo = subprocess.Popen('lasinfo ' + absPath + ' -nc -nv -nco', shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    for line in outputLASInfo[1].split('\n'):
        if line.count('min x y z:'):
            [minX, minY, minZ] = line.split(':')[-1].strip().split(' ')
        elif line.count('max x y z:'):
            [maxX, maxY, maxZ] = line.split(':')[-1].strip().split(' ')
        elif line.count('number of point records:'):
            count = line.split(':')[-1].strip()
        elif line.count('scale factor x y z:'):
            [scaleX, scaleY, scaleZ] = line.split(':')[-1].strip().split(' ')
        elif line.count('offset x y z:'):
            [offsetX, offsetY, offsetZ] = line.split(':')[-1].strip().split(' ')
    return (srid, count, minX, minY, minZ, maxX, maxY, maxZ, scaleX, scaleY, scaleZ, offsetX, offsetY, offsetZ)

def getPCFolderDetails(absPath):
    """ Get the details (count numPoints and extent) of a folder with LAS/LAZ files (using LAStools, hence it is fast)
    It is assumed that all file shave same SRID and scale as first one"""
    tcount = 0
    (tminx, tminy, tminz, tmaxx, tmaxy, tmaxz) =  (None, None, None, None, None, None)
    (tscalex, tscaley, tscalez) = (None, None)
    tsrid = None
    
    if os.path.isdir(absPath):
        inputFiles = utils.getFiles(absPath)
    else:
        inputFiles = [absPath,]
    
    for i in range(len(inputFiles)):
        (count, minx, miny, minz, maxx, maxy, maxz, scalex, scaley, scalez, _, _, _) = getPCFileDetails(inputFiles[i])
        if i == 0:
            (tscalex, tscaley, tscalez) = (scalex, scaley, scalez)
            tsrid = getSRID(inputFiles[i])
            
        tcount += count
        if count:
            if tminx == None or minx < tminx:
                tminx = minx 
            if tminy == None or miny < tminy:
                tminy = miny
            if tminz == None or minz < tminz:
                tminz = minz
            if tmaxx == None or maxx > tmaxx:
                tmaxx = maxx
            if tmaxy == None or maxy > tmaxy:
                tmaxy = maxy
            if tmaxz == None or maxz > tmaxz:
                tmaxz = maxz

    return (inputFiles, srid, tcount, tminx, tminy, tminz, tmaxx, tmaxy, tmaxz, tscalex, tscaley, tscalez)