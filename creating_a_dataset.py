####################################################################################
## TITLE:                  Creating  new dataset                                                                                                                                      
## AUTHOR:              Rosie Bell, for the Department _________, Western Australia                                 
## CONTACT:            Ph: ________    Email: __________
## DATE:                   Aug 2016                                                                                 
## NOTES:                 Programmed using Python2.7 and tested on ArcGIS 10.3                                       
## DEPENDANCIES:    arcpy, sys, os, time, ctypes                                                                                     
## DESCRIPTION:       Script uses layers from SDE as well as shapefiles imported from another source - all clipped to a shape using this
##                          	  script used in python window within arcpy                                                                                                           
####################################################################################

#================================ IMPORT DEPENDANCIES ================================
import arcpy, sys, os, time, ctypes

print ("imported dependencies")

#================================ ENV SETTINGS ================================
 
#Set initial environment to import files 
arcpy.env.workspace = r'J:\foo\bar.gdb'

#create new geodatabase with timestamp in the name
timestr = time.strftime("%Y%d%m_%H%M_%S")
gdbName = 'geoprocessed_datasets_' + timestr + '.gdb'
gdbPath = r'J:\foo'
arcpy.CreateFileGDB_management(gdbPath, gdbName)
geoprocessedgdbPathAndName = os.path.join(gdbPath, gdbName)


##import files by looping through initial workspace and copying each feature class to a new geodatabase##

# Use the ListFeatureClasses function to return a list of shapefiles.
featureclasses = arcpy.ListFeatureClasses()

#copy each fc from original env to new env
for fc in featureclasses:
    arcpy.FeatureClassToFeatureClass_conversion(fc, geoprocessedgdbPathAndName, fc)


# set new geodatabase as the new workspace
arcpy.env.workspace = geoprocessedgdbPathAndName
arcpy.env.overwriteOutput = True


# ================================ GLOBAL VARIABLES ================================
datasetsToMerge = ["dataset1", "dataset2", "dataset3", "dataset4", "dataset5", "dataset6"]
dropFields = ["UFI", "COMMENT_", "CLASSIFCTN"]
datasetsToAddAttributes = ['dataset1',   'dataset2',   'dataset3',    'dataset4', 'dataset5',    'dataset6',   'dataset7']
fcDictionary = {
    'oldname1': 'newname1',  
    'oldname2': 'newname2', 
    'oldname3': 'newname3'}


# ================================ FUNCTIONS ================================
def addSourceField():
    #loop over feature classes in the list, where source fields should be added
    for fc in datasetsToAddAttributes:
        fieldName = fcDictionary[fc]
        fieldName = fieldName.upper()
        arcpy.AddField_management(fc, fieldName, "TEXT", field_length = 50)
        with arcpy.da.UpdateCursor(fc, fieldName) as cursor:
            for row in cursor:
                row[0] = "YES"
                cursor.updateRow(row)

                
def bufferBy50m(fc_in, fc_out):
    #buffer point or line by 50m
    arcpy.Buffer_analysis(fc_in, fc_out, "50 Meters", "FULL", "ROUND", "NONE")

def delete_polygons(fc_in, fc_out):
    #Make feature layer
    arcpy.MakeFeatureLayer_management(fc_in, fc_out)
    unneededValues = ["", "20 - 30m", "30 - 40m", "40 - 50m", "No Class"]
    print "feature layer created"
    
    #Select features
    arcpy.SelectLayerByAttribute_management(fc_out, "NEW_SELECTION", """VALUES IN ( ' ', '20 - 30m', '30 - 40m', '40 - 50m', 'No Class')""")
    print "selected polygons"

    #delete selected polygons
    arcpy.DeleteFeatures_management(fc_out)
    print "deleted polygons"

# ================================ GEOPROCESSING ================================

### Part 1: Create single layer of features with selected value ####

#buffer by 50m
bufferBy50m("dataset1", "dataset1_buffered_50m")

print ("buffer done")

#delete fields that cause merge errors
featureClasses = arcpy.ListFeatureClasses()
for fc in featureClasses:
    if fc in datasetsToMerge:
        print (fc)
        #delete the field 
        arcpy.DeleteField_management(fc, dropFields)

print "delete fields complete"

#merge datasets to make single dataset 
arcpy.Merge_management(datasetsToMerge, "dataset2")
print("merge complete")

#delete  values that are outside range
delete_polygons("dataset2", "dataset2_in_range")

# dissolve polygons
arcpy.Dissolve_management("dataset2", "dataset2_dissolved")

#### Part 2: Add attributes to show  values #####
#buffer points by 50m
bufferBy50m("dataset3", "dataset3_buffered_50m")
bufferBy50m("dataset4", "dataset4_buffered_50m")

print ("points buffered")
# add field to each fc, with name of feature class
addSourceField()

print ("source fields added")

## add attributes from each values layer by using the union tool, then clip ##

arcpy.Union_analysis([
    "dataset1", "dataset2", "dataset3", "dataset4", "dataset5", "dataset6"], "union")
    
print ("union complete")    

arcpy.Clip_analysis("union", "dataset1","attributed_dataset")


##delete unneccesary fields from attributed dataset##

#list all fields
fields = arcpy.ListFields ("attributed_dataset")

# manually enter field names to keep here
# include mandatory fields name such as OBJECTID (or FID), and Shape in keepfields
keepFields = [
	'fieldname1', 'fieldname2','fieldname3', 'fieldname4', 'fieldname5'
]

# create dropFields list (all the fields not in keepFields)
dropFields = [f.name for f in fields if f.name not in keepFields]

# delete the fields
arcpy.DeleteField_management("attributed_dataset", dropFields)

## Rename fields  ##

renameFieldDictionary = {
    'oldname1': 'newname1',  
    'oldname2': 'newname2', 
    'oldname3': 'newname3'}

for key in renameFieldDictionary:
	arcpy.AlterField_management("attributed_dataset", key, renameFieldDictionary[key])


## alert box when complete##
timestr = time.strftime("%Y%d%m_%H%M_%S")
print "script completed at " + timestr



ctypes.windll.user32.MessageBoxA(0, "Script is complete", "Python alert", 1)


