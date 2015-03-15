#ifndef _SENSOR_H_
#define _SENSOR_H_

#define MAX_SENSOR_NAME			32
#define MAX_SENSOR_DATA			10
#define MAX_USER_DATA			3

#define SENSOR_POS_X			0
#define SENSOR_POS_Y			1
#define SENSOR_POS_Z			2
#define SENSOR_ORI_YAW			3
#define SENSOR_ORI_PITCH		4
#define SENSOR_ORI_ROLL			5
#define SENSOR_ORI_QX			3
#define SENSOR_ORI_QY			4
#define SENSOR_ORI_QZ			5
#define SENSOR_ORI_QW			6

// Sensor types:
#define SENSOR_SERIALJOY		1
#define SENSOR_MOUSE			2
#define SENSOR_HEADPOS			4		// must equal VIZ_HEAD_POS
#define SENSOR_HEADORI			8		// must equal VIZ_HEAD_ORI
#define SENSOR_BODYORI			16		// must equal VIZ_BODY_ORI
#define SENSOR_EULER1			32
#define SENSOR_EULER2			64
#define SENSOR_QUATERNION		128
#define SENSOR_RAW				256
#define SENSOR_MULTI			512
#define SENSOR_TEXGEN			1024
#define SENSOR_ENGINE			2048
#define SENSOR_STRING_CUSTOM	4096


// All types available for automatic eyepoint tracking
#define SENSOR_TRACKER_MASK			(SENSOR_HEADPOS + SENSOR_HEADORI + SENSOR_BODYORI)

#define SENSOR_POSITION_MASK		(SENSOR_HEADPOS)
#define SENSOR_ORIENTATION_MASK		(SENSOR_EULER1 + SENSOR_EULER2 + SENSOR_QUATERNION)


typedef char (PLUGIN_PROC)(void *);

typedef struct VRUTSensorObj {
	char			name[MAX_SENSOR_NAME];
	char			status;
	int				type;
	float			*data;
	short			user[MAX_USER_DATA];

	PLUGIN_PROC		*queryProc;
	PLUGIN_PROC		*initProc;
	PLUGIN_PROC		*updateProc;
	PLUGIN_PROC		*resetProc;
	PLUGIN_PROC		*closeProc;
	PLUGIN_PROC		*commandProc;

	char			version[MAX_SENSOR_NAME];
	void			*custom;
	void			*xf;
	float			command;
	int				dataSize;

    /* The transform pointer should only be initialized if we want to
	   have VRUT automatically contruct a 4x4 matrix every frame.  If 
	   it's NULL, then we won't do this step.  When it is being used,
	   others can link to it and use the information.  For example, a
	   geometry node can take this csTransform pointer and insert it 
	   after it's original transform so that the sensor will affect an
	   object.  Using this method, there's no cost to attaching the 
	   sensor to one or more objects.
	*/

} VRUTSensorObj;

#endif //_SENSOR_H_