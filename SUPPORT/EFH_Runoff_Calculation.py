# ==========================================================================================
# Name: Calculate_RunoffCurveNumber.py
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
        f.write("Executing \"1. Runoff Calculation\" Tool \n")
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
def peakRunoff(coeffDict, P, CN, tc, acres, Fp=1): #distType = NOAA Distribution type P = actual rainfall, CN = Curve Number, tc = time of concentration, acres = watershed area in acres, Fp is adjustment factor for pond and swamp areas
    sqmi = acres / 640 #convert acres to square miles
    S = (1000/CN) - 10 #S is max retention after runoff begins
    ratioActual = (0.2 * S / P)

    ratioList = list(coeffDict.keys())
    ratios = []
    for v in ratioList:
        ratios.append(float(v))
    ratios = sorted(ratios)
    maxRatio = max(ratios)
    minRatio = min(ratios)
    if ratioActual < minRatio:
        ratio = minRatio
    elif ratioActual > maxRatio:
        ratio = maxRatio
    else:
        ratio = ratioActual
        
    if ratioActual in ratios:
        c0 = coeffDict[str(ratioActual)]['c0']
        c1 = coeffDict[str(ratioActual)]['c1']
        c2 = coeffDict[str(ratioActual)]['c2']
    else:
        #find cloest ratio that is smaller than the actual
        y = 100
        z = 100
        for x in ratios:
            diff = ratioActual - x
            if diff < 0 and abs(diff) < z:
                high = x
                z = abs(diff)
            elif diff > 0 and diff < y:
                low = x
                y = diff      

        if ratio < 0.25:
            low = 0.1
            high = 0.25
        elif ratio < 0.3:
            low = 0.25
            high = 0.3
        elif ratio < 0.4:
            low = 0.3
            high = 0.4
        else:
            low = 0.4
            high = 0.5

        #AddMsgAndPrint('Ratio low: ' + str(low))
        #AddMsgAndPrint('Ratio high: ' + str(high))
        try:
            c0a = coeffDict[str(low)]['c0']
            c1a = coeffDict[str(low)]['c1']
            c2a = coeffDict[str(low)]['c2']
            c0b = coeffDict[str(high)]['c0']
            c1b = coeffDict[str(high)]['c1']
            c2b = coeffDict[str(high)]['c2']
        except:
            #AddMsgAndPrint('There is something wrong with the dictionary (Probably)')
            exit()
        c0 = (ratio-low)/(high-low)*(c0b-c0a)+c0a
        c1 = (ratio-low)/(high-low)*(c1b-c1a)+c1a
        c2 = (ratio-low)/(high-low)*(c2b-c2a)+c2a
    
    print('c0 = ' + str(c0))
    print('c1 = ' + str(c1))
    print('c2 = ' + str(c2))

    Q = ((P-0.2*S)**2)/(P + 0.8 * S) #runoff
    qu = 10**(c0 + (c1 * math.log10(tc)) + (c2 * math.log10(tc)**2))   #unit peak flow
    qp = qu * sqmi * Q * Fp  #peak discharge

    
    qp = str(math.ceil(qp))
    Q = round(Q, 2)
    ratio = str(round(ratio,2))
    qu = round(qu, 3)
    
    return Q, qu, qp, ratio

## ================================================================================================================
def updateLayout(efhLyt, elmName, elmNum, value):

    elmName = elmName + str(elmNum)
    elm = efhLyt.listElements("TEXT_ELEMENT", elmName)[0]
    elm.text = str(value)
    return    

## ================================================================================================================
# Import system modules
import sys, os, string, traceback, arcpy, math

