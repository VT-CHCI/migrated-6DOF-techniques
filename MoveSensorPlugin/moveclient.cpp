// Authors: Kenny Hoff and Mike Taylor

#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "moveclient.h"

static MoveServerPacket myMoveServerPacket;
static MoveServerCameraFrameSlicePacket myMoveServerCameraFrameSlicePacket;
CRITICAL_SECTION myMoveStateCriticalSection;

static int sendRequestPacket(uint32_t, uint32_t);
static int sendRequestPacketRumble(uint32_t, uint32_t);
static int sendRequestPacketForceRGB(uint32_t, float, float, float);
static int sendRequestPacketTrackHues(uint32_t, uint32_t, uint32_t, uint32_t);
static int sendRequestPacketPrepareCamera(uint32_t, float);

static void deserializeMoveServerPacketHeader(LPMoveServerPacketHeader);
static void deserializeMoveServerPacket(LPMoveServerPacket);

// Locals
SOCKET sControlSocket = INVALID_SOCKET;
SOCKET sTransferSocket = INVALID_SOCKET;
HANDLE shUpdateMoveState;
fd_set sfd_read, sfd_except;
BOOL sConnected = FALSE;
BOOL sTransferring = FALSE;

#define PACKET_PREP(_s, _cr) \
  _s packet_data; \
  int packet_size = sizeof(packet_data); \
  int payload_size = packet_size - sizeof(packet_data.header); \
  /* Setup header */ setupHeader(&packet_data.header, _cr, payload_size);


// Local functions
static __inline void setupHeader(LPMoveServerRequestPacketHeader header, uint32_t client_request, uint32_t payload_size)
{
  header->client_request = htonl(client_request);
  header->payload_size = htonl(payload_size);
}

// Host to network float
static float htonf(float f)
{
  uint32_t tmpInt = *(uint32_t *)&f;
  tmpInt = htonl(tmpInt);
  f = *(float *)&tmpInt;
  return f;
}

// Network to host float
static float ntohf(float f)
{
  uint32_t tmpInt = *(uint32_t *)&f;
  tmpInt = ntohl(tmpInt);
  f = *(float *)&tmpInt;
  return f;
}

static __inline int sendData(uint8_t *data_pointer, uint32_t data_size)
{
  while (0 < data_size) {
	int bytes = send(sControlSocket, (const char*)data_pointer, data_size, 0);

    if (0 > bytes) {
      break;
    }

    data_pointer += bytes;
    data_size -= bytes;
  }

  return WSAGetLastError();
}

static int sendRequestPacket(uint32_t client_request, uint32_t payload)
{
  PACKET_PREP(MoveServerRequestPacket, client_request);

  // Serialize data
  packet_data.payload = htonl(payload);

  // Send
  return sendData((uint8_t *) &packet_data, packet_size);
}


static int sendRequestPacketRumble(uint32_t gem_num, uint32_t rumble)
{
  PACKET_PREP(MoveServerRequestPacketRumble, MOVE_CLIENT_REQUEST_SET_RUMBLE);

  // Serialize data
  packet_data.gem_num = htonl(gem_num);
  packet_data.rumble = htonl(rumble);

  // Send
  return sendData((uint8_t *) &packet_data, packet_size);
}


static int sendRequestPacketForceRGB(uint32_t gem_num, float r, float g, float b)
{
  PACKET_PREP(MoveServerRequestPacketForceRGB, MOVE_CLIENT_REQUEST_FORCE_RGB);

  // Serialize data
  packet_data.gem_num = htonl(gem_num);
  packet_data.r = htonf(r);
  packet_data.g = htonf(g);
  packet_data.b = htonf(b);

  // Send
  return sendData((uint8_t *) &packet_data, packet_size);
}


