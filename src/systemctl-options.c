#include "systemctl-options.h"
#include "systemctl-types.h"
#include "systemctl-logging.h"
#include <stdlib.h>
#include <stdio.h>

void
systemctl_options_init(systemctl_options_t* self)
{
    str_dict_init(&self->optmapping);
    str_dict_init(&self->optargument);
    str_dict_init(&self->optcomment);
    str_list_dict_init(&self->opts);
    str_list_init(&self->args);
}

void
systemctl_options_null(systemctl_options_t* self)
{
    str_dict_null(&self->optmapping);
    str_dict_null(&self->optargument);
    str_dict_null(&self->optcomment);
    str_list_dict_null(&self->opts);
    str_list_null(&self->args);
}

void
systemctl_options_add9(systemctl_options_t* self, 
    str_t opt1, str_t opt2, str_t opt3, str_t opt4, str_t opt5, 
    str_t opt6, str_t opt7, str_t opt8, str_t opt9)
{
    str_t opts[] = { opt1, opt2, opt3, opt4, opt5, opt6, opt7, opt8, opt9 };
    ssize_t optslen = 9;
    /* the last -opt/--option will name the storage key (without '-'s) */
    str_t key = NULL;
    for (int i=0; i < optslen; ++i) {
        if (! str_empty(opts[i])) {
             if (str_startswith(opts[i], "--")) {
                 str_sets(&key, str_cut_end(opts[i], 2));
             } else if (str_startswith(opts[i], "-")) {
                 str_sets(&key, str_cut_end(opts[i], 1));
             }
        }
    }
    if (! key) {
       logg_error("missing option name");
       return;
    }
    for (int i=0; i < optslen; ++i) {
        if (! str_empty(opts[i])) {
            if (str_startswith(opts[i], "-")) {
                str_dict_add(&self->optmapping, opts[i], key);
            }
            else if (str_startswith(opts[i], "=")) {
                str_dict_add(&self->optargument, key, opts[i]);
            }
            else {
                str_dict_add(&self->optcomment, key, opts[i]);
            }
        }
    }
    str_null(&key);
}

void
systemctl_options_add8(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3, str_t opt4, str_t opt5, str_t opt6, str_t opt7, str_t opt8)
{
    systemctl_options_add9(self, opt1, opt2, opt3, opt4, opt5, opt6, opt7, opt8, NULL);
}

void
systemctl_options_add7(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3, str_t opt4, str_t opt5, str_t opt6, str_t opt7)
{
    systemctl_options_add9(self, opt1, opt2, opt3, opt4, opt5, opt6, opt7, NULL, NULL);
}

void
systemctl_options_add6(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3, str_t opt4, str_t opt5, str_t opt6)
{
    systemctl_options_add9(self, opt1, opt2, opt3, opt4, opt5, opt6, NULL, NULL, NULL);
}

void
systemctl_options_add5(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3, str_t opt4, str_t opt5)
{
    systemctl_options_add9(self, opt1, opt2, opt3, opt4, opt5, NULL, NULL, NULL, NULL);
}

void
systemctl_options_add4(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3, str_t opt4)
{
    systemctl_options_add9(self, opt1, opt2, opt3, opt4, NULL, NULL, NULL, NULL, NULL);
}

void
systemctl_options_add3(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3)
{
    systemctl_options_add9(self, opt1, opt2, opt3, NULL, NULL, NULL, NULL, NULL, NULL);
}

