APPLY                   	= C = 0
CANCEL                  	= C = C + 1

CONNECT_DEVICE          	= C = C + 1
DISCONNECT_DEVICE       	= C = C + 1

DEVICE_CONNECTING       	= C = C + 1
DEVICE_CONNECTED        	= C = C + 1
DEVICE_DISCONNECTING    	= C = C + 1
DEVICE_DISCONNECTED     	= C = C + 1
DEVICE_NOT_FOUND        	= C = C + 1

RUN_MODE                	= C = C + 1
RUN_MODE_MONITOR        	= C = C + 1
RUN_MODE_ISOTHERMAL     	= C = C + 1
RUN_MODE_LINEAR_RAMP    	= C = C + 1
RUN_MODE_STEPPED_RAMP   	= C = C + 1

START_RUN               	= C = C + 1
FINISH_RUN              	= C = C + 1

RUN_STARTING            	= C = C + 1
RUN_STARTED             	= C = C + 1
RUN_FINISHING           	= C = C + 1
RUN_FINISHED            	= C = C + 1

OPEN_DIALOG             	= C = C + 1
ISOTHERMAL_DIALOG       	= C = C + 1
LINEAR_RAMP_DIALOG      	= C = C + 1
STEP_TABLE_DIALOG       	= C = C + 1
PID_SETTINGS_DIALOG     	= C = C + 1
CALIBRATION_DIALOG			= C = C + 1
SAVE_CALIBRATION			= C = C + 1
LOAD_CALIBRATION			= C = C + 1
LOAD_DEFAULT_CALIBRATION	= C = C + 1
HTR_PT100_CALIBRATION		= C = C + 1
CJ_PT100_CALIBRATION		= C = C + 1
TC_GAIN_CALIB_0				= C = C + 1
TC_GAIN_CALIB_499			= C = C + 1

OPEN_METHOD             	= C = C + 1
SAVE_METHOD             	= C = C + 1

OPEN_DEVICE                 = C = C + 1
CRYOSTAT_DEVICE             = C = C + 1

# ++++ TCON driver constants ++++

BAUDRATE                         = 9600
VALID_CMD                        = 'D'

# ++++ TCON parameters ++++

TOTAL_SENSORS 					 = 3
RTD_SESNORS 					 = 2
TC_SENSORS 						 = 1

# ++++ TCON sensors ++++

SENSOR_RTD1                      = C = 0
SENSOR_RTD2                      = C = C + 1
SENSOR_TC1                       = C = C + 1

# ++++ TCON run modes ++++

TCON_RUN_MODE_IDLE				 = C = 0
TCON_RUN_MODE_ISOTHERMAL		 = C = C + 1
TCON_RUN_MODE_LINEAR_RAMP		 = C = C + 1

# ++++ Datatype constants ++++

DATASET_COL_TIME                         = C = 0
DATASET_COL_SAMPLE_TEMPERATURE           = C = C + 1
DATASET_COL_HEATER_TEMPERATURE           = C = C + 1
DATASET_COL_CJ_TEMPERATURE               = C = C + 1
DATASET_COL_HEATER_SETPOINT              = C = C + 1
DATASET_COL_HEATER_POWER                 = C = C + 1


DEFAULT_P      = 0.5
DEFAULT_I      = 0.004
DEFAULT_D      = 1.0
DEFAULT_IRANGE = 3.0

DEFAULT_CTRL_SENSOR = SENSOR_RTD1

DEFAULT_PT100_R		= 100.0 #Ohms
DEFAULT_TC_VOLTAGE	= 4.99  #mV


# ++++ Stepped ramp state ++++

STEP_STATE_IDLE            = C = 0
STEP_STATE_PREDELAY        = C = C + 1
STEP_STATE_CHECK_STABILITY = C = C + 1
STEP_STATE_POSTDELAY       = C = C + 1
STEP_STATE_STABLE          = C = C + 1
STEP_STATE_FINISHED        = C = C + 1

# ++++ Communication timeout ++++

COMM_TIMEOUT_INTERVAL = 5.0
