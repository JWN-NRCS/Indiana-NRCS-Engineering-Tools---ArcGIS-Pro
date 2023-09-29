# ==========================================================================================
# Name: UpdateRainfallData.py
#
# Author: Josh Nurrenbern
#         GIS Specialist
#         IN State GIS Specialist
#         USDA - NRCS
# e-mail: joshua.nurrenbern@usda.gov
# phone: 
# Created by Josh Nurrenbern 2023
# ==========================================================================================
## ===============================================================================================================
def print_exception():
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        theMsg = "\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[1] + "\n\t" + traceback.format_exception(exc_type, exc_value, exc_traceback)[-1]
        if theMsg.find("exit") > -1:
            AddMsgAndPrint("\n\n")
            pass
        else:
            AddMsgAndPrint("\n----------------------------------- ERROR Start -----------------------------------",2)
            AddMsgAndPrint(theMsg,2)
            AddMsgAndPrint("------------------------------------- ERROR End -----------------------------------\n",2)
    except:
        AddMsgAndPrint("Unhandled error in print_exception method", 2)
        pass
## ================================================================================================================
def AddMsgAndPrint(msg, severity=0):
    # prints message to screen if run as a python script
    # Adds tool message to the geoprocessor
    # Split the message on  \n first, so that if it's multiple lines, a GPMessage will be added for each line
    print(msg)
    try:
        f = open(textFilePath,'a+')
        f.write(msg + " \n")
        f.close
        del f
    except:
        pass
    if severity == 0:
        arcpy.AddMessage(msg)
    elif severity == 1:
        arcpy.AddWarning(msg)
    elif severity == 2:
        arcpy.AddError(msg)
        exit()
## ================================================================================================================
def logBasicSettings():
    # record basic user inputs and settings to log file for future purposes
    try:
        import getpass, time
        arcInfo = arcpy.GetInstallInfo()  # dict of ArcGIS Pro information
        f = open(textFilePath,'a+')
        f.write("\n################################################################################################################\n")
        f.write("Executing \"Update Rainfall Data\" Tool \n")
        f.write("User Name: " + getpass.getuser() + "\n")
        f.write("Date Executed: " + time.ctime() + "\n")
        f.write(arcInfo['ProductName'] + ": " + arcInfo['Version'] + "\n")
        f.write("User Parameters:\n")
        f.write("\tinWatershed: " + inWatershed + "\n")
        f.close
        del f
    except:
        print_exception()
        exit()

## ================================================================================================================
# Import system modules
import sys, os, string, traceback, arcpy
if __name__ == '__main__':
    try:
        # --------------------------------------------------------------------------------------------- Input Parameters
        inRainfall = arcpy.GetParameterAsText(0)
        outPath = r'C:\GIS_Tools\Engineering_Tools_Pro\SUPPORT\Support.gdb'
        outName = 'RainfallDataTable'
        
        fields = arcpy.ListFields(inRainfall)
        
        nameList = []
        for field in fields:
            nameList.append(field.name)
            
        if nameList.count('State') != 1:
            AddMsgAndPrint("'State' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('County') != 1:
            AddMsgAndPrint("'County' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('Rainfall Type') != 1:
            AddMsgAndPrint("'Rainfall Type' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('2-YR') != 1:
            AddMsgAndPrint("'2-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('5-YR') != 1:
            AddMsgAndPrint("'5-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('10-YR') != 1:
            AddMsgAndPrint("'10-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('25-YR') != 1:
            AddMsgAndPrint("'25-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('50-YR') != 1:
            AddMsgAndPrint("'50-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('100-YR') != 1:
            AddMsgAndPrint("'100-YR' field doesn't exist in input table. Exiting.....", 2)
        if nameList.count('1-Yr') != 1:
            AddMsgAndPrint("'1-Yr' field doesn't exist in input table. Exiting.....", 2)
        
        arcpy.conversion.TableToTable(inRainfall, outPath, outName)
        AddMsgAndPrint('Rainfall Data Updated!')
    except:
        print_exception()
            
