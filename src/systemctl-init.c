/*
 * This implementation follows the structure of systemctl.py very closely.
 * In that way it is possible to do debugging in python transposing the
 * the solutions into C code after that.
 */

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <regex.h>
#include <fnmatch.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <pwd.h>
#include <grp.h>
#include "systemctl-types.h"
#include "systemctl-shlex.h"
#include "systemctl-regex.h"
#include "systemctl-options.h"
#include "systemctl-logging.h"
#include "systemctl-shlex.h"
#include "systemctl-init.h"

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

double EpsilonTime = 0.1;

#define ERROR1 1
#define ERROR3 3

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
    self->init = false;
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
shell_cmd(str_list_t* cmd)
{
   str_t res = str_dup("");
   for (int i=0; i < cmd->size; ++i) {
       if (res[0]) 
           str_append(&res, " ");
       str_appends(&res, str_to_json(cmd->data[i]));
   }
   ssize_t len = str_len(res);
   return res;
}


str_t restrict
unit_of(str_t module)
{
    if (! strchr(module, '.')) {
        return str_dup2(module, ".service");
    }
    return str_dup(module);
}

str_t restrict
os_path(str_t root, str_t path)
{
    if (! root)
        return str_dup(path);
    if (! path)
        return path;
    char* path2 = path;
    while (*path2 && *path2 == '/') path2++;
    return str_dup3(root, "/", path2);
}

str_t /* not free */
os_getlogin_p()
{
    struct passwd* pwd = getpwuid(geteuid());
    return pwd->pw_name;
}

str_t restrict
os_getlogin()
{
    return str_dup(os_getlogin_p());
}

str_t restrict
get_runtime_dir()
{
    char* explicit = getenv("XDG_RUNTIME_DIR");
    if (explicit) return str_dup(explicit);
    str_t user = os_getlogin_p();
    return str_dup2("/tmp/run-", user);
}

str_t restrict
get_home()
{
    char* explicit = getenv("HOME");
    if (explicit) return str_dup(explicit);
    struct passwd* pwd = getpwuid(geteuid());
    return str_dup(pwd->pw_dir);
}

static str_t restrict
_var_path(str_t path)
{
    /* assumes that the path starts with /var - when in 
        user mode it shall be moved to /run/user/1001/run/
        or as a fallback path to /tmp/run-{user}/ so that
        you may find /var/log in /tmp/run-{user}/log .. */
    if (str_startswith(path, "/var")) {
        str_t runtime = get_runtime_dir(); /* $XDG_RUNTIME_DIR */
        if (! os_path_isdir(runtime)) {
            os_makedirs(runtime);
            os_chmod(runtime, 0700);
        }
        str_t res = str_dup2(runtime, path+4);
        str_free(runtime);
        return res;
    }
    return str_dup(path);
}

str_t restrict
os_environ_get(const char* name, str_t restrict defaults)
{
    char* explicit = getenv("HOME");
    if (explicit) return str_dup(explicit);
    return defaults;
}

str_dict_t* restrict
shutil_setuid(str_t user, str_t group)
{
    str_dict_t* res = str_dict_new();
    if (! str_empty(group)) {
        struct group* gr = getgrnam(group);
        gid_t gid = gr->gr_gid;
        setgid(gid);
        logg_debug("setgid %lu '%s'", (unsigned long) gid, group);
    }
    if (! str_empty(user)) {
        struct passwd* pw = getpwnam(user);
        if (! group) {
            gid_t gid = pw->pw_gid;
            setgid(gid);
            logg_debug("setgid %lu", (unsigned long) gid);
        }
        uid_t uid = pw->pw_uid;
        setuid(uid);
        logg_debug("setuid %lu '%s'", (unsigned long) uid, user);
        str_t home = pw->pw_dir;
        str_t shell = pw->pw_shell;
        str_t logname = pw->pw_name;
        str_dict_add(res, "USER", user);
        str_dict_add(res, "LOGNAME", logname);
        str_dict_add(res, "HOME", home);
        str_dict_add(res, "SHELL", shell);
    }
    return res;
}

str_t
checkstatus_cmd(str_t value) 
{
   if (!value) return value;
   if (*value == '-') return value+1;
   return value;
}

bool
checkstatus_do(str_t value)
{
   if (!value) return value;
   if (*value == '-') return false;
   return true;
}

typedef struct systemctl_subprocess
{
    int pid;
    int returncode;
    int signal;
} systemctl_subprocess_t;

typedef systemctl_subprocess_t run_t;

int
subprocess_waitpid(int pid, systemctl_subprocess_t* res)
{
    int run_stat = 0;
    int run_pid = waitpid(pid, &run_stat, 0);
    if (res) {
        res->pid = run_pid;
        res->returncode =  WEXITSTATUS(run_stat);
        res->signal = WTERMSIG(run_stat);
    }
    return run_stat;
}

int
subprocess_testpid(int pid, systemctl_subprocess_t* res)
{
    int run_stat = 0;
    int run_pid = waitpid(pid, &run_stat, WNOHANG);
    if (res && run_pid) {
        res->pid = run_pid;
        res->returncode =  WEXITSTATUS(run_stat);
        res->signal = WTERMSIG(run_stat);
    } else if (res) {
        res->pid = pid;
        res->returncode = EOF;
        res->signal = 0;
    }
    return run_stat;
}

/* .............................. */
static str_t _tmp_shell_cmd = str_NULL;

str_t
tmp_shell_cmd(str_list_t* cmd)
{
    str_sets(&_tmp_shell_cmd, shell_cmd(cmd));
    return _tmp_shell_cmd;
}

static str_t _tmp_unit_of = str_NULL;

str_t
tmp_unit_of(str_t cmd)
{
    str_sets(&_tmp_unit_of, unit_of(cmd));
    return _tmp_unit_of;
}

static str_t _tmp_int_or = str_NULL;

str_t
tmp_int_or(int val, str_t defaults)
{
    if (val) {
       str_sets(&_tmp_int_or, str_format("%i", val));
    } else {
       str_sets(&_tmp_int_or, str_dup(defaults));
    }
    return _tmp_int_or;
}

static str_t _tmp_int_or_no = str_NULL;

str_t
tmp_int_or_no(int val)
{
    if (val) {
       str_sets(&_tmp_int_or_no, str_format("%i", val));
    } else {
       str_sets(&_tmp_int_or_no, str_dup(""));
    }
    return _tmp_int_or_no;
}

void
tmp_null()
{
   str_null(&_tmp_shell_cmd);
   str_null(&_tmp_unit_of);
   str_null(&_tmp_int_or);
   str_null(&_tmp_int_or_no);
}

/* .............................. */

