## ===============================================================================================================
## Name:    Download CLU by Tract
## Purpose: Download the CLU for a tract into the installed support database based on
##          values specified by user inputs for admin state, county, and tract.
##
## Authors: Chris Morse
##          GIS Specialist
##          Indianapolis State Office
##          USDA-NRCS
##          chris.morse@usda.gov
##          317.295.5849
##
##          Adolfo Diaz
##          GIS Specialist
##          National Soil Survey Center
##          USDA-NRCS
##          adolfo.diaz@usda.gov
##          608.662.4422, ext. 216
##
## Created: 2/24/2021
##
## ===============================================================================================================
## Changes
## ===============================================================================================================
##
##
## ===============================================================================================================
##
##
## ===============================================================================================================
## Main Body
## ===============================================================================================================

#### Import system modules
import sys, string, os, traceback, re
import datetime, shutil
import arcpy
from importlib import reload
sys.dont_write_bytecode=True
scriptPath = os.path.dirname(sys.argv[0])
sys.path.append(scriptPath)

import extract_CLU_by_Tract
reload(extract_CLU_by_Tract)


#### Set overwrite
arcpy.env.overwriteOutput = True


#### Wrap it
try:
    
    #### Inputs
    arcpy.AddMessage("Reading inputs...\n")
    sourceState = arcpy.GetParameterAsText(2)
    sourceCounty = arcpy.GetParameterAsText(4)
    tractList = arcpy.GetParameter(5)
    #tractNumber = arcpy.GetParameterAsText(5)
    cluFeatureClass = arcpy.GetParameterAsText(7)

    arcpy.AddMessage("\nTracts to process:")
    for tract in tractList:
        arcpy.AddMessage("\n" + str(tract))


    #### Map Layer Names
    cluOut = "Project_CLU"
    basedataGDB_path = os.path.join(os.path.dirname(sys.argv[0]), "scratch.gdb")
    #projectCLU = basedataGDB_path + os.sep + cluOut
    projectCLU = cluFeatureClass
    
    #### Test for Pro project.
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
    except:
        arcpy.AddError("\nThis tool must be run from an active ArcGIS Pro project. Exiting...\n")
        exit()
        

    #### Set output spatial reference
    activeMap = aprx.activeMap
    try:
        activeMapName = activeMap.name
        activeMapSR = activeMap.getDefinition('V2').spatialReference['latestWkid']
        outSpatialRef = arcpy.SpatialReference(activeMapSR)
    except:
        arcpy.AddError("Could not get a spatial reference! Please run the tool from the Catalog Pane with an active ArcGIS Pro Map open! Exiting...")
        exit()
    arcpy.env.outputCoordinateSystem = outSpatialRef


    #### Set transformation (replace with assignment from Transformation lookup from cim object of active map object in the future)
    arcpy.env.geographicTransformations = "WGS_1984_(ITRF00)_To_NAD_1983"


    #### Update the default aprx workspace to be the installed SCRATCH.gdb in case script validation didn't work or wasn't set
    aprx.defaultGeodatabase = basedataGDB_path


    #### Check GeoPortal Connection
    nrcsPortal = 'https://gis.sc.egov.usda.gov/portal/'
    portalToken = extract_CLU_by_Tract.getPortalTokenInfo(nrcsPortal)
    if not portalToken:
        arcpy.AddError("Could not generate Portal token! Please login to GeoPortal! Exiting...")
        exit()


    #### Check Inputs for existence and create FIPS code variables
    lut = os.path.join(os.path.dirname(sys.argv[0]), "support.gdb" + os.sep + "lut_census_fips")
    if not arcpy.Exists(lut):
        arcpy.AddError("Could not find state and county lookup table! Contact the GIS Specialist for assistance. Exiting...\n")
        exit()


    #### Search for FIPS codes to give to the Extract CLU Tool/Function. Break after the first row (should only find one row in any case).
    stfip, cofip = '', ''
    fields = ['STATEFP','COUNTYFP','NAME','STATE','STPOSTAL']
    field1 = 'STATE'
    field2 = 'NAME'
    expression = "{} = '{}'".format(arcpy.AddFieldDelimiters(lut,field1), sourceState) + " AND " + "{} = '{}'".format(arcpy.AddFieldDelimiters(lut,field2), sourceCounty)
    with arcpy.da.SearchCursor(lut, fields, where_clause = expression) as cursor:
        for row in cursor:
            stfip = row[0]
            cofip = row[1]
            adStatePostal = row[4]
            break
        
    if len(stfip) != 2 and len(cofip) != 3:
        arcpy.AddError("State and County FIPS codes could not be retrieved! Contact the GIS Specialist for assistance. Exiting...\n")
        exit()

    if adStatePostal == '':
        arcpy.AddError("State postal code could not be retrieved! Contact the GIS Specialist for assistance. Exiting...\n")
        exit()


    #### Transfer found values to variables to use for CLU download and project creation.
    adminState = stfip
    adminCounty = cofip
    postal = adStatePostal.lower()


    #### Remove the existing projectCLU layer from the Map
    arcpy.AddMessage("\nRemoving CLU layer from project maps, if present...\n")
    mapLayersToRemove = [projectCLU]
    try:
        for maps in aprx.listMaps():
            for lyr in maps.listLayers():
                if lyr.name in mapLayersToRemove:
                    maps.removeLayer(lyr)
    except:
        pass


    #### Delete the existing CLU
    if arcpy.Exists(projectCLU):
        try:
            arcpy.Delete_management(projectCLU)
        except:
            pass
        

    #### Download the CLU
    arcpy.AddMessage("\nDownloading latest CLU data for input tract number...")
    x=0
    cluTempPath = []
    for tractNumber in tractList:
        cluTempPath.append(extract_CLU_by_Tract.start(adminState, adminCounty, tractNumber, outSpatialRef, basedataGDB_path))
        x = x + 1

    cluExists = []
    for fc in cluTempPath:
        if arcpy.Exists(fc):
            cluExists.append(fc)

    arcpy.AddMessage("\nMerging CLUs to one dataset...")
    try:
        arcpy.management.Merge(cluExists, projectCLU)
    except:
        arcpy.AddMessage("\nNo tracts to merge... Exiting.")
    arcpy.AddMessage("\nDeleting temporary CLUs from SCRATCH.gdb...")
    for fc in cluExists:
        arcpy.management.Delete(fc)

    #### Add results to map
    arcpy.SetParameterAsText(6, projectCLU)


    #### Compact FGDB
    try:
        arcpy.Compact_management(basedataGDB_path)
    except:
        pass


except SystemExit:
    pass

