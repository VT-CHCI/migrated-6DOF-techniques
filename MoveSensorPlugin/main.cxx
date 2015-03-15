#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <vector>

#include "sensor.h"
#include "moveclient.h"

// DO NOT MODIFY THESE DECLARATIONS----------------
extern "C" __declspec(dllexport) void QuerySensor(void *);
extern "C" __declspec(dllexport) void InitializeSensor(void *);
extern "C" __declspec(dllexport) void UpdateSensor(void *);
extern "C" __declspec(dllexport) void CommandSensor(void *);
extern "C" __declspec(dllexport) void ResetSensor(void *);
extern "C" __declspec(dllexport) void CloseSensor(void *);

int sensorCount = 0;

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
	strcpy(((VRUTSensorObj *)sensor)->version, "Worldviz moveme Driver v1.0");
	//Your plugin type e.g.( SENSOR_HEADPOS | SENSOR_HEADORI | SENSOR_QUATERNION )
	((VRUTSensorObj *)sensor)->type = SENSOR_HEADPOS | SENSOR_HEADORI | SENSOR_QUATERNION;
}

typedef struct {
	VRUTSensorObj*		instance;
} MySensor;

std::vector< MySensor > m_sensors;

void InitializeSensor(void *sensor)
{
	//Called each time an instance is created.
	MySensor ms;
	ms.instance = ((VRUTSensorObj *)sensor);

	//Save sensor number in user field
	ms.instance->user[0] = m_sensors.size();

	//This function will attempt to connect to the device and initialize any variables.
	
	//You can set the size of the data field to any value.
	//After this function is called, Vizard will allocate the
	//data field of the plugin to the size given here. Then you
	//can put any values you want in the data field and the user
	//can get those values by calling the "get" command on the
	//sensor object in the script.
	//It is suggested that the size of the data field be 7 or higher
	ms.instance->dataSize = 13;

	//If you have multiple instances you can store your own unique
	//identifier in the user data field.

	//If initialization failed then set status to FALSE, if it succeeded set it to TRUE.
	if(movemeConnect("128.173.239.236","7899") == 0)
		ms.instance->status = TRUE;
	else
		ms.instance->status = FALSE;

	//Save object in global array
	m_sensors.push_back(ms);
}

void GetMoveData(int gem) {

	MoveStatus controllerStatus;
	MoveState controllerState;
	
	movemeGetState(gem,controllerState,controllerStatus);

	m_sensors[gem].instance->data[0] = controllerState.pos[0];
	m_sensors[gem].instance->data[1] = controllerState.pos[1];
	m_sensors[gem].instance->data[2] = controllerState.pos[2];

	m_sensors[gem].instance->data[3] = controllerState.quat[0];
	m_sensors[gem].instance->data[4] = controllerState.quat[1];
	m_sensors[gem].instance->data[5] = controllerState.quat[2];
	m_sensors[gem].instance->data[6] = controllerState.quat[3];

	m_sensors[gem].instance->data[7] = controllerState.handle_pos[0];
	m_sensors[gem].instance->data[8] = controllerState.handle_pos[1];
	m_sensors[gem].instance->data[9] = controllerState.handle_pos[2];

	m_sensors[gem].instance->data[10] = controllerState.pad.digital_buttons;
	m_sensors[gem].instance->data[11] = controllerState.pad.analog_trigger;

	m_sensors[gem].instance->data[12] = controllerState.camera_pitch_angle;
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

	//Update 'data' field of all sensors
	for(unsigned int i = 0; i < m_sensors.size(); ++i) {
		GetMoveData(i);
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

	strcpy(msg,(char *)((VRUTSensorObj *)sensor)->custom);

	float x,y,z;
	
	x = ((VRUTSensorObj *)sensor)->data[0];
	y = ((VRUTSensorObj *)sensor)->data[1];
	z = ((VRUTSensorObj *)sensor)->data[2];
	
	switch( (int) ((VRUTSensorObj *)sensor)->command) {
		case 1:
			movemeRumble(((VRUTSensorObj*)sensor)->user[0], (int)x);
			break;
		case 2:
			movemeTrackHues((int)((VRUTSensorObj *)sensor)->custom, (int)x, (int)y, (int)z);
			break;
		case 3:
			movemeForceRGB(((VRUTSensorObj*)sensor)->user[0], x,y,z);
			break;
		default:
			break;
	}
}

void CloseSensor(void *sensor)
{
	// Go ahead, clean up, and close files and COM ports.
	//Called only once no matter how many instances were created
	movemeDisconnect();
}