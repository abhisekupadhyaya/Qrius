CONNECT_DEVICE              = C = 0
DISCONNECT_DEVICE           = C = C + 1

DEVICE_CONNECTING           = C = C + 1
DEVICE_CONNECTED            = C = C + 1
DEVICE_DISCONNECTING        = C = C + 1
DEVICE_DISCONNECTED         = C = C + 1
DEVICE_NOT_FOUND            = C = C + 1

CM_RANGE_CHANGED            = C = C + 1
VM_RANGE_CHANGED            = C = C + 1
VM2_RANGE_CHANGED           = C = C + 1
SOURCE_PARAMETERS_CHANGED   = C = C + 1

RUN_MODE                    = C = C + 1
RUN_MODE_ITime              = C = C + 1
RUN_MODE_VTime              = C = C + 1
RUN_MODE_IV                 = C = C + 1
RUN_MODE_RTime              = C = C + 1
RUN_MODE_IV_TIME_RESOLVED   = C = C + 1

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
IV_RAMP_SETTINGS_DIALOG     = C = C + 1
IV_TIME_RESOLVED_RAMP_SETTINGS_DIALOG = C = C + 1
OHMMETER_SETTINGS_DIALOG    = C = C + 1

APPLY                       = C = C + 1
CANCEL                      = C = C + 1

OPEN_METHOD                 = C = C + 1
SAVE_METHOD                 = C = C + 1

# src_mode
SOURCE_MODE_CS              = C = 0
SOURCE_MODE_VS              = C = C + 1

# src autorange
AUTORANGE_ON                = True
AUTORANGE_OFF               = True

# vs_range
VS_RANGE_10V                = C = 0
VS_RANGE_100V               = C = C + 1
VS_RANGE_MIN                = VS_RANGE_10V
VS_RANGE_MAX                = VS_RANGE_10V
VS_RANGES                   = [10.0]

# vm_range
VM_RANGE_1mV                = C = 0
VM_RANGE_10mV               = C = C + 1
VM_RANGE_100mV              = C = C + 1
VM_RANGE_1V                 = C = C + 1
VM_RANGE_10V                = C = C + 1
VM_RANGE_100V               = C = C + 1
VM_RANGE_MIN                = VM_RANGE_100mV
VM_RANGE_MAX                = VM_RANGE_10V
VM_RANGES                   = [1e-3, 10e-3, 100e-3, 1.0, 10.0, 100.0]

# cm_range
CM_RANGE_10uA               = C = 0
CM_RANGE_100uA              = C = C + 1
CM_RANGE_1mA                = C = C + 1
CM_RANGE_10mA               = C = C + 1
CM_RANGE_100mA              = C = C + 1
CM_RANGE_MIN                = CM_RANGE_100uA
CM_RANGE_MAX                = CM_RANGE_10mA
CM_RANGES                   = [10e-6, 100e-6, 1e-3, 10e-3, 100e-3]

# vm2_range
VM2_RANGE_10V               = C = 0
VM2_RANGE_MIN               = VM2_RANGE_10V
VM2_RANGE_MAX               = VM2_RANGE_10V
VM2_RANGES                  = [10.0]

COMM_TIMEOUT_INTERVAL       = 1.0

R_TRACK_V_I                 = C = 0
R_TRACK_dV_dI               = C = C + 1

# scanMode
SCAN_MODE_POSITIVE          = C = 0
SCAN_MODE_NEGATIVE          = C = C + 1

DATASET_COL_TIME            = C = 0
DATASET_COL_CURRENT         = C = C + 1
DATASET_COL_VOLTAGE         = C = C + 1
DATASET_COL_VSRC            = C = C + 1
DATASET_COL_RESISTANCE      = C = C + 1

V_to_mV                     = 1e3
A_to_uA                     = 1e6

mV_to_V                     = 1e-3
uA_to_A                     = 1e-6

W_to_mW                     = 1e3
mW_to_W                     = 1e-3

# breakPlot
NO_BREAKPLOT                 = False
DO_BREAKPLOT                 = True