struct systemctl_conf_data
{
    str_list_dict_dict_t defaults;
    str_list_dict_dict_t conf;
    str_list_t files;
};


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
    str_t text = NULL;
    FILE* fd = fopen(filename, "r");
    if (fd == NULL) return false;
    str_t name = str_dup("");
    str_list_add(&self->files, filename);
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
            str_t includefile = str_strips(str_dup(line + sizeof(".include")));
            FILE* fd2 = fopen(includefile, "r");
            if (fd2 == NULL) continue;
            fclose(fd2);
            systemctl_conf_data_read_sysd(self, includefile);
            str_null(&includefile);
            continue;
        }
        if (str_startswith(line, "[")) {
            ssize_t x = str_find(line, ']');
            if (x > 0) {
                str_sets(&section, str_cut(line, 1, x));
                systemctl_conf_data_add_section(self, section);
            }
            continue;
        }
        if (regmatch("([[:alnum:]_]+) *=(.*)", line, m3, m, 0)) {
            logg_error("bad ini line: '%s'", line);
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
                if (! regmatch("\\S+\\s*([[:alnum:]][[:alnum:]_-]*):(.*)", line, m3, m, 0)) {
                    str_t key = str_strips(str_cut(line, m[1].rm_so, m[1].rm_eo));
                    str_t val = str_strips(str_cut(line, m[1].rm_so, m[1].rm_eo));
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

struct systemctl_conf
{
    systemctl_conf_data_t data;
    str_dict_t* env;
    str_dict_t* status;
    str_t masked;
    str_t module;
    str_dict_t drop_in_files;
    str_t name;
    str_t root;
    bool user_mode;
};

void 
systemctl_conf_init(systemctl_conf_t* self)
{
    systemctl_conf_data_init(&self->data);
    self->env = NULL;
    self->status = NULL;
    str_init(&self->masked);
    str_init(&self->module);
    str_dict_init(&self->drop_in_files);
    str_init(&self->name); /* TODO: helper only in C/C++ */
    str_init(&self->root);
    self->user_mode = false;
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
    str_dict_free(self->env);
    str_dict_free(self->status);
    str_null(&self->masked);
    str_null(&self->module);
    str_dict_null(&self->drop_in_files);
    str_null(&self->name);
    str_null(&self->root);
}

void
systemctl_conf_free(systemctl_conf_t* self)
{
    systemctl_conf_null(self);
    free(self);
}

str_t restrict
systemctl_conf_os_path(systemctl_conf_t* self, str_t path)
{
    return os_path(self->root, path);
}

str_t restrict
systemctl_conf_os_path_var(systemctl_conf_t* self, str_t path)
{
    if (self->user_mode) {
       str_t var_path = _var_path(path);
       str_t res = os_path(self->root, var_path);
       str_free(var_path);
       return res;
    }
    return os_path(self->root, path);
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

str_t restrict
systemctl_conf_name(systemctl_conf_t* self)
{
    str_t name;
    str_init(&name);
    if (! str_empty(self->module)) {
        str_set(&name, self->module);
    }
    str_t filename = systemctl_conf_filename(self);
    if (! str_empty(filename)) {
        str_sets(&name, os_path_basename(filename));
    }
    str_set(&name, systemctl_conf_get(self, "Unit", "Id", name));
    return name;
}

str_t /* do not str_free this */
systemctl_name(systemctl_conf_t* self) 
{
    if (str_empty(self->name)) {
       str_set(&self->name, systemctl_conf_name(self));
    }
    return self->name;
}

/* ============================================================ */
#define ERROR_FAILED 3
#define ERROR_FALSE 1

struct systemctl
{
    systemctl_settings_t use;
    str_t _unit_state;
    ptr_dict_t loaded_file_sysv; /* /etc/init.d/name => conf */
    ptr_dict_t loaded_file_sysd; /* /etc/systemd/system/name.service => conf */
    ptr_dict_t not_loaded_confs; /* name.service => conf */
    str_dict_t file_for_unit_sysv; /* name.service => /etc/init.d/name */
    str_dict_t file_for_unit_sysd; /* name.service => /etc/systemd/system/name.service */
    str_dict_t drop_in_files;
    /* FIXME: the loaded-conf is a mixture of parts from multiple files */
    bool user_mode;
    str_t current_user;
    int error; /* program exitcode or process returncode */
    str_t root;
    str_dict_t root_paths; /* TODO: special optimization for StdC */
    str_list_t extra_vars;
    str_t tmp;
};

void
systemctl_init(systemctl_t* self, systemctl_settings_t* settings)
{
    self->use = *settings;
    ptr_dict_init(&self->loaded_file_sysv, (free_func_t) systemctl_conf_free);
    ptr_dict_init(&self->loaded_file_sysd, (free_func_t) systemctl_conf_free);
    ptr_dict_init(&self->not_loaded_confs, (free_func_t) systemctl_conf_free);
    str_dict_init(&self->file_for_unit_sysv);
    str_dict_init(&self->file_for_unit_sysd);
    str_dict_init(&self->drop_in_files);
    self->user_mode = false;
    str_init(&self->current_user);
    self->error = 0;
    self->root = str_dup(settings->root);
    str_dict_init(&self->root_paths);
    str_list_init(&self->extra_vars);
    str_init(&self->tmp);
}

void
systemctl_null(systemctl_t* self)
{
    str_dict_null(&self->file_for_unit_sysd);
    str_dict_null(&self->file_for_unit_sysv);
    ptr_dict_null(&self->not_loaded_confs);
    ptr_dict_null(&self->loaded_file_sysv);
    ptr_dict_null(&self->loaded_file_sysd);
    str_dict_null(&self->drop_in_files);
    str_null(&self->current_user);
    str_null(&self->root);
    str_dict_null(&self->root_paths);
    str_list_null(&self->extra_vars);
    str_null(&self->tmp);
}


str_t
str_or(int value, str_t defaults)
{
}

str_t /* no free here */
systemctl_root(systemctl_t* self, str_t path)
{
    if (! self->root || ! self->root[0]) 
        return path;
    /* we assume that if root is set then it will not change later */
    if (! str_dict_contains(&self->root_paths, path)) {
        str_t root_path = str_dup2(self->root, path);
        str_dict_adds(&self->root_paths, path, root_path);
    }
    return str_dict_get(&self->root_paths, path);
}

str_t
systemctl_current_user(systemctl_t* self)
{
    if (str_empty(self->current_user)) 
        str_sets(&self->current_user, os_getlogin());
    return self->current_user;
}

bool
systemctl_user_mode(systemctl_t* self)
{
    return self->user_mode;
}

str_t restrict
systemctl_user_folder(systemctl_t* self)
{
    str_t result = str_NULL;
    str_list_t* folders = systemctl_user_folders(self);
    for (int i=0; i < folders->size; ++i) {
         if (folders->data[i]) {
             result = str_dup(folders->data[i]);
             str_list_free(folders);
             return result;
         }
    }
    str_list_free(folders);
    logg_error("did not find any systemd/user folder");
    return result;
}

str_list_t* restrict
systemctl_system_folders(systemctl_t* self);
str_t restrict
systemctl_system_folder(systemctl_t* self)
{
    str_t result = str_NULL;
    str_list_t* folders = systemctl_system_folders(self);
    for (int i=0; i < folders->size; ++i) {
         if (folders->data[i]) {
             result = str_dup(folders->data[i]);
             str_list_free(folders);
             return result;
         }
    }
    str_list_free(folders);
    logg_error("did not find any systemd/user folder");
    return result;
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
       str_t folder = str_NULL;
       for (int i=0; i < folders->size; ++i) {
           str_sets(&folder, os_path(self->root, folders->data[i]));
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
                 // logg_info("found %s => %s", name, path);
                 str_dict_adds(&self->file_for_unit_sysd, name, path);
              } else {
                 str_free(path);
              }
           }
           str_list_free(names);
       }
       str_null(&folder);
       str_list_free(folders);
   }
   logg_debug("found %i sysd files", str_dict_len(&self->file_for_unit_sysd));
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
                 // logg_info("found %s => %s", name2, path);
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


bool
systemctl_is_user_conf(systemctl_t* self, systemctl_conf_t* conf)
{
    if (conf == NULL)
        return false;
    str_t filename = systemctl_conf_filename(conf);
    if (! str_empty(filename) && str_contains(filename, "/user/")) {
        return true;
    } 
    return false;
}

bool
systemctl_not_user_conf(systemctl_t* self, systemctl_conf_t* conf)
{
    if (! conf) 
        return true;
    if (! systemctl_user_mode(self)) {
        logg_debug("%s no --user mode >> accept", systemctl_name(conf));
        return false;
    }
    if (systemctl_is_user_conf(self, conf)) {
        logg_debug("%s is /user/ conf >> accept", systemctl_name(conf));
        return false;
    }
    /* to allow for 'docker run -u user' with system services */
    str_t user = systemctl_expand_special(self, systemctl_conf_get(conf, "Service", "User", ""), conf);
    if (! str_empty(user) && str_equal(user, systemctl_current_user(self))) {
        logg_debug("%s with User=%s >> accept", systemctl_name(conf), user);
        str_free(user);
        return false;
    }
    str_free(user);
    return true;
}

str_dict_t* restrict
systemctl_find_drop_in_files(systemctl_t* self, str_t unit)
{
    str_dict_t* result = str_dict_new();
    str_list_t* folders = systemctl_sysd_folders(self);
    str_t folder = str_NULL;
    for (int i=0; i < folders->size; ++i) {
        str_set(&folder, folders->data[i]);
        if (str_empty(folder))
            continue;
        if (self->root) 
            os_path_prepend(&folder, self->root);
        os_path_append(&folder, unit); str_append(&folder, ".d");
        if (! os_path_isdir(folder))
            continue;
        str_list_t* names = os_path_listdir(folder);
        for (int j=0; j < names->size; ++j) {
            str_t name = names->data[j];
            str_t path = os_path_join(folder, name);
            if (os_path_isdir(path)) {
                /* continue */
            } else if (! str_endswith(path, ".conf")) {
                /* continue */
            } else if (! str_dict_contains(result, path)) {
                str_dict_adds(result, name, path); path = str_NULL;
            }
            str_null(&path);
        }
        str_list_free(names);
    }
    str_null(&folder);
    str_list_free(folders);
    return result;
}

systemctl_conf_t* 
systemctl_load_sysd_unit_conf(systemctl_t* self, str_t module)
{
    str_t path = systemctl_unit_sysd_file(self, module);
    if (str_empty(path)) return NULL;
    if (ptr_dict_contains(&self->loaded_file_sysd, path)) {
        return ptr_dict_get(&self->loaded_file_sysd, path);
    }
    str_t masked = str_NULL;
    if (os_path_islink(path)) {
       str_t link = os_path_readlink(path);
       if (str_startswith(link, "/dev")) {
          str_sets(&masked, link); link = str_NULL;
       }
       str_null(&link);
    }
    /* TODO: python has a different allocation order */
    systemctl_conf_t* conf = systemctl_conf_new();
    if (str_empty(masked)) {
        systemctl_conf_data_read_sysd(&conf->data, path);
        str_dict_sets(&conf->drop_in_files, 
            systemctl_find_drop_in_files(self, os_path_basename_p(path)));
        /* load in alphabetic order, irrespective of location */
        for (int k=0; k < self->drop_in_files.size; ++k) {
            str_t drop_in_file = self->drop_in_files.data[k].value;
            systemctl_conf_data_read_sysd(&conf->data, drop_in_file);
        }
    }
    str_sets(&conf->masked, masked); masked = str_NULL;
    str_set(&conf->module, module);
    str_set(&conf->root, self->root);
    conf->user_mode = self->user_mode;
    ptr_dict_adds(&self->loaded_file_sysd, path, conf);
    return conf;

}

bool
systemctl_is_sysv_file(systemctl_t* self, str_t filename)
{
    if (filename == NULL) return false;
    systemctl_unit_file(self, NULL);
    for (int d=0; d < self->file_for_unit_sysd.size; ++d) {
       str_t value = self->file_for_unit_sysd.data[d].value;
       if (str_equal(value, filename)) return false;
    }
    for (int d=0; d < self->file_for_unit_sysv.size; ++d) {
       str_t value = self->file_for_unit_sysv.data[d].value;
       if (str_equal(value, filename)) return true;
    }
    return false;
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
    str_set(&conf->module, module);
    str_set(&conf->root, self->root);
    conf->user_mode = self->user_mode;
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
    str_set(&conf->root, self->root);
    conf->user_mode = self->user_mode;
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
                if (! fnmatch(module, item, 0)) {
                   str_list_add(result, item);
                } else {
                    str_t module_suffix = str_dup2(module, ".service");
                    if (str_equal(module_suffix, item)) {
                        str_list_add(result, item);
                    }
                    str_free(module_suffix);
                }
            }
        }
    }
    if (false) 
      logg_info("matched %i units (limited by %i args, e.g. '%s')", 
        str_list_len(result), str_list_len(modules), modules->size ? modules->data[0]: "");
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
        if (str_list_contains(found, sysv->data[i])) {
            str_list_adds(found, sysv->data[i]);
            sysd->data[i] = NULL;
        }
    }
    str_list_free(sysv);
    return found;
}

