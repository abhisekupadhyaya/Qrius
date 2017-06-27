RUN_MODE                                = C = 0
RUN_MODE_RT_LINEAR_RAMP                 = C = C + 1
RUN_MODE_RT_STEP_RAMP                   = C = C + 1
RUN_MODE_IV_STEP_RAMP                   = C = C + 1
RUN_MODE_RTH_LINEAR_RAMP                = C = C + 1
RUN_MODE_RHT_STEPPED_RAMP               = C = C + 1

START_RUN                               = C = C + 1
FINISH_RUN                              = C = C + 1

RUN_STARTING                            = C = C + 1
RUN_STARTED                             = C = C + 1
RUN_FINISHING                           = C = C + 1
RUN_FINISHED                            = C = C + 1

OPEN_DEVICE                             = C = C + 1
TCON_DEVICE                             = C = C + 1
XSMU_DEVICE                             = C = C + 1
MGPS_DEVICE                             = C = C + 1

OPEN_METHOD                             = C = C + 1
SAVE_METHOD                             = C = C + 1

OPEN_DIALOG                             = C = C + 1
RH_SETTINGS_DIALOG                      = C = C + 1

APPLY                                   = C = C + 1
CANCEL                                  = C = C + 1

DATASET_COL_TIME                        = C = 0
DATASET_COL_CURRENT                     = C = C + 1
DATASET_COL_VOLTAGE                     = C = C + 1
DATASET_COL_RESISTANCE                  = C = C + 1
DATASET_COL_SAMPLE_TEMPERATURE          = C = C + 1
DATASET_COL_HEATER_TEMPERATURE          = C = C + 1
DATASET_COL_MAGNETIC_FIELD              = C = C + 1

A_to_uA                                 = 1e6
uA_to_A                                 = 1e-6

V_to_mV                                 = 1e3
mV_to_V                                 = 1e-3