static int sendRequestPacketTrackHues(uint32_t req_hue_gem_0, uint32_t req_hue_gem_1, uint32_t req_hue_gem_2, uint32_t req_hue_gem_3)
{
  PACKET_PREP(MoveServerRequestPacketTrackHues, MOVE_CLIENT_REQUEST_TRACK_HUES);

  // Serialize data
  packet_data.req_hue_gem_0 = htonl(req_hue_gem_0);
  packet_data.req_hue_gem_1 = htonl(req_hue_gem_1);
  packet_data.req_hue_gem_2 = htonl(req_hue_gem_2);
  packet_data.req_hue_gem_3 = htonl(req_hue_gem_3);

  // Send
  return sendData((uint8_t *) &packet_data, packet_size);
}


static int sendRequestPacketPrepareCamera(uint32_t max_exposure, float image_quality)
{
  PACKET_PREP(MoveServerRequestPacketPrepareCamera, MOVE_CLIENT_REQUEST_PREPARE_CAMERA);

  // Serialize data
  packet_data.max_exposure = htonl(max_exposure);
  packet_data.image_quality = htonf(image_quality);

  // Send
  return sendData((uint8_t *) &packet_data, packet_size);
}

#undef PACKET_PREP


// Deserialize the move server packet header
void deserializeMoveServerPacketHeader(LPMoveServerPacketHeader lpMoveServerPacketHeader)
{
  lpMoveServerPacketHeader->magic = ntohl(lpMoveServerPacketHeader->magic);
  lpMoveServerPacketHeader->move_me_server_version = ntohl(lpMoveServerPacketHeader->move_me_server_version);
  lpMoveServerPacketHeader->packet_code = ntohl(lpMoveServerPacketHeader->packet_code);
  lpMoveServerPacketHeader->packet_index = ntohl(lpMoveServerPacketHeader->packet_index);
  lpMoveServerPacketHeader->packet_length = ntohl(lpMoveServerPacketHeader->packet_length);
}