void
systemctl_options_add2(systemctl_options_t* self, str_t opt1, str_t opt2)
{
    systemctl_options_add9(self, opt1, opt2, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
}

void
systemctl_options_add1(systemctl_options_t* self, str_t opt1)
{
    systemctl_options_add9(self, opt1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
}

bool
systemctl_options_scan(systemctl_options_t* self, int argc, char** argv)
{
    bool stopargs = false;
    str_t nextarg = NULL;
    for (int o=0; o < self->optmapping.size; ++o) {
        logg_debug("WITH OPTION %s", self->optmapping.data[o]);
    }
    /* let's go */
    for (int i=1; i < argc; ++i) {
        if (stopargs) {
            str_list_add(&self->args, argv[i]);
            continue;
        }
        if (nextarg) {
            str_list_dict_add1(&self->opts, nextarg, argv[i]);
            nextarg = NULL;
            continue;
        }
        if (str_empty(argv[i])) {
            continue;
        }
        if (str_equal(argv[i], "--")) {
            stopargs = true; /* later arguments are never options */
            continue;
        } else if (str_startswith(argv[i], "--")) {
            int x = str_find(argv[i], "=");
            if (x > 0) {
                str_t opt = str_cut(argv[i], 0, x);
                str_t key = str_dict_get(&self->optmapping, opt);
                if (! key) {
                    logg_error("no such option %s", opt);
                    continue;
                }
                str_t val = str_cut_end(argv[i], x+1);
                str_list_dict_adds1(&self->opts, key, val);
            } else {
                str_t opt = argv[i];
                str_t key = str_dict_get(&self->optmapping, opt);
                if (! key) {
                    logg_error("no such option %s", opt);
                    continue;
                }
                str_t arg = str_dict_get(&self->optargument, opt);
                if (arg) {
                   nextarg = key;
                   continue; /* with next argument */
                }
                str_list_dict_add1(&self->opts, key, opt);
            }
        } else if (str_startswith(argv[i], "-")) {
            str_t chars = argv[i];
            ssize_t sized = str_len(chars);
            for (int k=1; k < sized; ++k) {
                char opt[] = { '-', chars[k], '\0' };
                str_t key = str_dict_get(&self->optmapping, opt);
                if (! key) {
                    logg_error("no such option %s", opt);
                    continue;
                }
                nextarg = str_dict_get(&self->optargument, opt);
                if (k+1 < sized && chars[k+1] == '-') {
                    ++k;
                    str_list_dict_add1(&self->opts, opt, "");
                    continue; /* next short arg */
                }
                str_t arg = str_dict_get(&self->optargument, opt);
                if (nextarg) {
                   logg_error("multiple short options require an arg: %s (%s) (%s)", opt, key, nextarg);
                   str_list_dict_add1(&self->opts, nextarg, opt);
                }
                if (arg) {
                    nextarg = key;
                } else {
                    str_list_dict_add1(&self->opts, key, opt);
                }
            }
        } else {
           str_list_add(&self->args, argv[i]);
        }
    }
}

bool
systemctl_options_help(systemctl_options_t* self)
{
    printf("HELP\n");
    str_dict_t options;
    str_dict_init(&options);
    for (int i=0; i < self->optmapping.size; ++i) {
        str_t key = self->optmapping.data[i].value;
        if (! str_dict_contains(&options, key)) {
            str_t arg = str_dict_get(&self->optargument, key);
            str_dict_add(&options, key, arg);
        }
    }
    for (int k=0; k < options.size; ++k) {
        str_t key = options.data[k].key;
        str_t arg = options.data[k].value;
        str_list_t opts;
        str_list_init(&opts);
        for (int i=0; i < self->optmapping.size; ++i) {
            str_t opt = self->optmapping.data[i].key;
            str_t value = self->optmapping.data[i].value;
            if (! str_equal(value, key)) continue;
            str_list_add(&opts, opt);
        }
        ssize_t col = 0;
        str_t showopts = str_list_join(&opts, " / ");
        printf("  %s", showopts);
        col += str_len(showopts) + 2;
        if (arg) {
           printf(" %s", arg);
           col += str_len(arg) + 1;
        }
        str_t help = str_dict_get(&self->optcomment, key);
        if (help) {
            if (col < 30) {
                for(; col < 24; ++col) 
                    printf(" ");
            } else {
                printf("\n                        ");
            }
            printf(" %s", help);
            col += str_len(help) + 2;
        }
        printf("\n");
        str_free(showopts);
        str_list_null(&opts);
    }
    if (false) {
        for (int u=0; u < self->optcomment.size; ++u) {
            str_t key = self->optcomment.data[u].key;
            str_t value = self->optcomment.data[u].value;
            logg_info("HELP %s: %s", key, value);
        }
    }

    str_dict_null(&options);
}

str_list_t*
str_options_getlist(systemctl_options_t* self, str_t name, str_list_t* defaults)
{
    str_list_t* values = str_list_dict_get(&self->opts, name);
    if (values && values->size) {
        return values;
    }
    return defaults;
}

str_t
str_options_get(systemctl_options_t* self, str_t name, str_t defaults)
{
    str_list_t* values = str_list_dict_get(&self->opts, name);
    if (values && values->size) {
        return values->data[values->size-1]; /* the last value given */
    }
    return defaults;
}

bool
str_options_getbool(systemctl_options_t* self, str_t name, bool defaults)
{
    str_list_t* values = str_list_dict_get(&self->opts, name);
    if (values && values->size) {
        str_t val = values->data[values->size-1]; /* the last value given */
        if (str_empty(val)) return false;
        return true;
    }
    return defaults;
}

