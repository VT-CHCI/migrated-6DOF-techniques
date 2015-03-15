#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <MSR_NuiApi.h>

#include "sensor.h"

// DO NOT MODIFY THESE DECLARATIONS----------------
extern "C" __declspec(dllexport) void QuerySensor(void *);
extern "C" __declspec(dllexport) void InitializeSensor(void *);
extern "C" __declspec(dllexport) void UpdateSensor(void *);
extern "C" __declspec(dllexport) void CommandSensor(void *);
extern "C" __declspec(dllexport) void ResetSensor(void *);
extern "C" __declspec(dllexport) void CloseSensor(void *);

void QuerySensor(void *sensor)
{
	// This function gets called during the Vizard initialization process.
	// Its only purpose is to set the sensor type (see choices in sensor.h),
	// so that it can be automatically made available to the user according
	// to its type.
	// No initialization or communication should be attempted at this point
	// because the device may never be requested by user (and it might not
	// even be connected!).

	//A short description of your plugin
	strcpy(((VRUTSensorObj *)sensor)->version, "Worldviz Driver v1.0");
	//Your plugin type e.g.( SENSOR_HEADPOS | SENSOR_HEADORI | SENSOR_QUATERNION )
	((VRUTSensorObj *)sensor)->type = SENSOR_HEADPOS | SENSOR_HEADORI | SENSOR_QUATERNION;
}


void InitializeSensor(void *sensor)
{
	//Called each time an instance is created.

	//This function will attempt to connect to the device and initialize any variables.

	//You can set the size of the data field to any value.
	//After this function is called, Vizard will allocate the
	//data field of the plugin to the size given here. Then you
	//can put any values you want in the data field and the user
	//can get those values by calling the "get" command on the
	//sensor object in the script.
	//It is suggested that the size of the data field be 7 or higher
	((VRUTSensorObj*)sensor)->dataSize = 105;

	//If you have multiple instances you can store your own unique
	//identifier in the user data field.
	((VRUTSensorObj*)sensor)->user[0] = 0;

	//If initialization failed then set status to FALSE, if it succeeded set it to TRUE.
	if (NuiInitialize(NUI_INITIALIZE_FLAG_USES_SKELETON) == 0) {
		((VRUTSensorObj *)sensor)->status = TRUE;
	}
	else {
		((VRUTSensorObj *)sensor)->status = FALSE;
	}
}



void UpdateSensor(void *sensor)
{
	// Update the sensor data fields (see sensor.h)
	// Fields 0-2: reserved for x, y, z position data
	// Fields 3-5: reserved for yaw, pitch, roll if SENSOR_EULER1 is specified in type
	// or
	// Fields 3-6: reserved for quaternion data if SENSOR_QUATERNION is specified in type
	// 
	// eg:
	// ((VRUTSensorObj *)sensor)->data[0] = newX;
	// If this plugin is not a SENSOR_HEADPOS or SENSOR_HEADORI then you can fill
	// the data fields with whatever you want and retrieve it with the "<sensor>.get()" command
	// in your script.

	NUI_SKELETON_FRAME skeletonFrame;

	NuiSkeletonGetNextFrame(5,&skeletonFrame);
	NuiTransformSmooth(&skeletonFrame,NULL);
	

	((VRUTSensorObj *)sensor)->data[0] = 7;
	
	int i,j,k;

	for(i=0; i<6; i++) {
		if (skeletonFrame.SkeletonData[i].eTrackingState == NUI_SKELETON_TRACKED) {
			((VRUTSensorObj *)sensor)->data[0] = i;
			
			k = 1;
			
			for(j=0; j<20; j++) { 
				((VRUTSensorObj *)sensor)->data[k] = skeletonFrame.SkeletonData[i].SkeletonPositions[j].x;
				k++;
				
				((VRUTSensorObj *)sensor)->data[k] = skeletonFrame.SkeletonData[i].SkeletonPositions[j].y;
				k++;

				((VRUTSensorObj *)sensor)->data[k] = skeletonFrame.SkeletonData[i].SkeletonPositions[j].z;
				k++;
				
				((VRUTSensorObj *)sensor)->data[k] = skeletonFrame.SkeletonData[i].SkeletonPositions[j].w;
				k++;

				((VRUTSensorObj *)sensor)->data[k] = skeletonFrame.SkeletonData[i].eSkeletonPositionTrackingState[j];
				k++;
			}
		}
	}
}


void ResetSensor(void *sensor)
{
	// If the user were to send a reset command, do whatever makes sense to do.
}

void CommandSensor(void *sensor)
{
	// The user has sent a command to the sensor.
	// The command is saved in sensor->command.
	// 3 floating point numbers are saved under
	// sensor->data Fields 0-2.
	// A string is saved in sensor->custom. Don't forget
	// to cast it to a (char*)
	char msg[30];
	float x,y,z;
	switch( (int) ((VRUTSensorObj *)sensor)->command) {
		case 1:
			strcpy(msg,(char *)((VRUTSensorObj *)sensor)->custom);
			x = ((VRUTSensorObj *)sensor)->data[0];
			y = ((VRUTSensorObj *)sensor)->data[1];
			z = ((VRUTSensorObj *)sensor)->data[2];
			break;
		case 9:
			NuiShutdown();
			break;
		default:
			break;
	}
}

void CloseSensor(void *sensor)
{
	// Go ahead, clean up, and close files and COM ports.
	//Called only once no matter how many instances were created
	NuiShutdown();
}