// Deserialize the move server packet
void deserializeMoveServerPacket(LPMoveServerPacket lpMoveServerPacket)
{
  int i, j;

  // Server Config
  lpMoveServerPacket->server_config.num_image_slices = ntohl(lpMoveServerPacket->server_config.num_image_slices);
  lpMoveServerPacket->server_config.image_slice_format = ntohl(lpMoveServerPacket->server_config.image_slice_format);

  // Connection Config
  lpMoveServerPacket->client_config.ms_delay_between_standard_packets = ntohl(lpMoveServerPacket->client_config.ms_delay_between_standard_packets);
  lpMoveServerPacket->client_config.ms_delay_between_camera_frame_packets = ntohl(lpMoveServerPacket->client_config.ms_delay_between_camera_frame_packets);
  lpMoveServerPacket->client_config.camera_frame_packet_paused = ntohl(lpMoveServerPacket->client_config.camera_frame_packet_paused);

  // Camera
  lpMoveServerPacket->camera_state.exposure = ntohl(lpMoveServerPacket->camera_state.exposure);
  lpMoveServerPacket->camera_state.exposure_time = ntohf(lpMoveServerPacket->camera_state.exposure_time);
  lpMoveServerPacket->camera_state.gain = ntohf(lpMoveServerPacket->camera_state.gain);
  lpMoveServerPacket->camera_state.pitch_angle = ntohf(lpMoveServerPacket->camera_state.pitch_angle);
  lpMoveServerPacket->camera_state.pitch_angle_estimate = ntohf(lpMoveServerPacket->camera_state.pitch_angle_estimate);

  // Nav
  for (i = 0; i < MOVE_SERVER_MAX_NAVS; i++) {
    lpMoveServerPacket->pad_info.port_status[i] = ntohl(lpMoveServerPacket->pad_info.port_status[i]);

    // NavPadData
    lpMoveServerPacket->pad_data[i].len = ntohl(lpMoveServerPacket->pad_data[i].len);

    for (j = 0; j < CELL_PAD_MAX_CODES; j++) {
      lpMoveServerPacket->pad_data[i].button[j] = ntohs(lpMoveServerPacket->pad_data[i].button[j]);
    }
  }

  // Gems
  for (i = 0; i < MOVE_SERVER_MAX_GEMS; i++) {

    // Status
    lpMoveServerPacket->status[i].connected = ntohl(lpMoveServerPacket->status[i].connected);
    lpMoveServerPacket->status[i].code = ntohl(lpMoveServerPacket->status[i].code);
    lpMoveServerPacket->status[i].flags = ntohll(lpMoveServerPacket->status[i].flags);

    if (lpMoveServerPacket->status[i].connected == 1) {

      // State
      for (j = 0; j < 4; j++) {
        lpMoveServerPacket->state[i].pos[j] = ntohf(lpMoveServerPacket->state[i].pos[j]);
        lpMoveServerPacket->state[i].vel[j] = ntohf(lpMoveServerPacket->state[i].vel[j]);
        lpMoveServerPacket->state[i].accel[j] = ntohf(lpMoveServerPacket->state[i].accel[j]);
        lpMoveServerPacket->state[i].quat[j] = ntohf(lpMoveServerPacket->state[i].quat[j]);
        lpMoveServerPacket->state[i].angvel[j] = ntohf(lpMoveServerPacket->state[i].angvel[j]);
        lpMoveServerPacket->state[i].angaccel[j] = ntohf(lpMoveServerPacket->state[i].angaccel[j]);
        lpMoveServerPacket->state[i].handle_pos[j] = ntohf(lpMoveServerPacket->state[i].handle_pos[j]);
        lpMoveServerPacket->state[i].handle_vel[j] = ntohf(lpMoveServerPacket->state[i].handle_vel[j]);
        lpMoveServerPacket->state[i].handle_accel[j] = ntohf(lpMoveServerPacket->state[i].handle_accel[j]);
      }

      lpMoveServerPacket->state[i].timestamp = (system_time_t)ntohll((uint64_t)lpMoveServerPacket->state[i].timestamp);
      lpMoveServerPacket->state[i].temperature = ntohf(lpMoveServerPacket->state[i].temperature);
      lpMoveServerPacket->state[i].camera_pitch_angle = ntohf(lpMoveServerPacket->state[i].camera_pitch_angle);
      lpMoveServerPacket->state[i].tracking_flags = ntohl(lpMoveServerPacket->state[i].tracking_flags);

      // Pad
      lpMoveServerPacket->state[i].pad.digital_buttons = ntohs(lpMoveServerPacket->state[i].pad.digital_buttons);
      lpMoveServerPacket->state[i].pad.analog_trigger = ntohs(lpMoveServerPacket->state[i].pad.analog_trigger);

      // Image State
      lpMoveServerPacket->image_state[i].frame_timestamp = (system_time_t)ntohll((uint64_t)lpMoveServerPacket->image_state[i].frame_timestamp);
      lpMoveServerPacket->image_state[i].timestamp = (system_time_t)ntohll((uint64_t)lpMoveServerPacket->image_state[i].timestamp);
      lpMoveServerPacket->image_state[i].u = ntohf(lpMoveServerPacket->image_state[i].u);
      lpMoveServerPacket->image_state[i].v = ntohf(lpMoveServerPacket->image_state[i].v);
      lpMoveServerPacket->image_state[i].r = ntohf(lpMoveServerPacket->image_state[i].r);
      lpMoveServerPacket->image_state[i].projectionx = ntohf(lpMoveServerPacket->image_state[i].projectionx);
      lpMoveServerPacket->image_state[i].projectiony = ntohf(lpMoveServerPacket->image_state[i].projectiony);
      lpMoveServerPacket->image_state[i].distance = ntohf(lpMoveServerPacket->image_state[i].distance);

      // Sphere State
      lpMoveServerPacket->sphere_state[i].tracking = ntohl(lpMoveServerPacket->sphere_state[i].tracking);
      lpMoveServerPacket->sphere_state[i].tracking_hue = ntohl(lpMoveServerPacket->sphere_state[i].tracking_hue);
      lpMoveServerPacket->sphere_state[i].r = ntohf(lpMoveServerPacket->sphere_state[i].r);
      lpMoveServerPacket->sphere_state[i].g = ntohf(lpMoveServerPacket->sphere_state[i].g);
      lpMoveServerPacket->sphere_state[i].b = ntohf(lpMoveServerPacket->sphere_state[i].b);

      // Pointer State
      lpMoveServerPacket->pointer_state[i].valid = ntohl(lpMoveServerPacket->pointer_state[i].valid);
      lpMoveServerPacket->pointer_state[i].normalized_x = ntohf(lpMoveServerPacket->pointer_state[i].normalized_x);
      lpMoveServerPacket->pointer_state[i].normalized_y = ntohf(lpMoveServerPacket->pointer_state[i].normalized_y);

      // Position Pointer State
      lpMoveServerPacket->position_pointer_state[i].valid = ntohl(lpMoveServerPacket->position_pointer_state[i].valid);
      lpMoveServerPacket->position_pointer_state[i].normalized_x = ntohf(lpMoveServerPacket->position_pointer_state[i].normalized_x);
      lpMoveServerPacket->position_pointer_state[i].normalized_y = ntohf(lpMoveServerPacket->position_pointer_state[i].normalized_y);
    }
  }
}

