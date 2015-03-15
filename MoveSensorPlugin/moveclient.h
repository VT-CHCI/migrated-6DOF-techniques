#ifndef INC_MOVE_CLIENT_H
#define INC_MOVE_CLIENT_H

#ifdef __cplusplus
extern "C" {
#endif

#include <windows.h>

// Defines
#define MAX_UDP_MSG_SIZE (65535 - (20 + 8)) // Max size of UDP packet payload: 0xffff - (sizeof(IP Header) + sizeof(UDP Header))

#define IMAGE_BUFFER_SIZE (60 * 1024)
#define CAMERA_FRAME_SPLIT_FORMAT_JPG 0x1
#define MAX_CAMERA_FRAME_SLICES 8

#define MOVE_PACKET_MAGIC 0xff0000dd
#define MOVE_PACKET_CODE_STANDARD 0x1
#define MOVE_PACKET_CODE_CAMERA_FRAME_SLICE 0x2

#define MOVE_SERVER_MAX_GEMS 4
#define MOVE_SERVER_MAX_NAVS 7
#define MOVE_TRANSFER_TIMEOUT 20000  // microseconds
#define MOVE_CLIENT_OK 0
#define MOVE_CLIENT_ERROR -1
#define CELL_PAD_MAX_CODES 64

typedef enum MOVE_CLIENT_REQUESTS {
	MOVE_CLIENT_REQUEST_INIT = 0x0,
	MOVE_CLIENT_REQUEST_PAUSE = 0x1,
	MOVE_CLIENT_REQUEST_RESUME = 0x2,
	MOVE_CLIENT_REQUEST_DELAY_CHANGE = 0x3,  // payload is ms between packets
	MOVE_CLIENT_REQUEST_PREPARE_CAMERA = 0x4,  // payload is maximum exposure(int) and image_quality(float)

	MOVE_CLIENT_REQUEST_POINTER_SET_LEFT = 0x7,  // payload is gem number
	MOVE_CLIENT_REQUEST_POINTER_SET_RIGHT = 0x8,  // payload is gem number
	MOVE_CLIENT_REQUEST_POINTER_SET_BOTTOM = 0x9,  // payload is gem number
	MOVE_CLIENT_REQUEST_POINTER_SET_TOP = 0x10,  // payload is gem number
	MOVE_CLIENT_REQUEST_POINTER_ENABLE = 0x11,  // payload is gem number
	MOVE_CLIENT_REQUEST_POINTER_DISABLE = 0x12,  // payload is gem number
	MOVE_CLIENT_REQUEST_CONTROLLER_RESET = 0x13,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_SET_LEFT = 0x14,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_SET_RIGHT = 0x15,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_SET_BOTTOM = 0x16,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_SET_TOP = 0x17,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_ENABLE = 0x18,  // payload is gem number
	MOVE_CLIENT_REQUEST_POSITION_POINTER_DISABLE = 0x19,  // payload is gem number

	MOVE_CLIENT_REQUEST_FORCE_RGB = 0x20,  // payload is gem number followed by r,g,b floats
	MOVE_CLIENT_REQUEST_SET_RUMBLE = 0x21,  // payload is gem number followed by rumble value
	MOVE_CLIENT_REQUEST_TRACK_HUES = 0x22,  // payload is four hue track values

	MOVE_CLIENT_REQUEST_CAMERA_FRAME_DELAY_CHANGE = 0x23,  // acceptable delay: 16ms to 255 ms
	MOVE_CLIENT_REQUEST_CAMERA_FRAME_CONFIG_NUM_SLICES = 0x24,  // acceptable range: 1 to 8
	MOVE_CLIENT_REQUEST_CAMERA_FRAME_PAUSE = 0x25,
	MOVE_CLIENT_REQUEST_CAMERA_FRAME_RESUME = 0x26,

} MOVE_CLIENT_REQUESTS;

#ifndef ntohll
#define ntohll(x) (((unsigned __int64)(ntohl((unsigned __int32)x)) << 32) | (unsigned __int64)(ntohl((unsigned __int32)((unsigned __int64)x >> 32))))
#endif


// Type translations
typedef unsigned __int8 uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
typedef unsigned __int64 uint64_t;
typedef __int32 int32_t;
typedef __int64 system_time_t;
typedef float float4[4];


// Move structures
typedef struct _NavPadInfo {
	uint32_t port_status[MOVE_SERVER_MAX_NAVS];

} NavPadInfo, *LPNavPadInfo;

typedef struct _NavPadData {
	int32_t len;
	uint16_t button[CELL_PAD_MAX_CODES];

} NavPadData, *LPNavPadData;

typedef struct _MovePadData {
	uint16_t digital_buttons;
	uint16_t analog_trigger;

} MovePadData, *LPMovePadData;

typedef struct _MoveState {
	float4 pos;
	float4 vel;
	float4 accel;
	float4 quat;
	float4 angvel;
	float4 angaccel;
	float4 handle_pos;
	float4 handle_vel;
	float4 handle_accel;
	MovePadData pad;
	system_time_t timestamp;
	float temperature;
	float camera_pitch_angle;
	uint32_t tracking_flags;

} MoveState, *LPMoveState;

typedef struct _MoveImageState {
	system_time_t frame_timestamp; 
	system_time_t timestamp;
	float u;
	float v;
	float r;
	float projectionx;
	float projectiony;
	float distance;
	unsigned char visible;
	unsigned char r_valid;

} MoveImageState, *LPMoveImageState;

typedef struct _MoveSphereState {
	uint32_t tracking;
	uint32_t tracking_hue;
	float r;
	float g;
	float b;
	
} MoveSphereState, *LPMoveSphereState;

typedef struct _MoveCameraState {
	int32_t exposure;
	float exposure_time;
	float gain;
	float pitch_angle;
	float pitch_angle_estimate;
	
} MoveCameraState, *LPMoveCameraState;

typedef struct _MovePointerState
{
	uint32_t valid;
	float normalized_x;
	float normalized_y;

} MovePointerState, *LPMovePointerState;

typedef struct _MovePositionPointerState
{
	uint32_t valid;
	float normalized_x;
	float normalized_y;

} MovePositionPointerState, *LPMovePositionPointerState;


// Header structure
typedef struct _MoveServerPacketHeader
{
	uint32_t magic;
	uint32_t move_me_server_version;
	uint32_t packet_code;
	uint32_t packet_length;
	uint32_t packet_index;

} MoveServerPacketHeader, *LPMoveServerPacketHeader;


// Standard packet structures
typedef struct _MoveServerConfig
{
	int32_t num_image_slices;
	int32_t image_slice_format;

} MoveServerConfig, *LPMoveServerConfig;

typedef struct _MoveConnectionConfig
{
	uint32_t ms_delay_between_standard_packets;
	uint32_t ms_delay_between_camera_frame_packets;
	uint32_t camera_frame_packet_paused;

} MoveConnectionConfig, *LPMoveConnectionConfig;

typedef struct _MoveStatus
{
	uint32_t connected;
	uint32_t code;
	uint64_t flags;

} MoveStatus, *LPMoveStatus;

typedef struct _MoveServerPacket
{
	MoveServerPacketHeader header;
	MoveServerConfig server_config;
	MoveConnectionConfig client_config;
	MoveStatus status[MOVE_SERVER_MAX_GEMS];
	MoveState state[MOVE_SERVER_MAX_GEMS];
	MoveImageState image_state[MOVE_SERVER_MAX_GEMS];
	MovePointerState pointer_state[MOVE_SERVER_MAX_GEMS];
	NavPadInfo pad_info;
	NavPadData pad_data[MOVE_SERVER_MAX_NAVS];
	MoveSphereState sphere_state[MOVE_SERVER_MAX_GEMS];
	MoveCameraState camera_state;
	MovePositionPointerState position_pointer_state[MOVE_SERVER_MAX_GEMS];

} MoveServerPacket, *LPMoveServerPacket;


// Camera packet structure
typedef struct _MoveServerCameraFrameSlicePacket {
	MoveServerPacketHeader header;
	unsigned char slice_num;
	unsigned char num_slices;
	unsigned char format;
	unsigned char buffer[IMAGE_BUFFER_SIZE];

} MoveServerCameraFrameSlicePacket, *LPMoveServerCameraFrameSlicePacket;


// Request packet structures
typedef struct _MoveServerRequestPacketHeader
{
	uint32_t client_request;
	uint32_t payload_size;

} MoveServerRequestPacketHeader, *LPMoveServerRequestPacketHeader;

typedef struct _MoveServerRequestPacket
{
	MoveServerRequestPacketHeader header;
	uint32_t payload;

} MoveServerRequestPacket, *LPMoveServerRequestPacket;

typedef struct _MoveServerRequestPacketRumble
{
	MoveServerRequestPacketHeader header;
	uint32_t gem_num;
	uint32_t rumble;

} MoveServerRequestPacketRumble, *LPMoveServerRequestPacketRumble;

typedef struct _MoveServerRequestPacketForceRGB {
	MoveServerRequestPacketHeader header;
	uint32_t gem_num;
	float r;
	float g;
	float b;

} MoveServerRequestPacketForceRGB, *LPMoveServerRequestPacketForceRGB;

typedef struct _MoveServerRequestPacketTrackHues {
	MoveServerRequestPacketHeader header;
	uint32_t req_hue_gem_0;
	uint32_t req_hue_gem_1;
	uint32_t req_hue_gem_2;
	uint32_t req_hue_gem_3;

} MoveServerRequestPacketTrackHues, *LPMoveServerRequestPacketTrackHues;

typedef struct _MoveServerRequestPacketPrepareCamera {
	MoveServerRequestPacketHeader header;
	uint32_t max_exposure;
	float image_quality;

} MoveServerRequestPacketPrepareCamera, *LPMoveServerRequestPacketPrepareCamera;


// Prototypes

int movemeConnect(PCSTR lpRemoteAddress, PCSTR lpPort);
int movemeDisconnect(void);
void movemeGetState(const int whichGem, MoveState &myMoveState, MoveStatus &myMoveStatus);
int movemePause(void);
int movemeResume(void);
int movemePauseCamera(void);
int movemeResumeCamera(void);
int movemeUpdateFrequency(uint32_t frequency);
int movemeUpdateCameraFrequency(uint32_t frequency);
int movemeRumble(uint32_t gem_num, uint32_t rumble);
int movemeForceRGB(uint32_t gem_num, float r, float g, float b);
int movemeTrackHues(uint32_t req_hue_gem_0, uint32_t req_hue_gem_1, uint32_t req_hue_gem_2, uint32_t req_hue_gem_3);
int movemePrepareCamera(uint32_t max_exposure, float image_quality);
int movemeCameraSetNumSlices(uint32_t slices);

#ifdef __cplusplus
}
#endif

#endif  // ... INC_MOVE_CLIENT_H