if __name__ == '__main__':
    try:
        # --------------------------------------------------------------------------------------------- Input Parameters
        inWatershed = arcpy.GetParameterAsText(0)
        inRainfallTable = arcpy.GetParameterAsText(1)
        inState = arcpy.GetParameterAsText(3)
        inCounty = arcpy.GetParameterAsText(5)
        inClient = arcpy.GetParameterAsText(6)
        inPractice = arcpy.GetParameterAsText(7)
        inUser = arcpy.GetParameterAsText(8)

        inCoeffTable = r'C:\GIS_Tools\Engineering_Tools_Pro\Support\Support.gdb\RunoffCoefficientsTable'
        
        # ---------------------------------------------------------------------------- Define Variables
        # inWatershed can ONLY be a feature class
        watershed_path = arcpy.Describe(inWatershed).CatalogPath
        if watershed_path.find('.gdb') > 0:
            watershedGDB_path = watershed_path[:watershed_path.find('.gdb')+4]
        else:
            AddMsgAndPrint("\n\nWatershed Layer must be a File Geodatabase Feature Class!.....Exiting",2)
            AddMsgAndPrint("You must run \"Prepare Soils and Landuse\" tool first before running this tool\n",2)
            exit()
            
        watershedFD_path = watershedGDB_path + os.sep + "Layers"
        watershedGDB_name = os.path.basename(watershedGDB_path)
        userWorkspace = os.path.dirname(watershedGDB_path)
        wsName = os.path.basename(inWatershed)
        inLength = watershedFD_path + os.sep + wsName + "_FlowPaths" #Flow Length table
        # ------------------------------------------------------------------------Check active APRX and layout exists
        # Check for active APRX
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
        except:
            arcpy.AddError("This tool must be run from an active ArcGIS Pro project. Exiting...")
            exit()
        #Check for expected contents of APRX, namely the layout
        try:
            efhLayout = aprx.listLayouts("EFHLayout")[0]
        except:
            arcpy.AddError("\nThe EFH Layout is missing from the project. Please use the installed template or a template developed from the installed template. Exiting...")
            exit()  
        
        # ---------------------------------------------------------------Add fields to inWatershed
        arcpy.SetProgressorLabel('Adding Fields to Watershed')
        if not len(arcpy.ListFields(inWatershed,"Lenngth_ft")) > 0:  #length field
            arcpy.AddField_management(inWatershed, "Length_ft", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED")

        if not len(arcpy.ListFields(inWatershed,"Time_Concentration")) > 0:  #time of concentration field
            arcpy.AddField_management(inWatershed, "Time_Concentration", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED")        
        AddMsgAndPrint('Fields added to Watershed')
        # ------------------------------------------------------------------------------------------------ Put the watershed flowpath length in Watershed Attribute Table
        arcpy.SetProgressorLabel('Getting flowpath length')
        with arcpy.da.UpdateCursor(inWatershed,['Subbasin','Length_ft']) as cursor:
            for row in cursor:

                # Get the RCN Value from rcn_stats table by subbasin number
                subBasinNumber = row[0]

                # subbasin values should not be NULL
                if subBasinNumber is None or len(str(subBasinNumber)) < 1:
                    AddMsgAndPrint("\n\tSubbasin record is NULL in " + wsName,2)
                    continue

                expression = (u'{} = ' + str(subBasinNumber)).format(arcpy.AddFieldDelimiters(inLength, "Subbasin"))
                Length_ft = [row[0] for row in arcpy.da.SearchCursor(inLength,["Length_ft"],where_clause=expression)][0]

                # Update the inWatershed subbasin RCN value
                row[1] = Length_ft
                cursor.updateRow(row)

                AddMsgAndPrint("\n\tSubbasin ID: " + str(subBasinNumber))
                AddMsgAndPrint("\t\tWatershed Length Value: " + str(round(Length_ft,0)))
        AddMsgAndPrint('Flowpath length added to watershed')

        # ------------------------------------------------------------------------------------------------ Calculate the Time of Concentration
        expression = "(math.pow(!Length_ft!, 0.8) * math.pow((((1000/!RCN!)-10) + 1), 0.7))/(1140 * math.pow(!Avg_Slope!, 0.5))"
        arcpy.management.CalculateField(inWatershed, 'Time_Concentration', expression)
        
        # ------------------------------------------------------------------------------------------------ Get county specific rainfall data
        arcpy.SetProgressorLabel('Getting county specific rainfall data')
        rainFields = ['State', 'County', 'Rainfall_Type', 'F1_Yr', 'F2_YR', 'F5_YR', 'F10_YR', 'F25_YR', 'F50_YR', 'F100_YR']                      
        with arcpy.da.SearchCursor(inRainfallTable, rainFields) as cursor:
            for row in cursor:
                if row[0] == inState and row[1] == inCounty:
                    rainfall = row[3:]
                    rainfallType = row[2]
                    break
        AddMsgAndPrint('Rainfall Distribution type: ' + rainfallType)

        # ------------------------------------------------------------------------------------------------Create Distribution Dictionary
        arcpy.SetProgressorLabel('Getting coefficients distribution type')
        distDict = {}
        x = 0
        with arcpy.da.SearchCursor(inCoeffTable, ['ratio', 'coeff_0', 'coeff_1', 'coeff_2'] ) as cursor:
            for row in cursor:
                if x == 0:
                    distType = str(row[0])
                    x = row[1]
                    if x < 0:
                        AddMsgAndPrint("There can't be a negative number of ratios.  Exiting...", 2)
                    distDict[distType] = {}
                elif x > 0:
                    distDict[distType][row[0]] = {"c0" : row[1], "c1" : row[2], "c2" : row[3]}
                    x = x-1
        
        AddMsgAndPrint('Rainfall Coeficients for Distribution Type gathered')
        
        #-------------------------------------------------------------------Setup Layout
        arcpy.SetProgressorLabel('Setting up layout')

        elementNames = ["Frequency", "Rainfall", "Ratio", "Runoff", "RunoffAC", "UPD", "CFS"]

        updateLayout(efhLayout, "Client", "", inClient) #Client Update
        updateLayout(efhLayout, "County", "", inCounty) #County Update
        updateLayout(efhLayout, "State", "", inState) #State Update
        updateLayout(efhLayout, "Practice", "", inPractice) #Practice Update
        updateLayout(efhLayout, "User", "", inUser) #User Update        
        AddMsgAndPrint('Layout background info entered')
        
        # ------------------------------------------------------------------------------------------------Create table for each basin
        with arcpy.da.SearchCursor(inWatershed, ['Subbasin', 'Watershed_Name', 'Time_Concentration', 'Acres', 'RCN', 'Avg_Slope', 'Length_ft'] ) as cursor:
            for row in cursor:
                if row[1] is None:
                    watershedName = "Subbasin " + str(row[0])
                else:
                    watershedName = row[1]

                strCheck = watershedName.replace(" ", "").isalnum()
                if strCheck == 0:
                    AddMsgAndPrint('Your watershed name contains special characters, please rename your watershed with only letters, numbers, and spaces. Exiting...', 2)
                watershedName = watershedName.replace(" ", "_")

                arcpy.SetProgressorLabel('Creating table for ' + watershedName)
                tc = row[2]
                acres = row[3]
                CN = row[4]
                slope = row[5]
                length = row[6]
                tcT = str(round(tc, 2))
                acresT = str(round(acres, 2))
                CNT = str(round(CN, 2))
                slopeT = str(round(slope, 2))
                lengthT = str(round(length, 2))

                #------------------------------------------------------Create table for watershed and add fields to it    
                arcpy.management.CreateTable(watershedGDB_path, wsName + '_' + watershedName)
                workingTable = watershedGDB_path + os.sep + wsName + '_' + watershedName
                tableFields = ["Frequency", "Rain_24hr", "Peak_Flow", "Runoff", 'IaP']
                arcpy.AddField_management(workingTable, tableFields[0], "String", "", "", "3", "", "NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(workingTable, tableFields[1], "String", "", "", "5", "", "NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(workingTable, tableFields[2], "String", "", "", "7", "", "NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(workingTable, tableFields[3], "String", "", "", "5", "", "NULLABLE", "NON_REQUIRED")
                arcpy.AddField_management(workingTable, tableFields[4], "String", "", "", "4", "", "NULLABLE", "NON_REQUIRED")

                freqList = ['1', '2', '5', '10', '25', '50', '100']
                AddMsgAndPrint('Watershed Name: ' + watershedName)
                updateLayout(efhLayout, "WatershedName", "", watershedName) #Watershed Name Update
                AddMsgAndPrint('____Drainage Area:         ' + acresT)
                updateLayout(efhLayout, "DrainageArea", "", acresT) #Drainage Area Update
                AddMsgAndPrint('____Runoff Curve Number:   ' + CNT)
                updateLayout(efhLayout, "CurveNumber", "", CNT) #Curve Number Update
                AddMsgAndPrint('____Watershed Length:      ' + lengthT)
                updateLayout(efhLayout, "WatershedLength", "", lengthT) #Watershed Length Update
                AddMsgAndPrint('____Watershed Slope:       ' + slopeT)
                updateLayout(efhLayout, "WatershedSlope", "", slopeT) #Watershed Slope Update
                AddMsgAndPrint('____Time of Concentration: ' + tcT)
                updateLayout(efhLayout, "TimeOfConcentration", "", tcT) #Time of Concentration Update
                AddMsgAndPrint('____Rainfall Type: ', rainfallType)
                updateLayout(efhLayout, "RainfallType", "", rainfallType) #Rainfall Type Update
                AddMsgAndPrint('Storm Frequency, 24hr rainfall, CFS, Runoff, Ia/P Ratio')
                
                for x in range(7):
                    freq = freqList[x]
                    rain = rainfall[x]
                    runoff, unitPeak, peakDischarge, IaP = peakRunoff(distDict[rainfallType], rain, CN, tc, acres, 1)

                    with arcpy.da.InsertCursor(workingTable, tableFields) as cursor:
                        insertRowFields = [freq, rain, peakDischarge, runoff, IaP]
                        AddMsgAndPrint(insertRowFields)
                        cursor.insertRow(insertRowFields)
                    elmName = elementNames[0] + str(x+1)
                    ##updateLayout (efhLayout, elmName, elmNum, value)
                    updateLayout(efhLayout, elementNames[0], x+1, freq) #Frequency Update
                    updateLayout(efhLayout, elementNames[1], x+1, rain) #Frequency Update
                    updateLayout(efhLayout, elementNames[2], x+1, IaP) #Frequency Update
                    updateLayout(efhLayout, elementNames[3], x+1, runoff) #Runoff Update
                    runoffAC = round(runoff * acres / 12, 2)
                    updateLayout(efhLayout, elementNames[4], x+1, runoffAC) #Runoff Ac Update
                    updateLayout(efhLayout, elementNames[5], x+1, unitPeak) #Unit Peak Discharge Update
                    updateLayout(efhLayout, elementNames[6], x+1, peakDischarge) #Peak Discharge Update
                    
                arcpy.SetProgressorLabel('Saving Layout to PDF')
                EFH_PDF = os.path.join(userWorkspace, watershedName + "_EFH.pdf")
                efhLayout.exportToPDF(EFH_PDF, resolution = 300, image_quality = "NORMAL", layers_attributes = "LAYERS_AND_ATTRIBUTES")
                os.startfile(EFH_PDF)
                
                
        
    except:
        print_exception()
            
