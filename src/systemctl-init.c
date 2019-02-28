/* 
 * This implementation follows the structure of systemctl.py very closely.
 * In that way it is possible to do debugging in python transposing the
 * the solutions into C code after that.
 */

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <limits.h>
#include <stdio.h>
#include <regex.h>
#include <fnmatch.h>
#include "systemctl-types.c"
#include "systemctl-options.c"

typedef char systemctl_copyright_t[64];
typedef char systemctl_version_t[16];

#define __copyright__ systemctl_copyright_t systemctl_copyright
#define __version__ systemctl_version_t systemctl_version

__copyright__ = "(C) 2016-2019 Guido U. Draheim, licensed under the EUPL";
__version__ = "2.5.3050";

char* SYSTEMCTL_COVERAGE = ""; 
char* SYSTEMCTL_DEBUG_AFTER = ""; 
char* SYSTEMCTL_EXIT_WHEN_NO_MORE_PROCS = "";
char* SYSTEMCTL_EXIT_WHEN_NO_MORE_SERVICES = "";

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

void
systemctl_settings_init(systemctl_settings_t* self)
{
    char** extra_vars = { NULL };
    self->extra_vars = extra_vars;
    self->force = false;
    self->full = false;
    self->now = false;
    self->no_legend = false;
    self->no_ask_password = false;
    self->preset_mode = "all";
    self->quiet = false;
    self->root = "";
    self->unit_type = NULL;
    self->unit_state = NULL;
    self->unit_property = NULL;
    self->show_all = false;
    self->user_mode = false;

    self->default_target = "multi-user.target";
    self->system_folder1 = "/etc/systemd/system";
    self->system_folder2 = "/var/run/systemd/system";
    self->system_folder3 = "/usr/lib/systemd/system";
    self->system_folder4 = "/lib/systemd/system";
    self->system_folder9 = NULL;
    self->user_folder1 = "~/.config/systemd/user";
    self->user_folder2 = "/etc/systemd/user";
    self->user_folder3 = "~.local/share/systemd/user";
    self->user_folder4 = "/usr/lib/systemd/user";
    self->user_folder9 = NULL;
    self->init_folder1 = "/etc/init.d";
    self->init_folder2 = "/var/run/init.d";
    self->init_folder9 = NULL;
    self->preset_folder1 = "/etc/systemd/system-preset";
    self->preset_folder2 = "/var/run/systemd/system-preset";
    self->preset_folder3 = "/usr/lib/systemd/system-preset";
    self->preset_folder4 = "/lib/systemd/system-preset";
    self->preset_folder9 = NULL;
    /* definitions */
    self->SystemCompatabilityVersion = 219;
    self->MinimumYield = 0.5;
    self->MinimumTimeoutStartSec = 4;
    self->MinimumTimeoutStopSec = 4;
    self->DefaultTimeoutStartSec = 90;
    self->DefaultTimeoutStopSec = 90;
    self->DefaultMaximumTimeout = 200;
    self->InitLoopSleep = 5;
    self->ProcMaxDepth = 100;
    self->MaxLockWait = -1;
    self->DefaultPath = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/sbin:/bin";
    char* ResetLocale_data[] = {
        "LANG", "LANGUAGE", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", 
        "LC_COLLATE", "LC_MONETARY", "LC_MESSAGES", "LC_PAPER", 
        "LC_NAME", "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT", 
        "LC_IDENTIFICATION", "LC_ALL" };
    str_list_t ResetLocale_list = { 15, ResetLocale_data };
    self->ResetLocale = &ResetLocale_list;
    /* the systemd default is NOTIFY_SOCKET="/var/run/systemd/notify" */
    self->notify_socket_folder = "/var/run/systemd";
    self->pid_file_folder = "/var/run";
    self->journal_log_folder = "/var/log/journal";
    self->debug_log = "/var/log/systemctl.debug.log";
    self->extra_log = "/var/log/systemctl.log";
}

str_dict_entry_t systemctl_runlevel_data[] = 
{
  { "0", "poweroff.target" },
  { "1", "rescue.target" },
  { "2", "multi-user.target" },
  { "3", "multi-user.target" },
  { "4", "multi-user.target" },
  { "5", "graphical.target" },
  { "6", "reboot.target" },
};

str_dict_t systemctl_runlevel_mappings = { 7, systemctl_runlevel_data };

str_dict_entry_t systemctl_sysv_data[] = 
{
  { "$local_fs", "local-fs.target" },
  { "$network", "network.target" },
  { "$remote_fs", "remote-fs.target" },
  { "$timer", "timers.target" },
};

str_dict_t systemctl_sysv_mappings = { 4, systemctl_sysv_data };

/* .............................. */

str_t restrict
unit_of(str_t module)
{
    if (! strchr(module, '.')) {
        return str_dup2(module, ".service");
    }
    return str_dup(module);
}

/* .............................. */

typedef struct systemctl_conf_data
{
    str_list_dict_dict_t defaults;
    str_list_dict_dict_t conf;
    str_list_t files;
} systemctl_conf_data_t;