// Recv from PS3
DWORD WINAPI UpdateMoveState(LPVOID)
{
  int returnCode, lastError, bytes;
  fd_set fd_read, fd_except;
  uint64_t buffer[MAX_UDP_MSG_SIZE / sizeof(uint64_t)];
  int header_packet_size = sizeof(MoveServerPacketHeader);
  int packet_size = sizeof(MoveServerPacket);
  int cameraPacketSize = sizeof(MoveServerCameraFrameSlicePacket);

  TIMEVAL timeout;

  // Set timeout
  memset((void *) &timeout, 0, sizeof(timeout)); 
  timeout.tv_usec = MOVE_TRANSFER_TIMEOUT;

  // Update loop
  while (sTransferring) {

    // Setup file_descriptors
    memcpy(&fd_read, &sfd_read, sizeof(fd_read));
    memcpy(&fd_except, &sfd_except, sizeof(fd_except));

    // Select
    returnCode = select(0, &fd_read, NULL, &fd_except, &timeout);

    if (0 < returnCode) {  // Check file descriptors

      if (FD_ISSET(sTransferSocket, &fd_read)) {
        bytes = recvfrom(sTransferSocket, (char *)buffer, MAX_UDP_MSG_SIZE, 0, 0, 0);

        if (bytes == SOCKET_ERROR) {  // Recv error occurred
          lastError = WSAGetLastError();

          if (lastError != WSAEWOULDBLOCK && sTransferring) {  // Ignore would-block
            printf("SOCKET ERROR: recvfrom() returned error #%d\n", lastError);

          }

        } else {
	      EnterCriticalSection(&myMoveStateCriticalSection);

          // Get pointer to header in the buffer
		      LPMoveServerPacketHeader lpMoveServerPacketHeader = (LPMoveServerPacketHeader) &buffer[0];

          // Deserialize header
          deserializeMoveServerPacketHeader(lpMoveServerPacketHeader);

          if (lpMoveServerPacketHeader->packet_code == MOVE_PACKET_CODE_STANDARD) {
            memcpy_s(&myMoveServerPacket, packet_size, (void *)lpMoveServerPacketHeader, packet_size);

            // Deserialize packet
            deserializeMoveServerPacket(&myMoveServerPacket);

          }else if (lpMoveServerPacketHeader->packet_code == MOVE_PACKET_CODE_CAMERA_FRAME_SLICE) {
            memcpy_s(&myMoveServerCameraFrameSlicePacket, cameraPacketSize, (void *)lpMoveServerPacketHeader, cameraPacketSize);

          }

        LeaveCriticalSection(&myMoveStateCriticalSection);
        }

        // Cleanup set
        FD_CLR(sTransferSocket, &fd_read);

      }

      if (FD_ISSET(sTransferSocket, &fd_except)) {

        if (sTransferring) {
          printf("SOCKET ERROR: select() set FD_EXCEPT with error #%d\n", WSAGetLastError());

        }

        // Cleanup set
        FD_CLR(sTransferSocket, &fd_except);

      }

    }
    else if (0 > returnCode) {  // Select error occurred

      if (sTransferring) {
        printf("SOCKET ERROR: select() returned error #%d\n", WSAGetLastError());

      }

    }

  }

  return MOVE_CLIENT_OK;
}

