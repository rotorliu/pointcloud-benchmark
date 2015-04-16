#!/usr/bin/env python
################################################################################
#    Created by Oscar Martinez                                                 #
#    o.rubi@esciencecenter.nl                                                  #
################################################################################
import os, logging
from pointcloud import pdalops, postgresops, utils, lasops
from pointcloud.postgres.AbstractLoader import AbstractLoader

class Loader(AbstractLoader):
    def initialize(self):
        # Initialize DB and extensions if creation of user is required
        if self.cDB:
            self.createDB()
            connection = self.getConnection()
            cursor = connection.cursor()
            self.initPointCloud(cursor)
        else:
            connection = self.getConnection()
            cursor = connection.cursor()
        
        logging.info('Getting files and extent from input folder ' + self.inputFolder)
        (self.inputFiles, _, _, self.minX, self.minY, self.minZ, _, _, _, self.scaleX, self.scaleY, self.scaleZ) = lasops.getPCFolderDetails(self.inputFolder)
        
        self.createBlocksTable(cursor, self.blockTable, self.tableSpace)
        connection.close()
 
    def process(self):
        logging.info('Starting data loading with PDAL (parallel by python) from ' + self.inputFolder + ' to ' + self.dbName)
        return self.processMulti(self.inputFiles, self.numProcessesLoad, self.loadFromFile)
        
    def loadFromFile(self, index, fileAbsPath):
        # Get connection
        connection = self.getConnection()
        cursor = connection.cursor()
        # Add point cloud format to poinctcloud_formats table
        (dimensionsNames, pcid, compression) = self.addPCFormat(cursor, self.schemaFile, fileAbsPath, self.srid)
        connection.close()

        # Get PDAL config and run PDAL
        xmlFile = os.path.basename(fileAbsPath) + '.xml'
        pdalops.PostgreSQLWriter(xmlFile, fileAbsPath, self.getConnectionString(), pcid, dimensionsNames, self.blockTable, self.srid, self.blockSize, compression)
        pdalops.executePDAL(xmlFile)

    def close(self):
        connection = self.getConnection()
        cursor = connection.cursor()
        self.indexBlockTable(cursor, self.blockTable, self.indexTableSpace, False, self.cluster)    
        connection.close()
        
    def getNumPoints(self):
        return self.getNumPointsBlocks(self.blockTable)
