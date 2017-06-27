RUN_MODE                    = C = 0
RUN_MODE_HTime              = C = C + 1
RUN_MODE_ITime              = C = C + 1
RUN_MODE_VTime              = C = C + 1

CONNECT_DEVICE              = C = C + 1
DISCONNECT_DEVICE           = C = C + 1

DEVICE_CONNECTING           = C = C + 1
DEVICE_CONNECTED            = C = C + 1
DEVICE_DISCONNECTING        = C = C + 1
DEVICE_DISCONNECTED         = C = C + 1
DEVICE_NOT_FOUND            = C = C + 1

CM_RANGE_CHANGED            = C = C + 1
VM_RANGE_CHANGED            = C = C + 1
HM_RANGE_CHANGED            = C = C + 1
SOURCE_PARAMETERS_CHANGED   = C = C + 1

START_RUN                   = C = C + 1
FINISH_RUN                  = C = C + 1

RUN_STARTING                = C = C + 1
RUN_STARTED                 = C = C + 1
RUN_FINISHING               = C = C + 1
RUN_FINISHED                = C = C + 1

OPEN_DIALOG                 = C = C + 1
SOURCE_PARAMETERS_DIALOG    = C = C + 1
METER_SETTINGS_DIALOG       = C = C + 1
ACQUISITION_SETTINGS_DIALOG = C = C + 1

APPLY                       = C = C + 1
CANCEL                      = C = C + 1

OPEN_METHOD                 = C = C + 1
SAVE_METHOD                 = C = C + 1

UPLOAD_CALIBRATION          = C = C + 1

CS_DEACTIVATE               = C = 0
CS_ACTIVATE                 = C = C + 1

# src_mode
SOURCE_MODE_HS              = C = 0
SOURCE_MODE_CS              = C = C + 1

# src autorange
AUTORANGE_ON                = True
AUTORANGE_OFF               = True

# hs_range
HS_RANGE_1              	= C = 0
HS_RANGE_MIN                = HS_RANGE_1
HS_RANGE_MAX                = HS_RANGE_1
HS_RANGES                   = [1000]

# cs_range
CS_RANGE_1                  = C = 0
CS_RANGE_MIN                = CS_RANGE_1
CS_RANGE_MAX                = CS_RANGE_1
CS_RANGES                   = [6.0]

# hm_range
HM_RANGE_1                  = C = 0
HM_RANGE_MAX                = HM_RANGE_1
HM_RANGE_MIN                = HM_RANGE_1
HM_RANGES                   = [1000]

# cm_range
CM_RANGE_1                  = C = 0
CM_RANGE_MIN                = CM_RANGE_1
CM_RANGE_MAX                = CM_RANGE_1
CM_RANGES                   = [6.0]

# vm_range
VM_RANGE_1                  = C = 0
VM_RANGE_MIN                = VM_RANGE_1
VM_RANGE_MAX                = VM_RANGE_1
VM_RANGES                   = [20.0]

COMM_TIMEOUT_INTERVAL       = 5.0

DATASET_COL_TIME            = C = 0
DATASET_COL_MAGNETIC_FIELD  = C = C + 1
DATASET_COL_CURRENT         = C = C + 1
DATASET_COL_VOLTAGE         = C = C + 1

T_to_mT                     = 1e3
mT_to_T                     = 1e-3

# breakPlot
NO_BREAKPLOT                 = False
DO_BREAKPLOT                 = True