static int stopTransfer(void)
{
  if (!sTransferring) {
    return MOVE_CLIENT_OK;
  }

  // Update internal state
  sTransferring = FALSE;

  // Wait for the thread to finish
  WaitForSingleObject(shUpdateMoveState, INFINITE);

  // Cleanup the thread handle
  CloseHandle(shUpdateMoveState);

  return GetLastError();
}

static int startTransfer(void)
{
  if (sTransferring) {
    return MOVE_CLIENT_OK;
  }

  // Update state
  sTransferring = TRUE;

  // Run update loop in a separate thread
  if ((shUpdateMoveState = CreateThread(NULL, 0, &UpdateMoveState, 0, 0, NULL)) == NULL) {
    stopTransfer();
    return MOVE_CLIENT_ERROR;

  }

  return MOVE_CLIENT_OK;
}

///////////////////
// Public functions
///////////////////

// PS3 Connect
int movemeConnect(PCSTR lpRemoteAddress, PCSTR lpPort)
{
  WSADATA wsaData;
  INT rc, tsa_len, lastError, udpBufferSize;
  SOCKADDR_IN service, transfer;
  ULONG nonBlock = 1;
  struct addrinfo *result = NULL, *ptr = NULL, hints;
  char remoteAddress[100], port[6];
  tsa_len = sizeof(transfer);
  udpBufferSize = 512 * 1024;

  if (sConnected) {
    return MOVE_CLIENT_OK;

  }

  InitializeCriticalSection(&myMoveStateCriticalSection);

  // Initialize Winsock
  if (WSAStartup(MAKEWORD(2, 2), &wsaData)) {
    return WSAGetLastError();

  }

  ZeroMemory(&hints, sizeof(hints));
  hints.ai_family = AF_UNSPEC;
  hints.ai_socktype = SOCK_STREAM;
  hints.ai_protocol = IPPROTO_TCP;

  service.sin_family = AF_INET;
  service.sin_port = 0;
  service.sin_addr.s_addr = htonl(INADDR_ANY);
  memset(service.sin_zero, '\0', sizeof(service.sin_zero));

  strncpy_s(remoteAddress, _countof(remoteAddress), lpRemoteAddress, _countof(remoteAddress) - 1);
  strncpy_s(port, _countof(port), lpPort, _countof(port) - 1);

  if (getaddrinfo(remoteAddress, port, &hints, &result)) {
    return WSAGetLastError();

  }

  // Create transfer socket
  if ((sTransferSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == INVALID_SOCKET) {
    lastError = WSAGetLastError();
    freeaddrinfo(result);
    WSACleanup();
    return lastError;

  }

  // Attempt to connect to an address until one succeeds
  for (ptr = result; ptr != NULL; ptr = ptr->ai_next) {

    if ((sControlSocket = socket(ptr->ai_family, ptr->ai_socktype, ptr->ai_protocol)) == INVALID_SOCKET) {
      freeaddrinfo(result);
      return WSAGetLastError();

    }

    // Connect to server
    if (connect(sControlSocket, ptr->ai_addr, (int)ptr->ai_addrlen) == SOCKET_ERROR) {
      closesocket(sControlSocket);
      sControlSocket = INVALID_SOCKET;
      continue;

    }
    break;

  }

  freeaddrinfo(result);

  if (sControlSocket == INVALID_SOCKET) {
    lastError = WSAGetLastError();
    closesocket(sTransferSocket);
    WSACleanup();
    return lastError;

  }

  // Update internal state after all sockets successfully created
  sConnected = TRUE;

  // Initialize socket file descriptors for select
  FD_ZERO(&sfd_read);
  FD_ZERO(&sfd_except);
  FD_SET(sTransferSocket, &sfd_read);
  FD_SET(sTransferSocket, &sfd_except);

  // Bind transfer Socket
  if (bind(sTransferSocket, (SOCKADDR *)&service, sizeof(service)) == INVALID_SOCKET) {
    lastError = WSAGetLastError();
    movemeDisconnect();
    return lastError;

  }


  // Change transfer socket mode to non-blocking
  if (ioctlsocket(sTransferSocket, FIONBIO, &nonBlock) == SOCKET_ERROR) {
    lastError = WSAGetLastError();
    movemeDisconnect();
    return lastError;

  }

  // Increase UDP buffer size
  if (setsockopt(sTransferSocket, SOL_SOCKET, SO_RCVBUF, (char *)&udpBufferSize, sizeof(udpBufferSize)) == SOCKET_ERROR) {
    lastError = WSAGetLastError();
    movemeDisconnect();
    return lastError;

  }

  // Get transfer socket port
  if (getsockname(sTransferSocket, (SOCKADDR *)&transfer, &tsa_len)) {
    lastError = WSAGetLastError();
    movemeDisconnect();
    return lastError;

  }

  // Start UpdateMoveServer thread
  if (rc = startTransfer()) {
    movemeDisconnect();
    return rc;

  }

  // Send initialization request
  if (rc = sendRequestPacket(MOVE_CLIENT_REQUEST_INIT, ntohs(transfer.sin_port))) {
    movemeDisconnect();
    return rc;

  }

  return MOVE_CLIENT_OK;
}

// PS3 Disconnect
int movemeDisconnect()
{

  if (!sConnected) {
    return MOVE_CLIENT_OK;
  }

  // Update internal state
  sConnected = FALSE;

  // Cleanup critical section
  DeleteCriticalSection(&myMoveStateCriticalSection);

  // Stop UpdateMoveState thread
  if (sTransferring) {
    stopTransfer();
  }

  // Clear file descriptor
  FD_CLR(sTransferSocket, &sfd_read);
  FD_CLR(sTransferSocket, &sfd_except);

  // Best effort attempt to cleanly close tranfer socket	
  closesocket(sTransferSocket);

  // Best effort attempt to cleanly close control socket
  shutdown(sControlSocket, SD_BOTH);
  closesocket(sControlSocket);

  // Windows socket cleanup
  WSACleanup();

  return WSAGetLastError();

}

// Copy local client move state into app's copy
void movemeGetState(const int whichGem, MoveState &myMoveState, MoveStatus &myMoveStatus)
{
	EnterCriticalSection(&myMoveStateCriticalSection);
	myMoveStatus = myMoveServerPacket.status[whichGem];
	myMoveState  = myMoveServerPacket.state[whichGem];
	LeaveCriticalSection(&myMoveStateCriticalSection);
}

int movemePause(void)
{
  if (!sConnected || !sTransferring) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_PAUSE, 0);
}

