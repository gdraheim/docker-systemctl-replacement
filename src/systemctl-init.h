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

struct systemctl_unit_name;
typedef struct systemctl_unit_name systemctl_unit_name_t;

/* from systemctl-init.c */

void
systemctl_settings_init(systemctl_settings_t* self);

str_t restrict
unit_of(str_t module);

str_t restrict
os_path(str_t root, str_t path);

str_t /* not free */
os_getlogin_p();

str_t restrict
os_getlogin();

str_t restrict
get_runtime_dir();

str_t restrict
get_home();

str_t restrict
os_environ_get(const char* name, str_t restrict defaults);

void
systemctl_conf_data_init(systemctl_conf_data_t* self);

systemctl_conf_data_t* restrict
systemctl_conf_data_new();

void
systemctl_conf_data_null(systemctl_conf_data_t* self);

void
systemctl_conf_data_free(systemctl_conf_data_t* self);

str_list_t*
systemctl_conf_data_filenames(systemctl_conf_data_t* self);

str_list_t* restrict
systemctl_conf_data_sections(systemctl_conf_data_t* self);

void
systemctl_conf_data_add_section(systemctl_conf_data_t* self, str_t section);

bool
systemctl_conf_data_has_section(systemctl_conf_data_t* self, str_t section);

bool
systemctl_conf_data_has_option(systemctl_conf_data_t* self, str_t section, str_t option);

bool
systemctl_conf_data_sets(systemctl_conf_data_t* self, str_t section, str_t option, str_t value);

bool
systemctl_conf_data_set(systemctl_conf_data_t* self, str_t section, str_t option, str_t value);

str_t
systemctl_conf_data_get(systemctl_conf_data_t* self, str_t section, str_t option);

str_list_t*
systemctl_conf_data_getlist(systemctl_conf_data_t* self, str_t section, str_t option);

bool
systemctl_conf_data_read(systemctl_conf_data_t* self, str_t filename);

bool
systemctl_conf_data_read_sysd(systemctl_conf_data_t* self, str_t filename);

bool
systemctl_conf_data_read_sysv(systemctl_conf_data_t* self, str_t filename);

void
systemctl_conf_init(systemctl_conf_t* self);

systemctl_conf_t* restrict
systemctl_conf_new();

void
systemctl_conf_null(systemctl_conf_t* self);

void
systemctl_conf_free(systemctl_conf_t* self);

str_t
systemctl_conf_loaded(systemctl_conf_t* self);

void
systemctl_conf_set(systemctl_conf_t* self, str_t section, str_t name, str_t value);

str_t
systemctl_conf_get(systemctl_conf_t* self, str_t section, str_t name, str_t defaults);

str_list_t*
systemctl_conf_getlist(systemctl_conf_t* self, str_t section, str_t name, str_list_t* defaults);

bool
systemctl_conf_getbool(systemctl_conf_t* self, str_t section, str_t name, str_t defaults);

str_t
systemctl_conf_filename(systemctl_conf_t* self);

str_t restrict
systemctl_conf_name(systemctl_conf_t* self);

str_t /* do not str_free this */
systemctl_name(systemctl_conf_t* self);

void
systemctl_init(systemctl_t* self, systemctl_settings_t* settings);

void
systemctl_null(systemctl_t* self);

str_t /* no free here */
systemctl_root(systemctl_t* self, str_t path);

str_t
systemctl_current_user(systemctl_t* self);

bool
systemctl_user_mode(systemctl_t* self);

str_t restrict
systemctl_user_folder(systemctl_t* self);

str_t restrict
systemctl_system_folder(systemctl_t* self);

str_list_t* restrict
systemctl_preset_folders(systemctl_t* self);

str_list_t* restrict
systemctl_init_folders(systemctl_t* self);

str_list_t* restrict
systemctl_user_folders(systemctl_t* self);

str_list_t* restrict
systemctl_system_folders(systemctl_t* self);

str_list_t* restrict
systemctl_sysd_folders(systemctl_t* self);

void
systemctl_scan_unit_sysd_files(systemctl_t* self);

void
systemctl_scan_unit_sysv_files(systemctl_t* self);

str_t
systemctl_unit_sysd_file(systemctl_t* self, str_t module);

str_t
systemctl_unit_sysv_file(systemctl_t* self, str_t module);

str_t
systemctl_unit_file(systemctl_t* self, str_t module);

bool
systemctl_is_user_conf(systemctl_t* self, systemctl_conf_t* conf);

bool
systemctl_not_user_conf(systemctl_t* self, systemctl_conf_t* conf);

str_dict_t* restrict
systemctl_find_drop_in_files(systemctl_t* self, str_t unit);