void 
systemctl_conf_data_init(systemctl_conf_data_t* self)
{
    str_list_dict_dict_init(&self->defaults);
    str_list_dict_dict_init(&self->conf);
    str_list_init(&self->files);
}

systemctl_conf_data_t* restrict
systemctl_conf_data_new()
{
    systemctl_conf_data_t* self = malloc(sizeof(systemctl_conf_data_t));
    systemctl_conf_data_init(self);
    return self;
}

void 
systemctl_conf_data_null(systemctl_conf_data_t* self)
{
    str_list_dict_dict_null(&self->defaults);
    str_list_dict_dict_null(&self->conf);
    str_list_null(&self->files);
}

void
systemctl_conf_data_free(systemctl_conf_data_t* self)
{
    if (self) {
        systemctl_conf_data_null(self);
        free (self);
    }
}

str_list_t*
systemctl_conf_data_filenames(systemctl_conf_data_t* self)
{
    return &self->files;
}

str_list_t* restrict
systemctl_conf_data_sections(systemctl_conf_data_t* self)
{
    return str_list_dict_dict_keys(&self->conf);
}

void
systemctl_conf_data_add_section(systemctl_conf_data_t* self, str_t section)
{
    if (! str_list_dict_dict_contains(&self->conf, section)) {
        str_list_dict_t empty = str_list_dict_NULL;
        str_list_dict_dict_add(&self->conf, section, &empty);
    }
}

bool
systemctl_conf_data_has_section(systemctl_conf_data_t* self, str_t section)
{
    return str_list_dict_dict_contains(&self->conf, section);
}

bool
systemctl_conf_data_has_option(systemctl_conf_data_t* self, str_t section, str_t option)
{
    str_list_dict_t* options = str_list_dict_dict_get(&self->conf, section);
    if (! options) return false;
    return str_list_dict_contains(options, option);
}

bool
systemctl_conf_data_sets(systemctl_conf_data_t* self, str_t section, str_t option, str_t value)
{
    str_list_dict_t* options1 = str_list_dict_dict_get(&self->conf, section);
    if (! options1) systemctl_conf_data_add_section(self, section);
    str_list_dict_t* options2 = str_list_dict_dict_get(&self->conf, section);
    str_list_t* values1 = str_list_dict_get(options2, option);
    if (value == NULL)
    {
        if (values1) {
           str_list_null(values1);
           str_list_init(values1);
        }
        return true;
    }

    if (values1) {
        str_list_adds(values1, value);
    } else {
        str_list_t* values = str_list_new();
        str_list_adds(values, value);
        str_list_dict_adds(options2, option, values);
    }
    return true;
}

bool
systemctl_conf_data_set(systemctl_conf_data_t* self, str_t section, str_t option, str_t value)
{
    return systemctl_conf_data_sets(self, section, option, str_dup(value));
}

str_t
systemctl_conf_data_get(systemctl_conf_data_t* self, str_t section, str_t option)
{
    str_list_dict_t* options = str_list_dict_dict_get(&self->conf, section);
    if (! options) return NULL;
    str_list_t* values = str_list_dict_get(options, option);
    if (! values) return NULL;
    if (values->size <= 0) return NULL;
    return values->data[0];
}

str_list_t*
systemctl_conf_data_getlist(systemctl_conf_data_t* self, str_t section, str_t option)
{
    str_list_dict_t* options = str_list_dict_dict_get(&self->conf, section);
    if (! options) return NULL;
    return str_list_dict_get(options, option);
}

bool
systemctl_conf_data_read_sysd(systemctl_conf_data_t* self, str_t filename);

bool
systemctl_conf_data_read(systemctl_conf_data_t* self, str_t filename)
{
    return systemctl_conf_data_read_sysd(self, filename);
}

