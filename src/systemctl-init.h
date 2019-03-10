#ifndef SYSTEMCTL_INIT_H
#define SYSTEMCTL_INIT_H 1

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include "systemctl-types.h"

typedef struct systemctl_settings
{
    /* defaults for options */
    char** extra_vars;
    bool   force;
    bool   full;
    bool   now;
    bool   no_legend;
    bool   no_ask_password;
    char*  preset_mode;
    bool   quiet;
    char*  root;
    char*  unit_type;
    char*  unit_state;
    char*  unit_property;
    bool   show_all;
    bool   user_mode;
    /* common default paths */
    char*  default_target;
    char*  system_folder1;
    char*  system_folder2;
    char*  system_folder3;
    char*  system_folder4;
    char*  system_folder9;
    char*  user_folder1;
    char*  user_folder2;
    char*  user_folder3;
    char*  user_folder4;
    char*  user_folder9;
    char*  init_folder1;
    char*  init_folder2;
    char*  init_folder9;
    char*  preset_folder1;
    char*  preset_folder2;
    char*  preset_folder3;
    char*  preset_folder4;
    char*  preset_folder9;
    /* definitions */
    int SystemCompatabilityVersion;
    float MinimumYield;
    int MinimumTimeoutStartSec;
    int MinimumTimeoutStopSec;
    int DefaultTimeoutStartSec;
    int DefaultTimeoutStopSec;
    int DefaultMaximumTimeout;
    int InitLoopSleep;
    int ProcMaxDepth;
    int MaxLockWait;
    char* DefaultPath;
    str_list_t* ResetLocale;
    /* system defaults */
    char* notify_socket_folder;
    char* pid_file_folder;
    char* journal_log_folder;
    char* debug_log;
    char* extra_log;
} systemctl_settings_t;

struct systemctl_conf_data;
typedef struct systemctl_conf_data systemctl_conf_data_t;

struct systemctl_conf;
typedef struct systemctl_conf systemctl_conf_t;

struct systemctl;
typedef struct systemctl systemctl_t;

#endif
