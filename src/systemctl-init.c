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
#include "systemctl-init-data.c"

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

/* defaults for options */
char** systemctl_extra_vars = { NULL };
bool systemctl_force = false;
bool systemctl_full = false;
bool systemctl_now = false;
bool systemctl_no_legend = false;
bool systemctl_no_ask_password = false;
char* systemctl_preset_mode = "all";
bool systemctl_quiet = false;
char* systemctl_root = "";
char* systemctl_unit_type = NULL;
char* systemctl_unit_state = NULL;
char* systemctl_unit_property = NULL;
// FIXME: bool systemctl_show_all = false;
// FIXME: bool systemctl_user_mode = false;

/* common default paths */
char* systemctl_default_target = "multi-user.target";
char* systemctl_system_folder1 = "/etc/systemd/system";
char* systemctl_system_folder2 = "/var/run/systemd/system";
char* systemctl_system_folder3 = "/usr/lib/systemd/system";
char* systemctl_system_folder4 = "/lib/systemd/system";
char* systemctl_system_folder9 = NULL;
char* systemctl_user_folder1 = "~/.config/systemd/user";
char* systemctl_user_folder2 = "/etc/systemd/user";
char* systemctl_user_folder3 = "~.local/share/systemd/user";
char* systemctl_user_folder4 = "/usr/lib/systemd/user";
char* systemctl_user_folder9 = NULL;
char* systemctl_init_folder1 = "/etc/init.d";
char* systemctl_init_folder2 = "/var/run/init.d";
char* systemctl_init_folder9 = NULL;
char* systemctl_preset_folder1 = "/etc/systemd/system-preset";
char* systemctl_preset_folder2 = "/var/run/systemd/system-preset";
char* systemctl_preset_folder3 = "/usr/lib/systemd/system-preset";
char* systemctl_preset_folder4 = "/lib/systemd/system-preset";
char* systemctl_preset_folder9 = NULL;

static int SystemCompatabilityVersion = 219;
static float MinimumYield = 0.5;
static int MinimumTimeoutStartSec = 4;
static int MinimumTimeoutStopSec = 4;
static int DefaultTimeoutStartSec = 90;
static int DefaultTimeoutStopSec = 90;
static int DefaultMaximumTimeout = 200;
static int InitLoopSleep = 5;
static int ProcMaxDepth = 100;
static int MaxLockWait = -1;
static char DefaultPath[] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/sbin:/bin";
static str_t ResetLocale_data[] = {
  "LANG", "LANGUAGE", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", 
  "LC_COLLATE", "LC_MONETARY", "LC_MESSAGES", "LC_PAPER", 
  "LC_NAME", "LC_ADDRESS", "LC_TELEPHONE", "LC_MEASUREMENT", 
  "LC_IDENTIFICATION", "LC_ALL" };
static str_list_t ResetLocale = { 15, ResetLocale_data };

char* systemctl_notify_socket_folder = "/var/run/systemd";
char* systemctl_pid_file_folder = "/var/run";
char* systemctl_journal_log_folder = "/var/log/journal";
char* systemctl_debug_log = "/var/log/systemctl.debug.log";
char* systemctl_extra_log = "/var/log/systemctl.log";

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
    if (values1) {
        str_list_adds(values1, value);
    } else {
        str_list_t* values = str_list_new();
        str_list_adds(values, value);
        str_list_dict_adds(options2, option, values);
    }
    if (value == NULL)
    {
        str_list_t* values2 = str_list_dict_get(options2, option);
        str_list_null(values2);
        str_list_init(values2);
    }
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
            /* logg "bad ini line" */
            goto done;
        }
        str_sets(&name, str_cut(line, m[1].rm_so, m[1].rm_eo));
        str_sets(&text, str_cut(line, m[2].rm_so, m[2].rm_eo));
        if (str_endswith(text, "\\") || str_endswith(text, "\\\n")) {
            nextline = true;
            str_sets(&text, str_dup2(text, "\n"));
        } else {
            /* hint: an empty line shall reset the value-list */
            if (! str_len(text)) 
                str_sets(&text, NULL);
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

/* ============================================================ */

typedef struct systemctl
{
    bool _no_legend;
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
systemctl_init(systemctl_t* self)
{
    self->_no_legend = false;
    self->_unit_state = NULL;
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
    str_null(&self->_unit_state);
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
   if (! str_empty(systemctl_preset_folder1)) 
       str_list_add(result, systemctl_preset_folder1);
   if (! str_empty(systemctl_preset_folder2)) 
       str_list_add(result, systemctl_preset_folder2);
   if (! str_empty(systemctl_preset_folder3)) 
       str_list_add(result, systemctl_preset_folder3);
   if (! str_empty(systemctl_preset_folder4)) 
       str_list_add(result, systemctl_preset_folder4);
   if (! str_empty(systemctl_preset_folder9)) 
       str_list_add(result, systemctl_preset_folder9);
   return result;
}

str_list_t* restrict
systemctl_init_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(systemctl_init_folder1)) 
       str_list_add(result, systemctl_init_folder1);
   if (! str_empty(systemctl_init_folder2)) 
       str_list_add(result, systemctl_init_folder2);
   if (! str_empty(systemctl_init_folder9)) 
       str_list_add(result, systemctl_init_folder9);
   return result;
}