bool
systemctl_conf_data_read_sysd(systemctl_conf_data_t* self, str_t filename)
{
    bool res = false;
    regmatch_t m[4];
    size_t m3 = 3;
    bool initscript = false;
    bool initinfo = false;
    str_t section = NULL;
    bool nextline = false;
    str_t name = str_dup("");
    str_t text = NULL;
    FILE* fd = fopen(filename, "r");
    if (fd == NULL) return false;
    str_t orig_line = NULL;
    str_t line = NULL;
    while(true) {
        if (orig_line) free(orig_line);
        orig_line = NULL; /* allocate as needed */
        size_t maxlen = 0; /* when both are null */
        ssize_t len = getline(&orig_line, &maxlen, fd);
        if (len <= 0) break;
        if (nextline) {
            str_sets(&text, str_dup2(text, orig_line));
            if (str_endswith(text, "\\") || str_endswith(text, "\\\n")) {
                str_sets(&text, str_rstrip(text));
                str_sets(&text, str_dup2(text, "\n"));
                continue;
            } else {
                systemctl_info("set from nextline");
                systemctl_conf_data_set(self, section, name, text);
                nextline = false;
                continue;
            }
        }
        str_sets(&line, str_rstrip(orig_line));
        if (line == NULL || ! str_len(line))
            continue;
        if (str_startswith(line, "#"))
            continue;
        if (str_startswith(line, ";"))
            continue;
        if (str_startswith(line, ".include")) {
            str_t includefile = str_dup(line + sizeof(".include"));
            str_sets(&includefile, str_strip(includefile));
            FILE* fd2 = fopen(includefile, "r");
            if (fd2 == NULL) continue;
            fclose(fd2);
            systemctl_conf_data_read_sysd(self, includefile);
            str_null(&includefile);
            continue;
        }
        if (str_startswith(line, "[")) {
            ssize_t x = str_find(line, "]");
            if (x > 0) {
                str_sets(&section, str_cut(line, 1, x));
                systemctl_conf_data_add_section(self, section);
            }
            continue;
        }
        if (regmatch("(\\w+) *=(.*)", line, m3, m, 0)) {
            systemctl_error("bad ini line: '%s'", line);
            goto done;
        }
        str_sets(&name, str_cut(line, m[1].rm_so, m[1].rm_eo));
        str_sets(&text, str_cut(line, m[2].rm_so, m[2].rm_eo));
        if (str_endswith(text, "\\") || str_endswith(text, "\\\n")) {
            nextline = true;
            str_sets(&text, str_dup2(text, "\n"));
        } else {
            /* hint: an empty line shall reset the value-list */
            if (! str_len(text)) {
                str_sets(&text, NULL);
            }
            systemctl_conf_data_set(self, section, name, text);
        }
    }
    res = true;
  done:
    fclose(fd);
    str_null(&orig_line);
    str_null(&line);
    str_null(&text);
    str_null(&name);
    str_null(&section);
    return res;
}

bool
systemctl_conf_data_read_sysv(systemctl_conf_data_t* self, str_t filename)
{
    bool res = false;
    regex_t preg;
    regmatch_t m[3];
    size_t m3 = 3;
    bool initinfo = false;
    str_t section = NULL;
    str_t line = NULL;
    FILE* fd = fopen(filename, "r");
    if (fd == NULL) return false;
    str_t orig_line = NULL;
    while(true) {
        if (orig_line) free(orig_line);
        orig_line = NULL; /* allocate as needed */
        size_t maxlen = 0; /* when both are null */
        ssize_t len = getline(&orig_line, &maxlen, fd);
        if (len <= 0) break;
        str_sets(&line, str_strip(orig_line));
        if (str_startswith(line, "#")) {
            if (str_contains(line, " BEGIN INIT INFO")) {
                initinfo = true;
                str_set(&section, "init.d");
            }
            if (str_contains(line, " END INIT INFO")) {
                initinfo = false;
            }
            if (initinfo) {
                if (! regmatch("\\S+\\s*(\\w[\\w_-]*):(.*)", line, m3, m, 0)) {
                    str_t key = str_cut(line, m[1].rm_so, m[1].rm_eo);
                    str_t val = str_cut(line, m[1].rm_so, m[1].rm_eo);
                    str_sets(&val, str_strip(val));
                    systemctl_conf_data_set(self, section, key, val);
                    str_null(&key);
                    str_null(&val);
                }
            }
            continue;
        }
    }
    if (true) {
        str_t description = systemctl_conf_data_get(self, "init.d", "Description");
        if (!str_empty (description)) {
            systemctl_conf_data_set(self, "Unit", "Description", description);
        }
        str_t check = systemctl_conf_data_get(self, "init.d", "Required-Start");
        if (!str_empty(check)) {
            str_list_t* items = str_split(check, ' ');
            for(int n = 0; n < items->size; ++n) {
                str_t item = str_strip(items->data[n]);
                str_t val = str_dict_get(&systemctl_sysv_mappings, item);
                if (val != NULL) {
                    systemctl_conf_data_set(self, "Unit", "Requires", val);
                }
                str_null(&item);
            }
            str_list_null(items); /* TODO: str_list_free ? */
        }
        str_t provides = systemctl_conf_data_get(self, "init.d", "Provides");
        if (! str_empty(provides)) {
            systemctl_conf_data_set(self, "Install", "Alias", provides);
        }
        /* if already in multi-user.target then start it there. */
        str_t runlevels = systemctl_conf_data_get(self, "init.d", "Default-Start");
        if (! str_empty(runlevels)) {
            str_list_t* items = str_split(runlevels, ' ');
            for (int n = 0; n < items->size; ++n) {
                str_t item = str_strip(items->data[n]);
                str_t val = str_dict_get(&systemctl_runlevel_mappings, item);
                if (val != NULL) {
                    systemctl_conf_data_set(self, "Install", "WantedBy", val);
                }
                str_null(&item);
            }
            str_list_null(items); /* TODO: str_list_free ? */
        }
        systemctl_conf_data_set(self, "Service", "Type", "sysv");
    }
    res = true;
  done:
    fclose(fd);
    if (orig_line) free(orig_line);
    str_null(&line);
    str_null(&section);
    return res;
}

