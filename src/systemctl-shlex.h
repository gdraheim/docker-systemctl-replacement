#ifndef SYSTEMCTL_SHLEX_H
#define SYSTEMCTL_SHLEX_H 1
#include "systemctl-types.h"

typedef struct _shlex shlex_t;

/* from systemctl-shlex.c */

void
shlex_init(shlex_t* self);

void
shlex_null(shlex_t* self);

void
shlex_begin(shlex_t* self, str_t value);

str_t
shlex_readnext(shlex_t* self);

str_t restrict
shlex_readline(shlex_t* self);

str_t restrict
shlex_get_token(shlex_t* self);

str_t restrict
shlex_read_token(shlex_t* self);

str_list_t* restrict
shlex_splits(str_t value, const_str_t options);

str_list_t* restrict
shlex_split(str_t value);

str_list_t* restrict
shlex_parse(str_t value);

#endif
