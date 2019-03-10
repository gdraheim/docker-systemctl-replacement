#ifndef SYSTEMCTL_OPTIONS_H
#define SYSTEMCTL_OPTIONS_H 1

#include <stdbool.h>
#include "systemctl-types.h"

typedef struct systemctl_options
{
    str_dict_t optmapping;
    str_dict_t optargument;
    str_dict_t optcomment;
    str_list_dict_t opts;
    str_list_t args;
} systemctl_options_t;

/* from systemctl-options.c */

void
systemctl_options_init(systemctl_options_t* self);

void
systemctl_options_null(systemctl_options_t* self);

void
systemctl_options_add3(systemctl_options_t* self, str_t opt1, str_t opt2, str_t opt3);

void
systemctl_options_add2(systemctl_options_t* self, str_t opt1, str_t opt2);

void
systemctl_options_add1(systemctl_options_t* self, str_t opt1);

bool
systemctl_options_scan(systemctl_options_t* self, int argc, char** argv);

str_list_t*
str_options_getlist(systemctl_options_t* self, str_t name, str_list_t* defaults);

str_t
str_options_get(systemctl_options_t* self, str_t name, str_t defaults);

bool
str_options_getbool(systemctl_options_t* self, str_t name, bool defaults);

#endif