typedef struct systemctl_conf
{
    systemctl_conf_data_t data;
    str_dict_t env;
    str_t status;
    str_t masked;
    str_t module;
    str_dict_t drop_in_files;
} systemctl_conf_t;

void 
systemctl_conf_init(systemctl_conf_t* self)
{
    systemctl_conf_data_init(&self->data);
    str_dict_init(&self->env);
    str_init(&self->status);
    str_init(&self->masked);
    str_init(&self->module);
    str_dict_init(&self->drop_in_files);
}

systemctl_conf_t* restrict
systemctl_conf_new()
{
    systemctl_conf_t* result = malloc(sizeof(systemctl_conf_t));
    systemctl_conf_init(result);
    return result;
}

void 
systemctl_conf_null(systemctl_conf_t* self)
{
    systemctl_conf_data_null(&self->data);
    str_dict_null(&self->env);
    str_null(&self->status);
    str_null(&self->masked);
    str_null(&self->module);
    str_dict_null(&self->drop_in_files);
}

void
systemctl_conf_free(systemctl_conf_t* self)
{
    systemctl_conf_null(self);
    free(self);
}

str_t
systemctl_conf_loaded(systemctl_conf_t* self)
{
    str_list_t* files = systemctl_conf_data_filenames(&self->data);
    if (! str_empty(self->masked)) {
        return "masked";
    }
    if (str_list_len(files)) {
        return "loaded";
    }
    return "";
}


void
systemctl_conf_set(systemctl_conf_t* self, str_t section, str_t name, str_t value)
{
    systemctl_conf_data_set(&self->data, section, name, value);
}

str_t
systemctl_conf_get(systemctl_conf_t* self, str_t section, str_t name, str_t defaults)
{
    str_t result = systemctl_conf_data_get(&self->data, section, name);
    if (result == NULL) 
        result = defaults;
    return result;
}

str_list_t*
systemctl_conf_getlist(systemctl_conf_t* self, str_t section, str_t name, str_list_t* defaults)
{
    str_list_t* result = systemctl_conf_data_getlist(&self->data, section, name);
    if (result == NULL) 
        result = defaults;
    return result;
}

bool
systemctl_conf_getbool(systemctl_conf_t* self, str_t section, str_t name, str_t defaults)
{
    str_t value = systemctl_conf_data_get(&self->data, section, name);
    if (value == NULL) 
        value = defaults;
    if (value == NULL) 
        value = "no";
    if (!str_empty(value)) {
        if (strchr("YyTt123456789", value[0])) {
            return true;
        }
    }
    return false;
}

str_t
systemctl_conf_filename(systemctl_conf_t* self)
{
    str_list_t* files = systemctl_conf_data_filenames(&self->data);
    if (str_list_len(files)) {
        return files->data[0];
    }
    return NULL;
}

str_t
systemctl_conf_name(systemctl_conf_t* self)
{
    str_t name;
    str_init(&name);
    if (! str_empty(self->module)) {
        str_set(&name, self->module);
    }
    str_t filename = systemctl_conf_filename(self);
    if (! str_empty(filename)) {
        str_set(&name, os_path_basename(filename));
    }
    str_set(&name, systemctl_conf_get(self, "Unit", "Id", name));
    return name;
}

/* ============================================================ */

typedef struct systemctl
{
    systemctl_settings_t use;
    str_t _unit_state;
    ptr_dict_t loaded_file_sysv; /* /etc/init.d/name => conf */
    ptr_dict_t loaded_file_sysd; /* /etc/systemd/system/name.service => conf */
    ptr_dict_t not_loaded_confs; /* name.service => conf */
    str_dict_t file_for_unit_sysv; /* name.service => /etc/init.d/name */
    str_dict_t file_for_unit_sysd; /* name.service => /etc/systemd/system/name.service */
    /* FIXME: the loaded-conf is a mixture of parts from multiple files */
    bool user_mode;
} systemctl_t;

void
systemctl_init(systemctl_t* self, systemctl_settings_t* settings)
{
    self->use = *settings;
    ptr_dict_init(&self->loaded_file_sysv, (free_func_t) systemctl_conf_free);
    ptr_dict_init(&self->loaded_file_sysd, (free_func_t) systemctl_conf_free);
    ptr_dict_init(&self->not_loaded_confs, (free_func_t) systemctl_conf_free);
    str_dict_init(&self->file_for_unit_sysv);
    str_dict_init(&self->file_for_unit_sysd);
    self->user_mode = false;
}

void
systemctl_null(systemctl_t* self)
{
    str_dict_null(&self->file_for_unit_sysd);
    str_dict_null(&self->file_for_unit_sysv);
    ptr_dict_null(&self->not_loaded_confs);
    ptr_dict_null(&self->loaded_file_sysv);
    ptr_dict_null(&self->loaded_file_sysd);
}

bool
systemctl_user_mode(systemctl_t* self)
{
    return self->user_mode;
}