str_list_t* restrict
systemctl_match_unit(systemctl_t* self, str_t module) 
{
   str_t data[] = { module };
   str_list_t match = { 1, data };
   return systemctl_match_units(self, &match);
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
    str_t json = str_list_list_to_json(result);
    logg_debug("systemctl_list_units: %s", json);
    str_free(json);
    return result;
}

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

str_dict_t* restrict
systemctl_each_target_file(systemctl_t* self)
{
    str_dict_t* result = str_dict_new();
    str_list_t* folders = NULL; 
    if (systemctl_user_mode(self)) {
        folders = systemctl_user_folders(self);
    } else {
        folders = systemctl_system_folders(self);
    }
    for (int i=0; i < folders->size; ++i) {
        str_t folder = folders->data[i];
        if (! os_path_isdir(folder))
            continue;
        str_list_t* filenames = os_path_listdir(folder);
        for (int k=0; k < filenames->size; ++k) {
            str_t filename = filenames->data[k];
            if (str_endswith(filename, ".target"))
                str_dict_adds(result, filename, os_path_join(folder, filename));
        }
        str_list_free(filenames);
    }
    str_list_free(folders);
    return result;
}

str_list_list_t*
systemctl_list_target_unit_files(systemctl_t* self, str_list_t* modules) 
{
    str_list_list_t* result = str_list_list_new();
    str_dict_t enabled = str_dict_NULL;
    str_dict_t targets = str_dict_NULL;
    str_dict_t* target_files = systemctl_each_target_file(self);
    for (int i=0; i < target_files->size; ++i) {
        str_t target = target_files->data[i].key;
        str_t filepath = target_files->data[i].value;
        logg_info("target %s", filepath);
        str_dict_add(&targets, target, filepath);
        str_dict_add(&enabled, target, "static");
    }
    // TODO: add all_common_targets
    str_dict_free(target_files);
    for (int i=0; i < targets.size; ++i) {
        str_t unit = targets.data[i].key;
        str_list_t* line = str_list_new();
        str_list_adds(line, str_dup(unit));
        str_list_adds(line, str_dup(str_dict_get(&enabled, unit)));
        str_list_list_adds(result, line);
    }
    str_dict_null(&targets);
    str_dict_null(&enabled);
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
        logg_error("unsupported unit --type=%s", self->use.unit_type);
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

int
systemctl_read_pid_file(systemctl_t* self, str_t pid_file)
{
    // TODO: FIXME: python version should always return an integer
    int pid = -1;
    if (! pid_file)
        return pid;
    if (! os_path_isfile(pid_file))
        return pid;
    if (systemctl_truncate_old(self, pid_file))
        return pid;
    FILE* fd = fopen(pid_file, "r");
    str_t orig_line = NULL;
    str_t line = NULL;
    while(true) {
        if (orig_line) free(orig_line);
        orig_line = NULL; /* allocate as needed */
        size_t maxlen = 0; /* when both are null */
        ssize_t len = getline(&orig_line, &maxlen, fd);
        if (len <= 0) break;
        str_sets(&line, str_strip(orig_line));
        if (! str_empty(line)) {
            /* pid = to_int(line); */
            /* TODO: what about the remainder */
            errno = 0;
            int found_pid = strtoul(line, NULL, 10);
            if (! errno) {
                pid = found_pid;
                break;
            }
        }
    }
    fclose(fd);
    if (orig_line) free (orig_line);
    return pid;
}

str_t
systemctl_get_status_file(systemctl_t* self, str_t unit)
{
    systemctl_conf_t* conf = systemctl_get_unit_conf(self, unit);
    return systemctl_status_file_from(self, conf);
}

str_t
systemctl_status_file_from(systemctl_t* self, systemctl_conf_t* conf)
{
    str_t defaults = systemctl_default_status_file(self, conf);
    if (! conf) return defaults;
    str_t status_file = systemctl_conf_get(conf, "Service", "StatusFile", defaults);
    /* this is not a real setting, but do the expand_special anyway */
    str_t res = systemctl_expand_special(self, status_file, conf);
    str_free(status_file);
    str_free(defaults);
    return res;
}

str_t
systemctl_default_status_file(systemctl_t* self, systemctl_conf_t* conf)
{
    str_t folder = systemctl_conf_os_path_var(conf, self->use.pid_file_folder);
    str_t name = systemctl_conf_name(conf);
    str_append(&name, ".status");
    str_t res = os_path(folder, name);
    str_free(name);
    str_free(folder);
    return res;
}

void
systemctl_clean_status_from(systemctl_t* self, systemctl_conf_t* conf)
{
    str_t status_file = systemctl_status_file_from(self, conf);
    if (os_path_exists(status_file))
        unlink(status_file);
    str_dict_free(conf->status);
    conf->status = NULL;
    str_free(status_file);
}

bool
systemctl_write_status_from(systemctl_t* self, systemctl_conf_t* conf, str_t key, str_t value)
{
    str_t status_file = systemctl_status_file_from(self, conf);
    if (! status_file) {
        logg_debug("status %s but no status_file", systemctl_conf_filename(conf));
        return false;
    }
    str_t dirpath = os_path_abspath_dirname(status_file);
    if (! os_path_isdir(dirpath))
        os_makedirs(dirpath);
    if (! conf->status) {
        conf->status = systemctl_read_status_from(self, conf);
    }
    if (true) {
        if (key) {
            if (! value) {
               str_dict_del(conf->status, key);
            } else {
               str_dict_add(conf->status, key, value);
            }
        }
    }
    if (true) {
       int f = open(status_file, O_WRONLY|O_CREAT, 0644);
       for (int k=0; k < conf->status->size; ++k) {
          str_t key = conf->status->data[k].key;
          str_t value = conf->status->data[k].value;
          if (str_equal(key, "MainPID") && str_equal(value, "0")) {
              logg_warning("ignore writing MainPID=0");
              continue;
          }
          str_t content = str_format("%s=%s", key, value);
          logg_debug("writing to %s\n\t%s", status_file, content);
          write(f, content, strlen(content));
          str_free(content);
       }
    }
    return true;
}

str_dict_t* restrict
systemctl_read_status_from(systemctl_t* self, systemctl_conf_t* conf)
{
    str_dict_t* status = str_dict_new();
    str_t status_file = systemctl_status_file_from(self, conf);
    if (! status_file) {
        logg_debug("no status file. returning");
        return status;
    }
    if (! os_path_isfile(status_file)) {
        logg_debug("no status file: %s\n returning", status_file);
        str_free(status_file);
        return status;
    }
    if (systemctl_truncate_old(self, status_file)) {
        logg_debug("old status file: %s\n returning", status_file);
        str_free(status_file);
        return status;
    }
    FILE* fd = fopen(status_file, "r");
    if (fd) {
        while (true) {
            str_t line = NULL;
            size_t size = 0;
            ssize_t len = getline(&line, &size, fd);
            if (len < 0) break; /* EOF */
            int m = str_find(line, '=');
            if (m) {
                str_t key = str_strips(str_cut(line, 0, m));
                str_t value = str_strips(str_cut_end(line, m+1));
                str_dict_adds(conf->status, key, value);
                str_free(key);
            } else {
                str_t value = str_strip(line);
                str_dict_adds(conf->status, "ActiveState", value);
            }
            free(line);
        } /* while not EOF */
        fclose(fd);
    } else {
        logg_warning("bad read of status file '%s': %s", status_file, strerror(errno));
    }
    str_free(status_file);
    return status;
}

double
systemctl_get_boottime(systemctl_t* self)
{
    double ctime = 0.;
    for (int pid=0; pid < 10; ++pid) {
        str_t proc = str_format("/proc/%i/status", pid);
        if (os_path_isfile(proc)) {
            /* FIXME: may be we should take the getctime ? */
            ctime = os_path_getmtime(proc);
            if (! ctime) {
                logg_warning("could not access %s: %s", proc, strerror(errno));
            }
        }
        str_free(proc);
        if (ctime) 
            return ctime;
    }
    return systemctl_get_boottime_oldest(self);
}

double
systemctl_get_boottime_oldest(systemctl_t* self)
{
    /* otherwise get the oldest entry in /proc */
    double booted = os_clock_gettime();
    str_list_t* filenames = os_path_listdir("/proc");
    for (int i=0; i < filenames->size; ++i) {
        str_t name = filenames->data[i];
        str_t proc = str_format("/proc/%s/status", name);
        if (os_path_isfile(proc)) {
            /* FIXME: may be we should take the getctime ? */
            double ctime = os_path_getmtime(proc);
            if (! ctime) {
                logg_warning("could not access %s: %s", proc, strerror(errno));
            } else if (ctime < booted) {
                booted = ctime;
            }
        }
        str_free(proc);
    }
    str_list_free(filenames);
    return 0.;
}

double
systemctl_get_filetime(systemctl_t* self, str_t filename)
{
    return os_path_getmtime(filename);
}

bool
systemctl_truncate_old(systemctl_t* self, str_t filename)
{
    double filetime = systemctl_get_filetime(self, filename);
    double boottime = systemctl_get_boottime(self);
    filetime -= EpsilonTime;
    if (filetime >= boottime) {
        logg_debug("  file time: %f", os_clock_localtime10(filetime));
        logg_debug("  boot time: %f", os_clock_localtime10(boottime));
        return false; /* OK */
    }
    logg_info("truncate old %s", filename);
    logg_info("  file time: %f", os_clock_localtime10(filetime));
    logg_info("  boot time: %f", os_clock_localtime10(boottime));
    os_path_truncate(filename);
    return true;
}

off_t
systemctl_getsize(systemctl_t* self, str_t filename)
{
    if (! filename) 
        return 0;
    if (! os_path_isfile(filename))
        return 0;
    if (systemctl_truncate_old(self, filename))
        return 0;
    return os_path_getsize(filename);
}

/* ........................................... */

str_dict_t* restrict
systemctl_read_env_file(systemctl_t* self, str_t env_file)
{
    str_dict_t* result = str_dict_new();
    if (str_startswith(env_file, "-")) {
        env_file ++;
        if (! os_path_isfile(systemctl_root(self, env_file)))
            return result;
    }
    FILE* fd = fopen(systemctl_root(self, env_file), "r");
    if (fd == NULL) return false;
    str_t orig_line = NULL;
    str_t line = NULL;
    while(true) {
        str_sets(&orig_line, NULL);
        size_t maxlen = 0; /* when both are null */
        ssize_t len = getline(&orig_line, &maxlen, fd);
        if (len <= 0) break;
        str_sets(&line, str_strip(orig_line));
        if (str_empty(line) || str_startswith(line, "#"))
            continue;
        regmatch_t m[4];
        size_t m3 = 3;
        if (!regmatch("(?:export +)?([[:alnum:]_]+)[=]'([^']*)'", line, m3, m, 0)) {
            str_t key = str_cut(line, m[1].rm_so, m[1].rm_eo);
            str_t val = str_cut(line, m[1].rm_so, m[1].rm_eo);
            str_dict_adds(result, key, val);
            str_free(key);
            continue;
        }
        if (!regmatch("(?:export +)?([[:alnum:]_]+)[=]\"([^\"]*)\"", line, m3, m, 0)) {
            str_t key = str_cut(line, m[1].rm_so, m[1].rm_eo);
            str_t val = str_cut(line, m[2].rm_so, m[2].rm_eo);
            str_dict_adds(result, key, val);
            str_free(key);
            continue;
        }
        if (!regmatch("(?:export +)?([[:alnum:]_]+)[=](.*)", line, m3, m, 0)) {
            str_t key = str_cut(line, m[1].rm_so, m[1].rm_eo);
            str_t val = str_cut(line, m[2].rm_so, m[2].rm_eo);
            str_dict_adds(result, key, val);
            str_free(key);
            continue;
        }
    }        
    fclose(fd);
    str_null(&orig_line);
    str_null(&line);
    return result;
}

str_dict_t* restrict
systemctl_read_env_part(systemctl_t* self, str_t env_part)
{
    str_dict_t* result = str_dict_new();
    str_list_t* lines = str_split(env_part, '\n');
    for (int i=0; i < lines->size; ++i) {
        str_t real_line = str_strip(lines->data[i]);
        str_t line = real_line;
        regmatch_t m[4];
        size_t m3 = 3;
        while (! regmatch("\\s*(\"[[:alnum:]_]+=[^\"]*\"|[[:alnum:]_]+=\\S*)", line, m3, m, 0)) {
            str_t part = str_cut(line, m[1].rm_so, m[1].rm_eo);
            if (str_startswith(part, "\"")) {
                 str_sets(&part, str_cut(part, 1, -1));
            }
            int x = str_find(part, '='); /* there is surely a '=' in there */
            str_t name = str_cut(part, 0, x);
            str_t value = str_cut_end(part, x+1);
            str_dict_adds(result, name, value);
            str_free(name);
            str_free(part);
            line = line + m[1].rm_eo; /* step */
        }
        str_free(real_line);
    }
    str_list_free(lines);
    return result;
}

str_dict_t* restrict
systemctl_get_env(systemctl_t* self, systemctl_conf_t* conf)
{
    str_dict_t* env = os_environ_copy();
    str_list_t* env_parts = systemctl_conf_getlist(conf, "Service", "Environment", &empty_str_list);
    for (int i=0; i < env_parts->size; ++i) {
        str_t env_part = systemctl_expand_special(self, env_parts->data[i], conf);
        str_dict_t* values = systemctl_read_env_part(self, env_part);
        for (int j=0; j < values->size; ++j) {
             str_t name = values->data[j].key;
             str_t value = values->data[j].value;
             str_dict_add(env, name, value); /* a '$word' is not special here */
        }
        str_free(env_part);
        str_dict_free(values);
    }
    str_list_t* env_files = systemctl_conf_getlist(conf, "Service", "EnvironmentFile", &empty_str_list);
    for (int i=0; i < env_files->size; ++i) {
        str_t env_file = systemctl_expand_special(self, env_files->data[i], conf);
        str_dict_t* values = systemctl_read_env_file(self, env_file);
        for (int j=0; j < values->size; ++j) {
             str_t name = values->data[j].key;
             str_t value = values->data[j].value;
             str_dict_adds(env, name, systemctl_expand_env(self, value, env));
        }
        str_free(env_file);
        str_dict_free(values);
    }
    for (int k=0; k < self->extra_vars.size; ++k) {
        str_t extra = self->extra_vars.data[k];
        if (str_startswith(extra, "@")) {
            str_dict_t* values = systemctl_read_env_file(self, extra+1);
            for (int j=0; j < values->size; ++j) {
                str_t name = values->data[j].key;
                str_t value = values->data[j].value;
                logg_debug("override %s=%s", name, value);
                str_dict_add(env, name, systemctl_expand_env(self, value, env));
            }
            str_dict_free(values);
        } else {
            str_dict_t* values = systemctl_read_env_part(self, extra);
            for (int j=0; j < values->size; ++j) {
                str_t name = values->data[j].key;
                str_t value = values->data[j].value;
                logg_debug("override %s=%s", name, value);
                str_dict_add(env, name, value); /* a '$word' is not special here */
            }
            str_dict_free(values);
       }
    }
    return env;
}

str_dict_t* restrict
systemctl_show_environment(systemctl_t* self, str_t unit)
{
    systemctl_conf_t* conf = systemctl_load_unit_conf(self, unit);
    if (! conf) {
        logg_error("Unit %s could not be found", unit);
        return NULL;
    }
    /* TODO: _unit_property */
    return systemctl_get_env(self, conf);
}

str_t restrict
str_expand(str_t regex, str_t value, str_dict_t* env)
{
    regmatch_t m[4];
    size_t m3 = 3;
    ssize_t p = 0;
    str_t expanded = str_NULL;
    str_t matching = value;
    while (! regmatch(regex, matching+p, m3, m, 0)) {
        str_t key = str_cut(matching+p, m[1].rm_so, m[1].rm_eo);
        if (! str_dict_contains(env, key)) {
            logg_debug("can not expand $%s", key);
            p += m[1].rm_eo;
        } else {
            str_t value = str_dict_get(env, key);
            ssize_t old_len = str_len(key);
            ssize_t new_len = str_len(value);
            str_t prefix = str_cut(matching, 0, p + m[1].rm_so);
            str_t suffix = str_cut_end(matching, p + m[1].rm_eo);
            str_sets(&expanded, str_dup3(prefix, value, suffix));
            str_free(suffix);
            str_free(prefix);
            p += m[1].rm_eo - old_len + new_len;
            matching = expanded;
        }
        str_free(key);
    }
    return expanded; /* my be null */
}

str_t restrict
str_expand_env1(str_t value, str_dict_t* env)
{
    return str_expand(".*[$]([[:alnum:]_]+)", value, env);
}

str_t restrict
str_expand_env2(str_t value, str_dict_t* env)
{
    return str_expand(".*[$][{]([[:alnum:]_]+)[}]", value, env);
}

str_t restrict
systemctl_expand_env(systemctl_t* self, str_t value, str_dict_t* env)
{
    str_t expanded = str_replace(value, "\\\\n", "");
    const int maxdepth = 20;
    for(int depth = 0; depth < maxdepth; ++depth) {
        regmatch_t m[4];
        size_t m3 = 3;
        ssize_t p = 0;
        int done = 0;
        str_t expanded1 = str_expand_env1(expanded, env);
        if (expanded1) { str_sets(&expanded, expanded1); }
        str_t expanded2 = str_expand_env2(expanded, env);
        if (expanded2) { str_sets(&expanded, expanded2); }
        if (! expanded1 && ! expanded2) {
            return expanded;
        }
    }
    logg_error("shell variable expansion exceeded maxdepth %i", maxdepth);
    return expanded;
}

typedef struct systemctl_unit_name
{
    str_t name;
    str_t prefix;
    str_t instance;
    str_t suffix;
    str_t component;
} systemctl_unit_name_t;

systemctl_unit_name_t*
systemctl_unit_name_new() 
{
    systemctl_unit_name_t* result = malloc(sizeof(systemctl_unit_name_t));
    result->name = str_NULL;
    result->prefix = str_NULL;
    result->instance = str_NULL;
    result->suffix = str_NULL;
    result->component = str_NULL;
    return result;
}

void
systemctl_unit_name_free(systemctl_unit_name_t* unit)
{
    if (! unit) return;
    str_null(&unit->name);
    str_null(&unit->prefix);
    str_null(&unit->instance);
    str_null(&unit->suffix);
    str_null(&unit->component);
    free(unit);
}

systemctl_unit_name_t* restrict
systemctl_parse_unit(systemctl_t* self, systemctl_conf_t* conf)
{
    systemctl_unit_name_t* unit = systemctl_unit_name_new();
    unit->name = systemctl_conf_name(conf);
    str_t unit_name = str_NULL;
    ssize_t has_suffix = str_rfind(unit->name, '.');
    if (has_suffix > 0) {
        unit_name = str_cut(unit->name, 0, has_suffix);
        unit->suffix = str_cut_end(unit->name, has_suffix+1);
    } else {
        unit_name = str_dup(unit->name);
        unit->suffix = str_dup("");
    }
    ssize_t has_instance = str_find(unit_name, '@');
    if (has_instance > 0) {
        unit->prefix = str_cut(unit_name, 0, has_instance);
        unit->instance = str_cut_end(unit_name, has_instance+1);
    } else {
        unit->prefix = str_dup(unit_name);
        unit->instance = str_dup("");
    }
    ssize_t has_component = str_rfind(unit->prefix, '-');
    if (has_component > 0) {
        unit->component = str_cut_end(unit->prefix, has_component+1);
    }
    str_free(unit_name);
    return unit;
}

static str_t restrict
sh_escape(str_t value)
{
   str_t escaped = str_escapes2(str_dup(value), '\\', "'");
   str_t result = str_dup3("'", escaped, "'");
   str_free(escaped);
   return result;
}

str_dict_t* restrict
systemctl_get_special_confs(systemctl_t* self, systemctl_conf_t* conf)
{
    str_dict_t* confs = str_dict_new();
    str_dict_add(confs, "%", "%");
    if (! conf)
        return confs;
    systemctl_unit_name_t* unit = systemctl_parse_unit(self, conf);
    str_dict_add(confs, "N", unit->name);
    str_dict_adds(confs, "n", sh_escape(unit->name));
    str_dict_add(confs, "P", unit->prefix);
    str_dict_adds(confs, "p", sh_escape(unit->prefix));
    str_dict_add(confs, "I", unit->instance);
    str_dict_adds(confs, "i", sh_escape(unit->instance));
    str_dict_add(confs, "J", unit->component);
    str_dict_adds(confs, "j", sh_escape(unit->component));
    str_dict_add(confs, "f", systemctl_conf_filename(conf));
    systemctl_unit_name_free(unit);
    str_t VARTMP = str_dup("/var/tmp");
    str_t TMP = str_dup("/tmp");
    str_t RUN = str_dup("/run");
    str_t DAT = str_dup("/var/lib");
    str_t LOG = str_dup("/var/log");
    str_t CACHE = str_dup("/var/cache");
    str_t CONFIG = str_dup("/etc");
    str_t HOME = str_dup("/root");
    str_t USER = str_dup("root");
    str_t SHELL = str_dup("/bin/sh");
    if (systemctl_is_user_conf(self, conf)) {
        str_sets(&USER, os_getlogin());
        str_sets(&HOME, get_home());
        str_sets(&RUN, os_environ_get("XDG_RUNTIME_DIR", get_runtime_dir()));
        str_sets(&CONFIG, os_environ_get("XDG_CONFIG_HOME", str_dup2(HOME, "./config")));
        str_sets(&CACHE, os_environ_get("XDG_CACHE_HOME", str_dup2(HOME, "/.cache")));
        // FIXME: not in original
        // str_sets(&SHARE, os_environ_get("XDG_DATA_HOME", str_dup2(HOME, "/.local/share")));
        str_sets(&DAT, str_dup(CONFIG));
        str_sets(&LOG, str_dup2(CONFIG, "log"));
        str_sets(&SHELL, os_environ_get("SHELL", str_dup(SHELL)));
        str_sets(&VARTMP, os_environ_get("TMPDIR", os_environ_get("TEMP", os_environ_get("TMP", str_dup(TMP)))));
    }
    str_dict_adds(confs, "V", os_path(self->root, VARTMP));
    str_dict_adds(confs, "T", os_path(self->root, TMP));
    str_dict_adds(confs, "t", os_path(self->root, RUN));
    str_dict_adds(confs, "S", os_path(self->root, DAT));
    str_dict_adds(confs, "s", str_dup(SHELL));
    str_dict_adds(confs, "h", str_dup(HOME));
    str_dict_adds(confs, "u", str_dup(USER));
    str_dict_adds(confs, "C", os_path(self->root, CACHE));
    str_dict_adds(confs, "E", os_path(self->root, CONFIG));

    str_free(VARTMP);
    str_free(TMP);
    str_free(RUN);
    str_free(DAT);
    str_free(LOG);
    str_free(CACHE);
    str_free(CONFIG);
    str_free(HOME);
    str_free(USER);
    str_free(SHELL);
    return confs;
}

str_t
systemctl_expand_special(systemctl_t* self, str_t value, systemctl_conf_t* conf)
{
    str_t result = str_dup(value);
    str_dict_t* confs = systemctl_get_special_confs(self, conf);
    ssize_t p = 0;
    while(true) {
       ssize_t x = str_find(result+p, '%');
       if (x < 0) break;
       char key[] = { result[p+x+1], '\0' };
       str_t val = str_dict_get(confs, key);
       if (! val) {
           logg_warning("can not expand %%%s", key);
           val = "''"; /* empty escaped string */
       }
       str_t prefix = str_cut(result, 0, p+x);
       str_t suffix = str_cut_end(result, p+x+2);
       str_sets(&result, str_dup3(prefix, val, suffix));
       str_free(prefix);
       str_free(suffix);
       p += str_len(val); /* step */
    }
    str_dict_free(confs);
    return result;
}

str_list_t* restrict
systemctl_exec_cmd(systemctl_t* self, str_t value, str_dict_t* env, systemctl_conf_t* conf) 
{
    str_list_t* restrict result = str_list_new();
    str_t cmd = str_replace(value, "\\\\n", "");
    str_t cmd2 = systemctl_expand_special(self, cmd, conf);
    if (cmd2) { str_sets(&cmd, cmd2); }
    str_t cmd3 = str_expand_env1(cmd, env);
    if (cmd3) { str_sets(&cmd, cmd3); }
    str_list_t* arg = shlex_split(cmd);
    logg_debug("split '%s' -> [%i] %s", cmd, arg->size, tmp_shell_cmd(arg));
    for (int i=0; i < arg->size; ++i) {
        str_t expanded = str_expand_env2(arg->data[i], env);
        if (expanded) {
            str_list_adds(result, expanded);
        } else {
            str_list_add(result, arg->data[i]);
        }
    }
    str_list_free(arg);
    str_null(&cmd);
    return result;
}

str_t restrict
systemctl_path_journal_log(systemctl_t* self, systemctl_conf_t* conf)
{
   str_t filename = os_path_basename(systemctl_conf_filename(conf));
   if (! filename) filename = str_dup("");
   str_t unitname = systemctl_conf_name(conf);
   if (! unitname) unitname = str_dup("default");
   str_append(&unitname, ".unit");
   str_t name = filename;
   if (! name) name = unitname;
   str_t log_folder = systemctl_conf_os_path_var(conf, self->use.journal_log_folder);
   str_t log_file = str_replace(name, "/", ".");
   str_append(&log_file, ".log");
   if (str_startswith(log_file, "."))
       str_prepend(&log_file, "dot.");
   str_t res = os_path(log_folder, log_file);
   str_null(&log_file);
   str_null(&log_folder);
   str_null(&unitname);
   str_null(&filename);
   return res;
}

int
systemctl_open_journal_log(systemctl_t* self, systemctl_conf_t* conf)
{
   str_t log_file = systemctl_path_journal_log(self, conf);
   str_t log_folder = os_path_dirname(log_file);
   if (! os_path_isdir(log_folder))
       os_makedirs(log_folder);
   str_free(log_folder);
   int res = open(log_file, O_WRONLY|O_CREAT|O_EXCL, S_IWUSR|S_IRUSR|S_IRGRP);
   if (res > 0) {
       logg_info("output %i %s", res, log_file);
   } else {
       res = open(log_file, O_WRONLY|O_APPEND);
       if (res > 0) {
           logg_info("append %i %s", res, log_file);
       } else {
           logg_info("problems %i %s (%s)", res, log_file, strerror(errno));
           res = open("/dev/null", O_WRONLY);
           logg_info("redirect %i %s (%s)", res, "/dev/null", strerror(errno));
       }
   }
   str_free(log_file);
   return res;
}

/* ..... */

bool
systemctl_start_modules(systemctl_t* self, str_list_t* modules) 
{
     bool found_all = true;
     str_list_t units;
     str_list_init(&units);
     for (int m = 0; m < modules->size; ++m) {
         str_t module = modules->data[m];
         str_list_t* matched = systemctl_match_unit(self, module);
         if (str_list_empty(matched)) {
            logg_error("Unit %s could not be found.", module);
            found_all = false;
            str_list_free(matched);
            continue;
        }
        for (int u=0; u < matched->size; ++u) {
            str_t unit = matched->data[u];
            if (!str_list_contains(&units, unit)) {
                str_list_add(&units, unit);
            }
        }
        str_list_free(matched);
    }
    bool init = self->use.now || self->use.init;
    bool done = systemctl_start_units(self, &units, init);
    str_list_null(&units);
    return done && found_all;
}

bool
systemctl_start_units(systemctl_t* self, str_list_t* units, bool init)
{
    bool done = true;
    str_list_t* started_units = str_list_new();
    for (int u=0; u < units->size; ++u) {
        str_t unit = units->data[u];
        str_list_add(started_units, unit);
        bool started = systemctl_start_unit(self, unit);
        if (! started)
            done = false;
    }
    if (init) {
        logg_info("init-loop start");
        str_t sig = systemctl_init_loop_until_stop(self, started_units);
        logg_info("init-loop stop %s", sig);
        for (int k = started_units->size-1; k >= 0; --k) {
            str_t unit = started_units->data[k];
            bool stopped = systemctl_stop_unit(self, unit);
        }
        str_free(sig);
    }
    str_list_free(started_units);
    return done;
}

bool
systemctl_start_unit(systemctl_t* self, str_t unit)
{
   systemctl_conf_t* conf = systemctl_load_unit_conf(self, unit);
   return systemctl_start_unit_from(self, conf);
}

int
systemctl_getTimeoutStartSec(systemctl_conf_t* conf)
{
   return 5; /* FIXME */
}

bool
systemctl_start_unit_from(systemctl_t* self, systemctl_conf_t* conf)
{
    int timeout = systemctl_getTimeoutStartSec(conf);
    bool doRemainAfterExit = systemctl_conf_getbool(conf, "Service", "RemainAfterExit", "no");
    str_t runs = systemctl_conf_get(conf, "Service", "Type", "simple");
    str_dict_t* env = systemctl_get_env(self, conf);
    /* for StopPost on failure: */
    int returncode = 0;
    str_t service_result = str_dup("success");
    if (true) {
        str_list_t* cmd_list = systemctl_conf_getlist(conf, "Service", "ExecStartPre", &empty_str_list);
        for (int c=0; c < cmd_list->size; ++c) {
            bool check = checkstatus_do(cmd_list->data[c]);
            str_t cmd = checkstatus_cmd(cmd_list->data[c]);
            str_list_t* newcmd = systemctl_exec_cmd(self, cmd, env, conf);
            logg_info(" pre-start %s", tmp_shell_cmd(newcmd));
            int forkpid = fork();
            if (! forkpid) {
                systemctl_execve_from(self, conf, newcmd, env);
                /* unreachable */
            }
            str_list_free(newcmd);
            run_t run;
            subprocess_waitpid(forkpid, &run);
            logg_info(" pre-start done (%s) <-%s>",
                tmp_int_or(run.returncode, "OK"), tmp_int_or_no(run.signal));
        }
    }
    if (str_equal(runs, "sysv")) {
        str_t status_file = systemctl_status_file_from(self, conf);
        if (true) {
            str_t exe = systemctl_conf_filename(conf);
            str_t cmd = str_format("'%s' start", exe);
            str_dict_add(env, "SYSTEMCTL_SKIP_REDIRECT", "yes");
            str_list_t* newcmd = systemctl_exec_cmd(self, cmd, env, conf);
            logg_info("%s start %s", runs, tmp_shell_cmd(newcmd));
            int forkpid = fork();
            if (! forkpid) {
                setsid();
                systemctl_execve_from(self, conf, newcmd, env);
                /* unreachable */
            }
            str_list_free(newcmd);
            run_t run;
            subprocess_waitpid(forkpid, &run);
            logg_info("%s start done (%s) <-%s>", runs,
                tmp_int_or(run.returncode, "OK"), tmp_int_or_no(run.signal));
            str_t active = run.returncode ? "failed" : "active";
            systemctl_write_status_from(self, conf, "ActiveState", active);
            return true;
        }
    }
    str_free(service_result);
    str_dict_free(env);
    return false;
}

str_dict_t* restrict
systemctl_extend_exec_env(systemctl_t* self, str_dict_t* env)
{
    str_dict_t* res = str_dict_new();
    str_dict_add_all(res, env);
    /* FIXME: implant DefaultPath into $PATH */
    /* FIXME: reset locale to system default */
    /* FIXME: read /etc/local.conf */
    return res;
}

void
systemctl_execve_from(systemctl_t* self, systemctl_conf_t* conf, str_list_t* cmd, str_dict_t* env)
{
    str_t runs = systemctl_conf_get(conf, "Service", "Type", "simple");
    logg_info("%s process for %s", runs, systemctl_conf_filename(conf));
    int inp = open("/dev/zero", O_RDONLY);
    int out = systemctl_open_journal_log(self, conf);
    dup2(inp, STDIN_FILENO);
    dup2(out, STDOUT_FILENO);
    dup2(out, STDERR_FILENO);
    str_t runuser = systemctl_expand_special(self, systemctl_conf_get(conf, "Service", "User", ""), conf);
    str_t rungroup = systemctl_expand_special(self, systemctl_conf_get(conf, "Service", "Group", ""), conf);
    str_dict_t* envs = shutil_setuid(runuser, rungroup);
    env = systemctl_extend_exec_env(self, env);
    str_dict_add_all(env, envs);
    str_free(runuser);
    str_free(rungroup);
    str_dict_free(envs);
    char* argv[cmd->size + 1]; /* C99 ? */
    char* envp[env->size + 1]; /* C99 ? */
    for (int i = 0; i < cmd->size; ++i) {
        argv[i] = alloca(str_len(cmd->data[i])+1);
        str_cpy(argv[i], cmd->data[i]);
        argv[i+1] = NULL;
    }
    for (int i = 0; i < env->size; ++i) {
        envp[i] = alloca(str_len(env->data[i].key)+1+str_len(env->data[i].value)+1);
        strcpy(envp[i], env->data[i].key);
        strcat(envp[i], "=");
        strcpy(envp[i], env->data[i].value);
        envp[i+1] = NULL;
    }
    str_dict_free(env); /* via extend_exec_env */
    execve(argv[0], argv, envp);
    exit(111); /* unreachable */
}

bool
systemctl_stop_unit(systemctl_t* self, str_t unit)
{
   systemctl_conf_t* conf = systemctl_load_unit_conf(self, unit);
   return systemctl_stop_unit_from(self, conf);
}

bool
systemctl_stop_unit_from(systemctl_t* self, systemctl_conf_t* conf)
{
   return false;
}

static int last_signal;

static void 
ignore_signals_and_raise_interrupt(int sig)
{
   last_signal = sig;
}

str_t restrict
systemctl_init_loop_until_stop(systemctl_t* self, str_list_t* started_units)
{
    str_t result = str_NULL;
    signal(SIGQUIT, ignore_signals_and_raise_interrupt);
    signal(SIGINT, ignore_signals_and_raise_interrupt);
    signal(SIGTERM, ignore_signals_and_raise_interrupt);
    while (true) {
       int err = sleep(self->use.InitLoopSleep);
       /* FIXME: reap_zomies */
       if (err) {
           if (last_signal == SIGQUIT) { result = str_dup("SIGQUIT"); }
           if (last_signal == SIGINT) { result = str_dup("SIGINT"); }
           if (last_signal == SIGTERM) { result = str_dup("SIGTERM"); }
           if (result) {
               logg_info("interrupted - exist init-loop");
               break;
           }
       }
    }
    logg_debug("done - init loop");
    return result;
}

/* ..... */

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

str_t restrict
systemctl_status_modules(systemctl_t* self, str_list_t* modules)
{
    bool found_all = true;
    str_list_t units;
    str_list_init(&units);
    for (int m=0; m < modules->size; ++m) {
        str_t module = modules->data[m];
        str_list_t* matched = systemctl_match_unit(self, module);
        if (str_list_empty(matched)) {
            logg_error("Unit %s could not be found.", module);
            found_all = false;
            str_list_free(matched);
            continue;
        }
        for (int u=0; u < matched->size; ++u) {
            str_t unit = matched->data[u];
            if (!str_list_contains(&units, unit)) {
                str_list_add(&units, unit);
            }
        }
        str_list_free(matched);
    }
    str_t result = systemctl_status_units(self, &units);
    str_list_null(&units);
    return result;
}

str_t restrict
systemctl_status_units(systemctl_t* self, str_list_t* units)
{
    str_t result = str_new();
    for (int u=0; u < units->size; ++u) {
        str_t unit = units->data[u];
        str_t result1 = systemctl_status_unit(self, unit);
        if (! str_empty(result)) {
           str_add(&result, "\n\n");
        }
        str_add(&result, result1);
        str_free(result1);
    }
    return result;
}

str_t restrict
systemctl_status_unit(systemctl_t* self, str_t unit)
{
    systemctl_conf_t* conf = systemctl_get_unit_conf(self, unit);
    str_t result = str_new();
    str_add(&result, unit);
    str_add(&result, " - ");
    str_adds(&result, systemctl_get_description_from(self, conf));
    str_t loaded = systemctl_conf_loaded(conf);
    if (!str_empty(loaded)) {
       str_t filename = systemctl_conf_filename(conf);
       str_t enabled = systemctl_enabled_from(self, conf);
       str_adds(&result, str_format("\n    Loaded: %s (%s, %s)", loaded, filename, enabled));
    } else {
       str_add(&result, "\n    Loaded: failed");
       self->error = self->error | ERROR3;
       return result;
    }
    str_t active = systemctl_get_active_from(self, conf);
    str_t substate = systemctl_get_substate_from(self, conf);
    str_adds(&result, str_format("\n    Active: %s (%s)", active, substate));
    if (str_equal(active, "active")) {
       self->error = self->error | ERROR3;
    }
    str_free(active);
    str_free(substate);
    return result;
}

/* ........................................................ */

int
str_print(str_t result)
{
    if (! result) return 0;
    fprintf(stdout, "%s\n", result);
    return result && result[0] ? 0 : 1;
}

int
str_list_print(str_list_t* result)
{
    if (! result) return 0;
    for (int i = 0; i < result->size; ++i) {
        str_t element = result->data[i];
        fprintf(stdout, "%s\n", element);
    }
    return result->size ? 0 : 1;
}

int
str_dict_print(str_dict_t* result)
{
    if (! result) return 0;
    for (int i = 0; i < result->size; ++i) {
        str_t line = str_dup3(result->data[i].key, "\t", result->data[i].value);
        fprintf(stdout, "%s\n", line);
        str_free(line);
    }
    return result->size ? 0 : 1;
}

int
str_list_list_print(str_list_list_t* result)
{
    if (! result) return 0;
    for (int i = 0; i < result->size; ++i) {
        str_list_t* element = &result->data[i];
        str_t line = str_list_join(element, "\t");
        fprintf(stdout, "%s\n", line);
        str_free(line);
    }
    return result->size ? 0 : 1;
}

int
str_print_bool(bool value)
{
    return value ? 0 : 1;
}

static char _systemctl_debug_log[] = "/var/log/systemctl.debug.log";
static char _systemctl_extra_log[] = "/var/log/systemctl.log";

int 
main(int argc, char** argv) {
    systemctl_settings_t settings;
    systemctl_settings_init(&settings);
    /* scan options */
    systemctl_options_t cmd;
    systemctl_options_init(&cmd);
    systemctl_options_add3(&cmd, "-h", "--help", "this help screen");
    systemctl_options_add5(&cmd, "-e", "--extra-vars", "--environment", "=NAME=VAL", 
        "..override settings in the syntax of 'Environment='");
    systemctl_options_add4(&cmd, "-t", "--type", "=TYPE", "List units of a particual type");
    systemctl_options_add3(&cmd, "--root", "=PATH", "Enable unit files in the specified root directory (used for alternative root prefix)");
    systemctl_options_add3(&cmd, "-4", "--ipv4", "..only keep ipv4 localhost in /etc/hosts");
    systemctl_options_add3(&cmd, "-6", "--ipv6", "..only keep ipv6 localhost in /etc/hosts");
    systemctl_options_add3(&cmd, "-1", "--init", "..keep running as init-process (default if PID 1)");
    systemctl_options_add3(&cmd, "-v", "--verbose", "increase logging level");
    systemctl_options_scan(&cmd, argc, argv);
    if (str_list_dict_contains(&cmd.opts, "help")) {
        str_t prog = os_path_basename(argv[0]);
        str_t note = str_format("%s [options] command [name...]", prog);
        systemctl_options_help2(&cmd, note, NULL);
        systemctl_options_note("use 'help' command for more information");
        str_free(prog);
        str_free(note);
        systemctl_options_null(&cmd);
        /* systemctl_settings_null(&settings); */
        return 0;
    }
    /* .... */
    if (str_list_dict_contains(&cmd.opts, "verbose")) {
        int level = str_list_len(str_list_dict_get(&cmd.opts, "verbose"));
        logg_setlevel(LOG_ERROR - 10 * level); /* similar style to python */
    }
    str_t root = str_list_dict_get_last(&cmd.opts, "root");
    str_t systemctl_extra_log = os_path(root, _systemctl_extra_log);
    if (os_path_exists(systemctl_extra_log)) {
        int level = str_list_len(str_list_dict_get(&cmd.opts, "verbose"));
        logg_open_logfile(1, systemctl_extra_log);
        logg_setlevel_logfile(1, LOG_INFO - 10 * level);
    }
    str_t systemctl_debug_log = os_path(root, _systemctl_debug_log);
    if (os_path_exists(systemctl_debug_log)) {
        logg_open_logfile(2, systemctl_debug_log);
        logg_setlevel_logfile(2, LOG_DEBUG);
    }
    str_free(systemctl_extra_log);
    str_free(systemctl_debug_log);
    /* ............................................ */
    systemctl_t systemctl;
    systemctl_init(&systemctl, &settings);
    str_list_set(&systemctl.extra_vars, str_list_dict_get(&cmd.opts, "environment"));
    str_set(&systemctl.root, str_list_dict_get_last(&cmd.opts, "root"));

    str_t command = str_NULL;
    str_list_t args = str_list_NULL;
    if (cmd.args.size == 0) {
        command = "help";
        str_list_init(&args);
    } else {
        command = cmd.args.data[0];
        str_list_init_from(&args, cmd.args.size - 1, cmd.args.data + 1);
    }
    
    if (str_equal(command, "daemon-reload")) {
        /* FIXME */
        logg_info("daemon-reload");
        logg_debug("needs to be implemented");
        logg_debug(" ................. ");
    } else if (str_equal(command, "list-units")) {
        str_list_list_t* result = systemctl_list_units(&systemctl, &args);
        str_list_list_print(result);
        str_list_list_free(result);
    } else if (str_equal(command, "list-unit-files")) {
        str_list_list_t* result = systemctl_show_list_unit_files(&systemctl, &args);
        str_list_list_print(result);
        str_list_list_free(result);
    } else if (str_equal(command, "status")) {
        str_t result = systemctl_status_modules(&systemctl, &args);
        str_print(result);
        str_free(result);
    } else if (str_equal(command, "start")) {
        bool result = systemctl_start_modules(&systemctl, &args);
        str_print_bool(result);
    } else if (str_equal(command, "show-environment")) {
        for (int i=0; i < args.size; ++i) {
            str_dict_t* result = systemctl_show_environment(&systemctl, args.data[i]);
            str_dict_print(result);
            str_dict_free(result);
        }
    } else {
        fprintf(stderr, "unknown command '%s'", command);
    }
    str_list_null(&args);

    int exitcode = systemctl.error;
    systemctl_null(&systemctl);
    systemctl_options_null(&cmd);
    if (exitcode) {
        logg_error(" exitcode %i", exitcode);
    } else {
        logg_debug(" exitcode %i", exitcode);
    }
    tmp_null();
    logg_stop();
    return exitcode;
}