str_list_t* restrict
systemctl_user_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(systemctl_user_folder1)) 
       str_list_add(result, systemctl_user_folder1);
   if (! str_empty(systemctl_user_folder2)) 
       str_list_add(result, systemctl_user_folder2);
   if (! str_empty(systemctl_user_folder3)) 
       str_list_add(result, systemctl_user_folder3);
   if (! str_empty(systemctl_user_folder4)) 
       str_list_add(result, systemctl_user_folder4);
   if (! str_empty(systemctl_user_folder9)) 
       str_list_add(result, systemctl_user_folder9);
   return result;
}

str_list_t* restrict
systemctl_system_folders(systemctl_t* self)
{
   str_list_t* result = str_list_new();
   if (! str_empty(systemctl_system_folder1)) 
       str_list_add(result, systemctl_system_folder1);
   if (! str_empty(systemctl_system_folder2)) 
       str_list_add(result, systemctl_system_folder2);
   if (! str_empty(systemctl_system_folder3)) 
       str_list_add(result, systemctl_system_folder3);
   if (! str_empty(systemctl_system_folder4)) 
       str_list_add(result, systemctl_system_folder4);
   if (! str_empty(systemctl_system_folder9)) 
       str_list_add(result, systemctl_system_folder9);
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
                    if (! str_cmp(module_suffix, item)) {
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

str_t restrict
systemctl_get_active_from(systemctl_t* self, systemctl_conf_t* conf)
{
    return NULL;
}

str_t restrict
systemctl_get_substate_from(systemctl_t* self, systemctl_conf_t* conf)
{
    return NULL;
}

str_t restrict
systemctl_get_description_from(systemctl_t* self, systemctl_conf_t* conf)
{
    return NULL;
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
             str_dict_add(&description, unit, systemctl_get_description_from(self, conf));
             str_dict_add(&active, unit, systemctl_get_active_from(self, conf));
             str_dict_add(&substate, unit, systemctl_get_substate_from(self, conf));
             if (self->_unit_state) {
                 if (! str_list3_contains(
                    str_dict_get(&result, unit),
                    str_dict_get(&active, unit),
                    str_dict_get(&substate, unit),
                    self->_unit_state)) {
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
    if (self->_no_legend) {
        return result;
    }
    str_t found = str_format("%i loaded units listed", str_list_list_len(result));
    str_list_list_add3(result, "", found, hint);
    str_free(found);
    return result;
}

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
    systemctl_t systemctl;
    systemctl_init(&systemctl);
    
    if (argc > 1 && !str_cmp(argv[1], "list-units")) {
        str_list_t modules = str_list_NULL;
        str_list_init_from(&modules, argc - 2, argv + 2);
        str_list_list_t* result = systemctl_list_units(&systemctl, &modules);
        returncode = str_list_list_print(result);
        fprintf(stderr, "returncode %i", returncode);
        str_list_list_free(result);
        str_list_null(&modules);
    } else {
        fprintf(stderr, "unknown command '%s'", argv[1]);
    }

    systemctl_null(&systemctl);
    return returncode;
}
