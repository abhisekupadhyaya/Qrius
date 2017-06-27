from math import pi

# Callback contexts
CONNECT_DEVICE                    = C = 0
DISCONNECT_DEVICE                 = C = C + 1
DEVICE_CONNECTING                 = C = C + 1
DEVICE_CONNECTED                  = C = C + 1
DEVICE_DISCONNECTING              = C = C + 1
DEVICE_DISCONNECTED               = C = C + 1
DEVICE_NOT_FOUND                  = C = C + 1

RUN_MODE                          = C = C + 1
RUN_MODE_VF                       = C = C + 1
RUN_MODE_VTime                    = C = C + 1

START_RUN                         = C = C + 1
FINISH_RUN                        = C = C + 1
RUN_STARTING                      = C = C + 1
RUN_STARTED                       = C = C + 1
RUN_FINISHING                     = C = C + 1
RUN_FINISHED                      = C = C + 1

REFERENCE_PARAMETER               = C = C + 1
MEASUREMENT_SETTINGS              = C = C + 1

OPEN_DIALOG                       = C = C + 1
REFERENCE_PARAMETER_DIALOG        = C = C + 1
MEASUREMENT_SETTINGS_DIALOG       = C = C + 1
ACQUISITION_SETTINGS_DIALOG       = C = C + 1
VF_RAMP_SETTINGS_DIALOG           = C = C + 1

VF_FREQ_STEP_MODE_LINEAR          = C = C + 1
VF_FREQ_STEP_MODE_LOG             = C = C + 1

APPLY                             = C = C + 1
CANCEL                            = C = C + 1

OPEN_METHOD                       = C = C + 1
SAVE_METHOD                       = C = C + 1

# Preamp input enumeration
INPUT_CHANNEL_INPUT_VOLTAGE       = C = 0
INPUT_CHANNEL_REFERENCE_CURRENT   = C = C + 1

# Preamp coupling enumeration
PREAMP_COUPLING_DC                = C = 0
PREAMP_COUPLING_AC                = C = C + 1

# Preamp gain enumeration
PREAMP_GAIN_1                     = C = 0
PREAMP_GAIN_10                    = C = C + 1
PREAMP_GAIN_100                   = C = C + 1

# Postamp gain enumeration
POSTAMP_GAIN_1                    = C = 0
POSTAMP_GAIN_10                   = C = C + 1
POSTAMP_GAIN_100                  = C = C + 1

# Time constant enumeration
INTGTR_TC_2ms                     = C = 0
INTGTR_TC_5ms                     = C = C + 1
INTGTR_TC_1sec                    = C = C + 1

# Communication
COMM_TIMEOUT_DELAY                = 2.0

# Conversions
mV_to_V                           = 1e-3
V_to_mV                           = 1e3

mA_to_A                           = 1e-3
A_to_mA                           = 1e3

rad_to_deg                        = 180.0 / pi
deg_to_rad                        = pi / 180.0

# Dataset columns
DATASET_COL_TIME                  = C = 0
DATASET_COL_REF_AMPL              = C = C + 1
DATASET_COL_REF_FREQ              = C = C + 1
DATASET_COL_REF_PHASE             = C = C + 1
DATASET_COL_CURRENT_AMPL          = C = C + 1
DATASET_COL_CURRENT_PHASE         = C = C + 1
DATASET_COL_SIGNAL_AMPL           = C = C + 1
DATASET_COL_SIGNAL_PHASE          = C = C + 1

MAX_DRIVE_VOLTAGE                 = 1.0

DRIVE_MODE_VS                     = C = 0
DRIVE_MODE_CS                     = C = C + 1

MEASUREMENT_MODE_QUICK            = C = 0
MEASUREMENT_MODE_FULL             = C = C + 1
