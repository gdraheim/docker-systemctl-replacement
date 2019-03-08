#ifndef SYSTEMCTL_OPTIONS_H
#define SYSTEMCTL_OPTIONS_H 1

typedef struct systemctl_options
{
    str_dict_t optmapping;
    str_dict_t optargument;
    str_dict_t optcomment;
    str_list_dict_t opts;
    str_list_t args;
} systemctl_options_t;

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
    /* .. */
    str_t opt = NULL;
    for (int i=0; i < optslen; ++i) {
        if (! str_empty(opts[i])) {
             if (str_startswith(opts[i], "--")) {
                 str_sets(&opt, str_cut_end(opts[i], 2));
             } else if (str_startswith(opts[i], "-")) {
                 str_sets(&opt, str_cut_end(opts[i], 1));
             }
        }
    }
    if (! opt) {
       logg_error("missing option name");
       return;
    }
    for (int i=0; i < optslen; ++i) {
        if (! str_empty(opts[i])) {
            if (str_startswith(opts[i], "-")) {
                str_dict_add(&self->optmapping, opts[i], opt);
            }
            else if (str_startswith(opts[i], "=")) {
                str_dict_add(&self->optargument, opts[i], opt);
            }
            else {
                str_dict_add(&self->optcomment, opts[i], opt);
            }
        }
    }
    str_null(&opt);
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
            stopargs = true;
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

#endif