str_list_t* restrict
systemctl_preset_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(self->use.preset_folder1)) 
       str_list_add(result, self->use.preset_folder1);
   if (! str_empty(self->use.preset_folder2)) 
       str_list_add(result, self->use.preset_folder2);
   if (! str_empty(self->use.preset_folder3)) 
       str_list_add(result, self->use.preset_folder3);
   if (! str_empty(self->use.preset_folder4)) 
       str_list_add(result, self->use.preset_folder4);
   if (! str_empty(self->use.preset_folder9)) 
       str_list_add(result, self->use.preset_folder9);
   return result;
}

str_list_t* restrict
systemctl_init_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(self->use.init_folder1)) 
       str_list_add(result, self->use.init_folder1);
   if (! str_empty(self->use.init_folder2)) 
       str_list_add(result, self->use.init_folder2);
   if (! str_empty(self->use.init_folder9)) 
       str_list_add(result, self->use.init_folder9);
   return result;
}

str_list_t* restrict
systemctl_user_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(self->use.user_folder1)) 
       str_list_add(result, self->use.user_folder1);
   if (! str_empty(self->use.user_folder2)) 
       str_list_add(result, self->use.user_folder2);
   if (! str_empty(self->use.user_folder3)) 
       str_list_add(result, self->use.user_folder3);
   if (! str_empty(self->use.user_folder4)) 
       str_list_add(result, self->use.user_folder4);
   if (! str_empty(self->use.user_folder9)) 
       str_list_add(result, self->use.user_folder9);
   return result;
}

str_list_t* restrict
systemctl_system_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(self->use.system_folder1)) 
       str_list_add(result, self->use.system_folder1);
   if (! str_empty(self->use.system_folder2)) 
       str_list_add(result, self->use.system_folder2);
   if (! str_empty(self->use.system_folder3)) 
       str_list_add(result, self->use.system_folder3);
   if (! str_empty(self->use.system_folder4)) 
       str_list_add(result, self->use.system_folder4);
   if (! str_empty(self->use.system_folder9)) 
       str_list_add(result, self->use.system_folder9);
   return result;
}

str_list_t* restrict
systemctl_sysd_folders(systemctl_t* self)
{
    if (systemctl_user_mode(self)) {
        return systemctl_user_folders(self);
    } else {
        return systemctl_system_folders(self);
    }
}

void
systemctl_scan_unit_sysd_files(systemctl_t* self)
{
   /* FIXME: only scan once even when not files present */
   if (str_dict_empty(&self->file_for_unit_sysd)) {
       str_list_t* folders = systemctl_sysd_folders(self);
       for (int i=0; i < folders->size; ++i) {
           str_t folder = folders->data[i];
           if (str_empty(folder))
               continue;
           if (! os_path_isdir(folder))
               continue;
           str_list_t* names = os_listdir(folder);
           for (int j=0; j < names->size; ++j) {
              str_t name = names->data[j];
              str_t path = os_path_join(folder, name);
              if (os_path_isdir(path)) {
                 str_free(path);
                 continue;
              }
              if (! str_dict_contains(&self->file_for_unit_sysd, name)) {
                 // systemctl_info("found %s => %s", name, path);
                 str_dict_adds(&self->file_for_unit_sysd, name, path);
              } else {
                 str_free(path);
              }
           }
           str_list_free(names);
       }
       str_list_free(folders);
   }
}

void
systemctl_scan_unit_sysv_files(systemctl_t* self)
{
   /* FIXME: only scan once even when not files present */
   if (str_dict_empty(&self->file_for_unit_sysv)) {
       str_list_t* folders = systemctl_init_folders(self);
       for (int i=0; i < folders->size; ++i) {
           str_t folder = folders->data[i];
           if (str_empty(folder))
               continue;
           if (! os_path_isdir(folder))
               continue;
           str_list_t* names = os_listdir(folder);
           for (int j=0; j < names->size; ++j) {
              str_t name = names->data[j];
              str_t path = os_path_join(folder, name);
              if (os_path_isdir(path)) {
                 str_free(path);
                 continue;
              }
              str_t service_name = str_dup2(name, ".service");
              if (! str_dict_contains(&self->file_for_unit_sysv, service_name)) {
                 // systemctl_info("found %s => %s", name2, path);
                 str_dict_adds(&self->file_for_unit_sysv, service_name, path);
              } else {
                 str_free(path);
              }
              str_free(service_name);
           }
           str_list_free(names);
       }
       str_list_free(folders);
   }
}

str_t
systemctl_unit_sysd_file(systemctl_t* self, str_t module)
{
    /* FIXME: do not scan all of them? */
    systemctl_scan_unit_sysd_files(self);
    if (! str_empty(module)) {
        if (str_dict_contains(&self->file_for_unit_sysd, module)) {
            return str_dict_get(&self->file_for_unit_sysd, module);
        }
        str_t unit_of_module = unit_of(module);
        if (str_dict_contains(&self->file_for_unit_sysd, unit_of_module)) {
            str_t value = str_dict_get(&self->file_for_unit_sysd, unit_of_module);
            str_free(unit_of_module);
            return value;
        }
        str_free(unit_of_module);
    }
    return NULL;
}