int movemeResume(void)
{
  if (!sConnected || !sTransferring) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_RESUME, 0);
}

int movemePauseCamera(void)
{
  if (!sConnected || !sTransferring) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_CAMERA_FRAME_PAUSE, 0);
}

int movemeResumeCamera(void)
{
  if (!sConnected || !sTransferring) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_CAMERA_FRAME_RESUME, 0);
}

int movemeUpdateFrequency(uint32_t frequency)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_DELAY_CHANGE, frequency);
}

int movemeUpdateCameraFrequency(uint32_t frequency)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_CAMERA_FRAME_DELAY_CHANGE, frequency);
}

int movemeRumble(uint32_t gem_num, uint32_t rumble)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacketRumble(gem_num, rumble);
}

int movemeForceRGB(uint32_t gem_num, float r, float g, float b)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacketForceRGB(gem_num, r, g, b);
}

int movemeTrackHues(uint32_t req_hue_gem_0, uint32_t req_hue_gem_1, uint32_t req_hue_gem_2, uint32_t req_hue_gem_3)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacketTrackHues(req_hue_gem_0, req_hue_gem_1, req_hue_gem_2, req_hue_gem_3);
}

int movemePrepareCamera(uint32_t max_exposure, float image_quality)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacketPrepareCamera(max_exposure, image_quality);
}

int movemeCameraSetNumSlices(uint32_t slices)
{
  if (!sConnected) {
    return MOVE_CLIENT_ERROR;
  }

  return sendRequestPacket(MOVE_CLIENT_REQUEST_CAMERA_FRAME_CONFIG_NUM_SLICES, slices);
}
