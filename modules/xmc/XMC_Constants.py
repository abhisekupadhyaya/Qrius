APPLY                   	= C = 0
ENTER	                  	= C = C + 1
CANCEL                  	= C = C + 1

CONNECT_DEVICE          	= C = C + 1
DISCONNECT_DEVICE       	= C = C + 1
RUN_MODE                	= C = C + 1
START_RUN               	= C = C + 1
FINISH_RUN              	= C = C + 1
RESET_DEVICE				= C = C + 1
STOP_DEVICE                 = C = C + 1
OPEN_DIALOG             	= C = C + 1

DEVICE_CONNECTING       	= C = C + 1
DEVICE_CONNECTED        	= C = C + 1
DEVICE_DISCONNECTING    	= C = C + 1
DEVICE_DISCONNECTED     	= C = C + 1
DEVICE_NOT_FOUND        	= C = C + 1
DEVICE_RESET	        	= C = C + 1
DEVICE_MOVING               = C = C + 1
DEVICE_PITCH_SET            = C = C + 1
DEVICE_STOPPED              = C = C + 1
DEVICE_STATUS	        	= C = C + 1

RUN_STARTING            	= C = C + 1
RUN_STARTED             	= C = C + 1
RUN_FINISHING           	= C = C + 1
RUN_FINISHED            	= C = C + 1

RUN_MODE_MONITOR        	= C = C + 1

PITCH_SETTING_DIALOG 	  	= C = C + 1
MOVE_ABSOLUTE_DIALOG   	    = C = C + 1
MOVE_RELATIVE_DIALOG     	= C = C + 1

COMM_TIMEOUT_INTERVAL = 1.0

MC_STATE_IDLE          = C = 0
MC_STATE_RESET         = C = C + 1
MC_STATE_MOVE_UP       = C = C + 1
MC_STATE_MOVE_DOWN     = C = C + 1

# ++++ Datatype constants ++++

DATASET_COL_TIME                         = C = 0
DATASET_COL_POSITION                     = C = C + 1

# ++++ Instrument specification +++

STEPS_PER_ROTATION = 400

# Conversions

mm_to_m                           = 1e-3
m_to_mm                           = 1e3