str_t
systemctl_unit_sysv_file(systemctl_t* self, str_t module)
{
    /* FIXME: do not scan all of them? */
    systemctl_scan_unit_sysv_files(self);
    if (! str_empty(module)) {
        if (str_dict_contains(&self->file_for_unit_sysv, module)) {
            return str_dict_get(&self->file_for_unit_sysv, module);
        }
        str_t unit_of_module = unit_of(module);
        if (str_dict_contains(&self->file_for_unit_sysv, unit_of_module)) {
            str_t value = str_dict_get(&self->file_for_unit_sysv, unit_of_module);
            str_free(unit_of_module);
            return value;
        }
        str_free(unit_of_module);
    }
    return NULL;
}

str_t
systemctl_unit_file(systemctl_t* self, str_t module)
{
    str_t path = systemctl_unit_sysd_file(self, module);
    if (! str_empty(path)) return path;
    path = systemctl_unit_sysd_file(self, module);
    if (! str_empty(path)) return path;
    return NULL;
}

systemctl_conf_t* 
systemctl_load_sysd_unit_conf(systemctl_t* self, str_t module)
{
    str_t path = systemctl_unit_sysd_file(self, module);
    if (str_empty(path)) return NULL;
    if (ptr_dict_contains(&self->loaded_file_sysd, path)) {
        return ptr_dict_get(&self->loaded_file_sysd, path);
    }
    systemctl_conf_t* conf = systemctl_conf_new();
    systemctl_conf_data_read_sysd(&conf->data, path);
    str_set(&conf->module, module);
    ptr_dict_adds(&self->loaded_file_sysd, path, conf);
    return conf;

}

systemctl_conf_t* 
systemctl_load_sysv_unit_conf(systemctl_t* self, str_t module)
{
    str_t path = systemctl_unit_sysv_file(self, module);
    if (str_empty(path)) return NULL;
    if (ptr_dict_contains(&self->loaded_file_sysv, path)) {
        return ptr_dict_get(&self->loaded_file_sysv, path);
    }
    systemctl_conf_t* conf = systemctl_conf_new();
    systemctl_conf_data_read_sysv(&conf->data, path);
    conf->module = str_dup(module);
    ptr_dict_adds(&self->loaded_file_sysv, path, conf);
    return conf;
}

systemctl_conf_t* 
systemctl_load_unit_conf(systemctl_t* self, str_t module)
{
   systemctl_conf_t* conf = NULL;
   conf = systemctl_load_sysd_unit_conf(self, module);
   if (conf) return conf;
   conf = systemctl_load_sysv_unit_conf(self, module);
   if (conf) return conf;
   return NULL;
}

systemctl_conf_t*
systemctl_conf_default(systemctl_conf_t* self, str_t module)
{
   systemctl_conf_data_set(&self->data, "Unit", "Id", module);
   systemctl_conf_data_set(&self->data, "Unit", "Names", module);
   systemctl_conf_data_sets(&self->data, "Unit", "Description", str_dup2("NOT FOUND ", module));
   /* assert not systemctl_conf_data_loaded(self); */
   str_set(&self->module, module);
   return self;
}

systemctl_conf_t* restrict
systemctl_default_unit_conf(systemctl_t* self, str_t module)
{
    systemctl_conf_t* conf = systemctl_conf_new();
    systemctl_conf_default(conf, module);
    return conf;
}


systemctl_conf_t* 
systemctl_get_unit_conf(systemctl_t* self, str_t unit)
{
    systemctl_conf_t* conf = systemctl_load_unit_conf(self, unit);
    if (! conf) {
       conf = systemctl_default_unit_conf(self, unit);
       ptr_dict_adds(&self->not_loaded_confs, unit, conf);
    }
    return conf;
}

str_list_t* restrict
systemctl_match_sysd_units(systemctl_t* self, str_list_t* modules) 
{
    str_list_t* result = str_list_new();
    systemctl_scan_unit_sysd_files(self);
    for (int i=0; i < self->file_for_unit_sysd.size; ++i) {
        str_t item = self->file_for_unit_sysd.data[i].key;
        if (str_list_empty(modules)) {
            str_list_add(result, item);
        } else {
            /* FIXME: different implementation */
            for (int j=0; j < modules->size; ++j) {
                str_t module = modules->data[j];
                if (fnmatch(module, item, 0)) {
                   str_list_add(result, item);
                } else {
                    str_t module_suffix = str_dup2(module, ".service");
                    if (str_equal(module_suffix, item)) {
                        str_list_add(result, item);
                    }
                }
            }
        }
    }
    return result;
}

str_list_t* restrict
systemctl_match_sysv_units(systemctl_t* self, str_list_t* modules) 
{
    str_list_t* result = str_list_new();
    systemctl_scan_unit_sysv_files(self);
    return result;
}

