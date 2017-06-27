from math import pi

APPLY                   	= C = 0
CANCEL                  	= C = C + 1

RUN_MODE                                = C = 0
RUN_MODE_XT_LINEAR_RAMP                 = C = C + 1
RUN_MODE_XT_STEP_RAMP                   = C = C + 1
RUN_MODE_XF_STEP_RAMP                   = C = C + 1
RUN_MODE_XL_PREP                        = C = C + 1
RUN_MODE_XL                             = C = C + 1

START_RUN                               = C = C + 1
FINISH_RUN                              = C = C + 1

RUN_STARTING                            = C = C + 1
RUN_STARTED                             = C = C + 1
RUN_FINISHING                           = C = C + 1
RUN_FINISHED                            = C = C + 1
RUN_PREPARING                           = C = C + 1
RUN_PROCEED                             = C = C + 1
RUN_PROCEED_STARTED                     = C = C + 1

OPEN_DEVICE                             = C = C + 1
TCON_DEVICE                             = C = C + 1
XLIA_DEVICE                             = C = C + 1
XMC_DEVICE                              = C = C + 1

OPEN_DIALOG                             = C = C + 1

XL_FIND_EXTREMA                         = C = C + 1

OPEN_METHOD                             = C = C + 1
SAVE_METHOD                             = C = C + 1

PROCEED_RUN                             = C = C + 1

ACQ_SETTING_DIALOG                   = C = 0

DATASET_COL_TIME                        = C = 0
DATASET_COL_REF_FREQ                    = C = C + 1
DATASET_COL_CURRENT_AMPL                = C = C + 1
DATASET_COL_CURRENT_PHASE               = C = C + 1
DATASET_COL_SIGNAL_AMPL                 = C = C + 1
DATASET_COL_SIGNAL_PHASE                = C = C + 1
DATASET_COL_CHIP                        = C = C + 1
DATASET_COL_CHIDP                       = C = C + 1
DATASET_COL_SAMPLE_TEMPERATURE          = C = C + 1
DATASET_COL_HEATER_TEMPERATURE          = C = C + 1
DATASET_COL_PROBE_POSITION              = C = C + 1

PROBE_UP                                = C = 0
PROBE_DOWN                              = C = C + 1

# Conversions
mV_to_V                           = 1e-3
V_to_mV                           = 1e3

mA_to_A                           = 1e-3
A_to_mA                           = 1e3

rad_to_deg                        = 180.0 / pi
deg_to_rad                        = pi / 180.0

mm_to_m                           = 1e-3
m_to_mm                           = 1e3