systemctl_conf_t*
systemctl_load_sysd_unit_conf(systemctl_t* self, str_t module);

bool
systemctl_is_sysv_file(systemctl_t* self, str_t filename);

systemctl_conf_t*
systemctl_load_sysv_unit_conf(systemctl_t* self, str_t module);

systemctl_conf_t*
systemctl_load_unit_conf(systemctl_t* self, str_t module);

systemctl_conf_t*
systemctl_conf_default(systemctl_conf_t* self, str_t module);

systemctl_conf_t* restrict
systemctl_default_unit_conf(systemctl_t* self, str_t module);

systemctl_conf_t*
systemctl_get_unit_conf(systemctl_t* self, str_t unit);

str_list_t* restrict
systemctl_match_sysd_units(systemctl_t* self, str_list_t* modules);

str_list_t* restrict
systemctl_match_sysv_units(systemctl_t* self, str_list_t* modules);

str_list_t* restrict
systemctl_match_units(systemctl_t* self, str_list_t* modules);

str_list_list_t* restrict
systemctl_list_service_unit_basics(systemctl_t* self);

str_list_list_t* restrict
systemctl_list_service_units(systemctl_t* self, str_list_t* modules);

str_list_list_t* restrict
systemctl_list_units(systemctl_t* self, str_list_t* modules);

str_list_list_t* restrict
systemctl_list_service_unit_files(systemctl_t* self, str_list_t* modules);

str_dict_t* restrict
systemctl_each_target_file(systemctl_t* self);

str_list_list_t*
systemctl_list_target_unit_files(systemctl_t* self, str_list_t* modules);

str_list_list_t*
systemctl_show_list_unit_files(systemctl_t* self, str_list_t* modules);

str_t restrict
systemctl_get_description_from(systemctl_t* self, systemctl_conf_t* conf);

str_t restrict
systemctl_get_description(systemctl_t* self, str_t unit);

int
systemctl_read_pid_file(systemctl_t* self, str_t pid_file);

double
systemctl_get_boottime(systemctl_t* self);

double
systemctl_get_boottime_oldest(systemctl_t* self);

double
systemctl_get_filetime(systemctl_t* self, str_t filename);

bool
systemctl_truncate_old(systemctl_t* self, str_t filename);

off_t
systemctl_getsize(systemctl_t* self, str_t filename);

str_dict_t* restrict
systemctl_read_env_file(systemctl_t* self, str_t env_file);

str_dict_t* restrict
systemctl_read_env_part(systemctl_t* self, str_t env_part);

str_dict_t* restrict
systemctl_get_env(systemctl_t* self, systemctl_conf_t* conf);

str_dict_t* restrict
systemctl_show_environment(systemctl_t* self, str_t unit);

str_t restrict
str_expand(str_t regex, str_t value, str_dict_t* env);

str_t restrict
str_expand_env1(str_t value, str_dict_t* env);

str_t restrict
str_expand_env2(str_t value, str_dict_t* env);

str_t restrict
systemctl_expand_env(systemctl_t* self, str_t value, str_dict_t* env);

systemctl_unit_name_t*
systemctl_unit_name_new();

void
systemctl_unit_name_free(systemctl_unit_name_t* unit);

systemctl_unit_name_t* restrict
systemctl_parse_unit(systemctl_t* self, systemctl_conf_t* conf);

static str_t restrict
sh_escape(str_t value);

str_dict_t* restrict
systemctl_get_special_confs(systemctl_t* self, systemctl_conf_t* conf);

str_t
systemctl_expand_special(systemctl_t* self, str_t value, systemctl_conf_t* conf);

str_list_t* restrict
systemctl_exec_cmd(systemctl_t* self, str_t value, str_dict_t* env, systemctl_conf_t* conf);

str_t restrict
systemctl_get_active_from(systemctl_t* self, systemctl_conf_t* conf);

str_t restrict
systemctl_get_substate_from(systemctl_t* self, systemctl_conf_t* conf);

str_t
systemctl_enabled(systemctl_t* self, str_t unit);

str_t
systemctl_enabled_from(systemctl_t* self, systemctl_conf_t* conf);

str_t restrict
systemctl_status_modules(systemctl_t* self, str_list_t* modules);

str_t restrict
systemctl_status_units(systemctl_t* self, str_list_t* units);

str_t restrict
systemctl_status_unit(systemctl_t* self, str_t unit);

int
str_print(str_t result);

int
str_list_print(str_list_t* result);

int
str_dict_print(str_dict_t* result);

int
str_list_list_print(str_list_list_t* result);

#endif