str_list_t* restrict
systemctl_match_units(systemctl_t* self, str_list_t* modules) 
{
    str_list_t* found = str_list_new();
    str_list_t* sysd = systemctl_match_sysd_units(self, modules);
    for (int i=0; i < sysd->size; ++i) {
        if (! str_list_contains(found, sysd->data[i])) {
            str_list_adds(found, sysd->data[i]);
            sysd->data[i] = NULL;
        }
    }
    str_list_free(sysd);
    str_list_t* sysv = systemctl_match_sysv_units(self, modules);
    for (int i=0; i < sysv->size; ++i) {
        if (! str_list_contains(found, sysv->data[i])) {
            str_list_adds(found, sysv->data[i]);
            sysd->data[i] = NULL;
        }
    }
    str_list_free(sysv);
    return found;
}

str_t
systemctl_expand_special(systemctl_t* self, str_t value, systemctl_conf_t* conf)
{
    return str_dup(value);
}

str_t restrict
systemctl_get_active_from(systemctl_t* self, systemctl_conf_t* conf)
{
    return str_dup("");
}

str_t restrict
systemctl_get_substate_from(systemctl_t* self, systemctl_conf_t* conf)
{
    return str_dup("");
}

str_t restrict
systemctl_get_description_from(systemctl_t* self, systemctl_conf_t* conf)
{
    if (! conf) return str_dup("");
    str_t description = systemctl_conf_get(conf, "Unit", "Description", "");
    return systemctl_expand_special(self, description, conf);
}

str_t restrict
systemctl_get_description(systemctl_t* self, str_t unit)
{
   systemctl_conf_t* conf = systemctl_load_unit_conf(self, unit);
   return systemctl_get_description_from(self, conf);
}

str_list_list_t* restrict
systemctl_list_service_unit_basics(systemctl_t* self) 
{
    str_list_list_t* result = str_list_list_new();
    str_t filename = systemctl_unit_file(self, "");
    for (int i=0; i < self->file_for_unit_sysd.size; ++i) {
        str_t name = self->file_for_unit_sysd.data[i].key;
        str_t value = self->file_for_unit_sysd.data[i].value;
        str_list_list_add3(result, name, "SysD", value);
    }
    for (int i=0; i < self->file_for_unit_sysv.size; ++i) {
        str_t name = self->file_for_unit_sysv.data[i].key;
        str_t value = self->file_for_unit_sysv.data[i].value;
        str_list_list_add3(result, name, "SysV", value);
    }
    return result;
}

str_list_list_t* restrict
systemctl_list_service_units(systemctl_t* self, str_list_t* modules) 
{
     str_list_list_t* res = str_list_list_new();
     str_dict_t result = str_dict_NULL;
     str_dict_t active = str_dict_NULL;
     str_dict_t substate = str_dict_NULL;
     str_dict_t description = str_dict_NULL;
     str_list_t* units = systemctl_match_units(self, modules);
     for (int i = 0; i < units->size; ++i) {
         str_t unit = units->data[i];
         systemctl_conf_t* conf = systemctl_get_unit_conf(self, unit);
         if (conf) {
             str_dict_add(&result, unit, "loaded");
             str_dict_adds(&description, unit, systemctl_get_description_from(self, conf));
             str_dict_adds(&active, unit, systemctl_get_active_from(self, conf));
             str_dict_adds(&substate, unit, systemctl_get_substate_from(self, conf));
             if (self->use.unit_state) {
                 if (! str_list3_contains(
                    str_dict_get(&result, unit),
                    str_dict_get(&active, unit),
                    str_dict_get(&substate, unit),
                    self->use.unit_state)) {
                    str_dict_del(&result, unit);
                 }
             }
         }
     }
     for (int i=0; i < result.size; ++i) {
          str_t unit = result.data[i].key;
          str_list_t* line = str_list_new();
          str_list_adds(line, str_dup(unit));
          str_list_adds(line, str_list3_join(
              str_dict_get(&result, unit),
              str_dict_get(&active, unit),
              str_dict_get(&substate, unit),
              " "));
          str_list_add(line, str_dict_get(&description, unit));
          str_list_list_adds(res, line);
     }
     str_list_free(units);
     str_dict_null(&result);
     str_dict_null(&description);
     str_dict_null(&active);
     str_dict_null(&substate);
     return res;
}

str_list_list_t* restrict
systemctl_list_units(systemctl_t* self, str_list_t* modules)
{
    str_t hint = "To show all installed unit files use 'systemctl list-unit-files'.";
    str_list_list_t* result = systemctl_list_service_units(self, modules);
    if (self->use.no_legend) {
        return result;
    }
    str_t found = str_format("%i loaded units listed", str_list_list_len(result));
    str_list_list_add3(result, "", found, hint);
    str_free(found);
    return result;
}

str_t systemctl_enabled_from(systemctl_t* self, systemctl_conf_t* conf);

str_list_list_t* restrict
systemctl_list_service_unit_files(systemctl_t* self, str_list_t* modules)
{
     str_list_list_t* res = str_list_list_new();
     str_dict_t result = str_dict_NULL;
     str_dict_t enabled = str_dict_NULL;
     str_list_t* units = systemctl_match_units(self, modules);
     for (int i = 0; i < units->size; ++i) {
         str_t unit = units->data[i];
         systemctl_conf_t* conf = systemctl_get_unit_conf(self, unit);
         if (conf) {
             str_dict_add(&result, unit, "loaded");
             str_dict_add(&enabled, unit, systemctl_enabled_from(self, conf));
         }
     }
     for (int i=0; i < result.size; ++i) {
          str_t unit = result.data[i].key;
          str_list_t* line = str_list_new();
          str_list_adds(line, str_dup(unit));
          str_list_adds(line, str_dup(str_dict_get(&enabled, unit)));
          str_list_list_adds(res, line);
     }
     str_list_free(units);
     str_dict_null(&result);
     str_dict_null(&enabled);
     return res;
}

str_list_list_t*
systemctl_list_target_unit_files(systemctl_t* self, str_list_t* modules) 
{
   str_list_list_t* result = str_list_list_new();
   return result;
}

str_list_list_t*
systemctl_show_list_unit_files(systemctl_t* self, str_list_t* modules) 
{
    str_list_list_t* result;
    str_list_t no_modules;
    str_list_init(&no_modules);

    if (self->use.now) {
        /* FIXME: no modules filter? */
        result = systemctl_list_service_unit_basics(self);
    }
    else if (str_equal(self->use.unit_type, "target")) {
        /* FIXME: no modules filter? */
        result = systemctl_list_target_unit_files(self, &no_modules);
    }
    else if (str_equal(self->use.unit_type, "service")) {
        /* FIXME: no modules filter? */
        result = systemctl_list_service_unit_files(self, &no_modules);
    }
    else if (!str_empty(self->use.unit_type)) {
        systemctl_error("unsupported unit --type=%s", self->use.unit_type);
        result = str_list_list_new();
    }
    else {
        result = systemctl_list_target_unit_files(self, modules);
        str_list_list_t* result2 = systemctl_list_service_unit_files(self, modules);
        for (int j=0; j < result2->size; ++j) {
           str_list_list_add(result, &result2->data[j]);
        }
        str_list_list_free(result2);
    }
    if (self->use.no_legend) {
        return result;
    }
    str_t found = str_format("%i loaded units listed", str_list_list_len(result));
    str_list_list_add3(result, "", found, "");
    str_free(found);
    return result;
}

str_t 
systemctl_enabled(systemctl_t* self, str_t unit)
{
    systemctl_conf_t* conf = systemctl_get_unit_conf(self, unit);
    return systemctl_enabled_from(self, conf);
}

str_t 
systemctl_enabled_from(systemctl_t* self, systemctl_conf_t* conf)
{
    str_t unit_file = systemctl_conf_filename(conf);
    return "unknown";
}

/* ........................................................ */

int
str_list_print(str_list_t* result)
{
    for (int i = 0; i < result->size; ++i) {
        str_t element = result->data[i];
        fprintf(stdout, "%s\n", element);
    }
    return result->size ? 0 : 1;
}

int
str_list_list_print(str_list_list_t* result)
{
    for (int i = 0; i < result->size; ++i) {
        str_list_t* element = &result->data[i];
        str_t line = str_list_join(element, "\t");
        fprintf(stdout, "%s\n", line);
        str_free(line);
    }
    return result->size ? 0 : 1;
}

int 
main(int argc, char** argv)
{
    int returncode = 1;
    systemctl_settings_t settings;
    systemctl_settings_init(&settings);
    /* scan options */
    systemctl_options_t options;
    systemctl_options_init(&options);
    systemctl_options_add3(&options, "-v", "--verbose", "increase logging level");
    systemctl_options_scan(&options, argc, argv);
    /* ............................................ */
    systemctl_t systemctl;
    systemctl_init(&systemctl, &settings);
    
    if (argc > 1 && str_equal(argv[1], "list-units")) {
        str_list_t modules = str_list_NULL;
        str_list_init_from(&modules, argc - 2, argv + 2);
        str_list_list_t* result = systemctl_list_units(&systemctl, &modules);
        returncode = str_list_list_print(result);
        fprintf(stderr, "returncode %i", returncode);
        str_list_list_free(result);
        str_list_null(&modules);
    } else if (argc > 1 && str_equal(argv[1], "list-unit-files")) {
        str_list_t modules = str_list_NULL;
        str_list_init_from(&modules, argc - 2, argv + 2);
        str_list_list_t* result = systemctl_show_list_unit_files(&systemctl, &modules);
        returncode = str_list_list_print(result);
        fprintf(stderr, "returncode %i", returncode);
        str_list_list_free(result);
        str_list_null(&modules);
    } else {
        fprintf(stderr, "unknown command '%s'", argv[1]);
    }

    systemctl_null(&systemctl);
    systemctl_options_null(&options);
    return returncode;
}
