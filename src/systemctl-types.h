#ifndef SYSTEMCTL_TYPES_H
#define SYSTEMCTL_TYPES_H 1
#include <string.h>
#include <stdbool.h>
#include <stddef.h>
#include <sys/types.h>

/* str */

typedef char* str_t;
typedef char const * const_str_t;

static inline ssize_t
str_len(const_str_t str1)
{
  if (str1 == NULL) return 0;
  return strlen(str1);
}

static inline str_t restrict
str_dup(const_str_t str1)
{
  if (str1 == NULL) return NULL;
  return strdup(str1);
}

static inline void
str_cpy(str_t into, const_str_t str1)
{
  if (into == NULL) return;
  if (str1 == NULL) return;
  strcpy(into, str1);
}

static inline int
str_cmp(const_str_t str1, const_str_t str2)
{
  if (str1 == NULL || str2 == NULL) {
      if (str1 && ! str2) {
          return -1;
      }
      if (! str1 && str2) {
          return 1;
      }
      return 0;
  }
  return strcmp(str1, str2);
}

/* types */

typedef void* ptr_list_entry_t;
typedef str_t str_list_entry_t;

typedef struct ptr_list
{
  ssize_t size;
  ptr_list_entry_t* data;
} ptr_list_t;

typedef struct str_list
{
  ssize_t size;
  str_list_entry_t* data;
} str_list_t;

typedef struct str_list_list
{
  ssize_t size;
  str_list_t* data;
} str_list_list_t;

typedef struct str_dict_entry
{
  str_t key;
  str_t value;
} str_dict_entry_t;

typedef struct str_dict
{
  ssize_t size;
  str_dict_entry_t* data;
} str_dict_t;

typedef struct str_list_dict_entry
{
  str_t key;
  str_list_t value;
} str_list_dict_entry_t;

typedef struct str_list_dict
{
  ssize_t size;
  str_list_dict_entry_t* data;
} str_list_dict_t;

typedef struct str_list_dict_dict_entry
{
  str_t key;
  str_list_dict_t value;
} str_list_dict_dict_entry_t;

typedef struct str_list_dict_dict
{
  ssize_t size;
  str_list_dict_dict_entry_t* data;
} str_list_dict_dict_t;

typedef struct ptr_dict_entry
{
  str_t key;
  void* value;
} ptr_dict_entry_t;

typedef struct ptr_list_dict_entry
{
  str_t key;
  ptr_list_t value;
} ptr_list_dict_entry_t;

typedef void (*free_func_t)(void*);

typedef struct ptr_dict
{
  ssize_t size;
  ptr_dict_entry_t* data;
  free_func_t free;
} ptr_dict_t;

typedef struct ptr_list_dict
{
  ssize_t size;
  ptr_list_dict_entry_t* data;
  free_func_t free;
} ptr_list_dict_t;

/* init */

#define str_NULL NULL
#define str_EMPTY { '\0' }

#define str_list_NULL { 0, NULL }
#define str_list_list_NULL { 0, NULL }
#define str_dict_NULL { 0, NULL }
#define str_dict_NULL { 0, NULL }
#define str_list_dict_NULL { 0, NULL }
#define str_list_dict_dict_NULL { 0, NULL }

/* initialized with the NULL macros */
extern str_t empty_str;
extern str_list_t empty_str_list;
extern str_list_list_t empty_str_list_list;
extern str_dict_t empty_str_dict_t;
extern str_list_dict_t empty_str_list_dict_t;
extern str_list_dict_dict_t empty_str_list_dict_dict_t;

/* len */

static inline ssize_t
str_list_len(const str_list_t* self)
{
   return self->size;
}

static inline ssize_t
str_list_list_len(const str_list_list_t* self)
{
   return self->size;
}

static inline ssize_t
str_list_dict_len(const str_list_dict_t* self)
{
   return self->size;
}

static inline ssize_t
str_list_dict_dict_len(const str_list_dict_dict_t* self)
{
   return self->size;
}

static inline ssize_t
str_dict_len(const str_dict_t* self)
{
   return self->size;
}

/* empty */

static inline bool
str_empty(const str_t self)
{
  if (self == NULL) return true;
  return 0 == str_len(self);
}

static inline bool
str_list_empty(const str_list_t* self)
{
  if (self == NULL) return true;
  return 0 == self->size;
}

static inline bool
str_dict_empty(const str_dict_t* self)
{
  if (self == NULL) return true;
  return 0 == self->size;
}

static inline bool
str_list_dict_empty(const str_list_dict_t* self)
{
  if (self == NULL) return true;
  return 0 == self->size;
}

/* from systemctl-types.c */

void
str_init(str_t* self);

void
str_init0(str_t* self, ssize_t size);

void
str_init_from(str_t* self, char* str);

void
str_list_init0(str_list_t* self, ssize_t size);

void
str_list_init(str_list_t* self);

void
str_list_init_from(str_list_t* self, int size, char** data);

void
str_list_list_init0(str_list_list_t* self, ssize_t size);

void
str_list_list_init(str_list_list_t* self);

void
str_list_list_init_from(str_list_list_t* self, int size, char** data);

void
str_dict_init0(str_dict_t* self, ssize_t size);

void
str_dict_init(str_dict_t* self);

void
str_list_dict_init0(str_list_dict_t* self, ssize_t size);

void
str_list_dict_init(str_list_dict_t* self);

void
str_list_dict_dict_init0(str_list_dict_dict_t* self, ssize_t size);

void
str_list_dict_dict_init(str_list_dict_dict_t* self);

void
ptr_dict_init0(ptr_dict_t* self, ssize_t size, free_func_t free);

void
ptr_dict_init(ptr_dict_t* self, free_func_t free);

void
str_null(str_t* self);

void
str_list_null(str_list_t* self);

void
str_list_list_null(str_list_list_t* self);

void
str_dict_null(str_dict_t* self);

void
str_list_dict_null(str_list_dict_t* self);

void
str_list_dict_dict_null(str_list_dict_dict_t* self);

void
ptr_dict_null(ptr_dict_t* self);

void
str_free(str_t self);

void
str_list_free(str_list_t* self);

void
str_list_list_free(str_list_list_t* self);

void
str_dict_free(str_dict_t* self);

void
str_list_dict_free(str_list_dict_t* self);

void
str_list_dict_dict_free(str_list_dict_dict_t* self);

void
ptr_dict_free(ptr_dict_t* self);

str_t restrict
str_new();

str_list_t* restrict
str_list_new();

str_list_t* restrict
str_list_new0(ssize_t size);

str_list_list_t* restrict
str_list_list_new();

str_dict_t* restrict
str_dict_new();

str_list_dict_t* restrict
str_list_dict_new();

str_list_dict_dict_t* restrict
str_list_dict_dict_new();

void
logg_info_ptr_dict(str_t msg, const ptr_dict_t* self);

void
logg_info_ptr_list_dict(str_t msg, const ptr_list_dict_t* self);

void
logg_info_str_dict(str_t msg, const str_dict_t* self);

void
logg_info_str_list_dict(str_t msg, const str_list_dict_t* self);

void
logg_info_str_list_dict_dict(str_t msg, const str_list_dict_dict_t* self);

str_t
str_list_get(const str_list_t* self, const_str_t key);

str_t
str_dict_get(const str_dict_t* self, const_str_t key);

str_list_t*
str_list_dict_get(const str_list_dict_t* self, const_str_t key);

str_list_dict_t*
str_list_dict_dict_get(const str_list_dict_dict_t* self, const_str_t key);

void*
ptr_dict_get(const ptr_dict_t* self, const_str_t key);

ssize_t
str_find_str(const_str_t self, const_str_t key);

ssize_t
str_find(const_str_t self, char key);

ssize_t
str_rfind(const_str_t self, char key);

ssize_t
str_list_find(const str_list_t* self, const_str_t key);

ssize_t
ptr_dict_find(const ptr_dict_t* self, const_str_t key);

ssize_t
ptr_list_dict_find(const ptr_list_dict_t* self, const_str_t key);

ssize_t
ptr_dict_find_pos(const ptr_dict_t* self, const_str_t key);

ssize_t
ptr_list_dict_find_pos(const ptr_list_dict_t* self, const_str_t key);

ssize_t
str_dict_find(const str_dict_t* self, const_str_t key);

ssize_t
str_dict_find_pos(const str_dict_t* self, const_str_t key);

ssize_t
str_list_dict_find(const str_list_dict_t* self, const_str_t key);

ssize_t
str_list_dict_dict_find(const str_list_dict_dict_t* self, const_str_t key);

ssize_t
str_list_dict_find_pos(const str_list_dict_t* self, const_str_t key);

ssize_t
str_list_dict_dict_find_pos(const str_list_dict_dict_t* self, const_str_t key);

bool
str_contains_chr(const_str_t self, char key);

bool
str_contains(const_str_t self, const_str_t key);

bool
str_list_contains(const str_list_t* self, const_str_t key);

bool
str_dict_contains(const str_dict_t* self, const_str_t key);

bool
str_list_dict_contains(const str_list_dict_t* self, const_str_t key);

bool
str_list_dict_dict_contains(const str_list_dict_dict_t* self, const_str_t key);

bool
str_list3_contains(const_str_t str1, const_str_t str2, const_str_t str3, const_str_t key);

bool
ptr_dict_contains(const ptr_dict_t* self, const_str_t key);

bool
str_equal(const_str_t str1, const_str_t str2);

bool
str_list_equal(const str_list_t* list1, const str_list_t* list2);

bool
str_list_list_equal(const str_list_list_t* list1, const str_list_list_t* list2);

str_list_t* restrict
str_dict_keys(const str_dict_t* self);

str_list_t* restrict
str_list_dict_keys(const str_list_dict_t* self);

str_list_t* restrict
str_list_dict_dict_keys(const str_list_dict_dict_t* self);

bool
str_copy(str_t* self, const_str_t* from);

bool
str_list_copy(str_list_t* self, const str_list_t* from);

bool
str_dict_copy(str_dict_t* self, const str_dict_t* from);

bool
str_list_dict_copy(str_list_dict_t* self, const str_list_dict_t* from);

bool
str_list_dict_dict_copy(str_list_dict_dict_t* self, const str_list_dict_dict_t* from);

str_t restrict
str_dup_all(const str_list_t* from);

str_t restrict
str_dup4(const_str_t str1, const_str_t str2, const_str_t str3, const_str_t str4);

str_t restrict
str_dup3(const_str_t str1, const_str_t str2, const_str_t str3);

str_t restrict
str_dup2(const_str_t str1, const_str_t str2);

str_list_t*
str_list_dup(const str_list_t* self);

str_dict_t*
str_dict_dup(const str_dict_t* self);

str_list_dict_t*
str_list_dict_dup(const str_list_dict_t* self);

str_list_dict_dict_t*
str_list_dict_dict_dup(const str_list_dict_dict_t* self);

void
str_sets(str_t* self, str_t from);

void
str_set(str_t* self, const_str_t from);

void
str_list_sets(str_list_t* self, str_list_t* from);

void
str_list_set(str_list_t* self, const str_list_t* from);

void
str_dict_sets(str_dict_t* self, str_dict_t* from);

void
str_dict_set(str_dict_t* self, const str_dict_t* from);

void
str_list_dict_sets(str_list_dict_t* self, str_list_dict_t* from);

void
str_list_dict_set(str_list_dict_t* self, const str_list_dict_t* from);

void
str_list_dict_dict_sets(str_list_dict_dict_t* self, str_list_dict_dict_t* from);

void
str_list_dict_dict_set(str_list_dict_dict_t* self, const str_list_dict_dict_t* from);

void
str_adds(str_t* self, str_t value);

void
str_add(str_t* self, str_t value);

void
str_list_adds(str_list_t* self, str_t value);

void
str_list_add(str_list_t* self, const_str_t value);

void
str_list_adds_all(str_list_t* self, str_list_t* value);

void
str_list_add_all(str_list_t* self, const str_list_t* value);

void
str_list_list_adds(str_list_list_t* self, str_list_t* value);

void
str_list_list_add(str_list_list_t* self, const str_list_t* value);

void
str_list_list_add4(str_list_list_t* self, str_t str1, str_t str2, str_t str3, str_t str4);

void
str_list_list_add3(str_list_list_t* self, str_t str1, str_t str2, str_t str3);

void
str_list_list_add2(str_list_list_t* self, str_t str1, str_t str2);

void
str_list_list_add1(str_list_list_t* self, str_t str1);

void
str_dict_adds(str_dict_t* self, const_str_t key, str_t value);

void
str_dict_add(str_dict_t* self, const_str_t key, const_str_t value);

void
str_list_dict_adds(str_list_dict_t* self, const_str_t key, str_list_t* value);

void
str_list_dict_add(str_list_dict_t* self, const_str_t key, const str_list_t* value);

void
str_list_dict_add1(str_list_dict_t* self, const_str_t key, str_t value);

void
str_list_dict_adds1(str_list_dict_t* self, const_str_t key, str_t value);

void
str_list_dict_dict_adds(str_list_dict_dict_t* self, const_str_t key, str_list_dict_t* value);

void
str_list_dict_dict_add(str_list_dict_dict_t* self, const_str_t key, const str_list_dict_t* value);

void
ptr_dict_adds(ptr_dict_t* self, const_str_t key, void* value);

void
ptr_dict_add(ptr_dict_t* self, const_str_t key, void* value);

void
str_prepend(str_t* str1, const_str_t prefix);

void
str_append(str_t* str1, const_str_t suffix);

void
str_prepends(str_t* str1, str_t prefix);

void
str_appends(str_t* str1, str_t suffix);

void
str_prepend_chr(str_t* str1, char prefix);

void
str_append_chr(str_t* str1, char suffix);

void
str_list_appends(str_list_t* self, str_t value);

void
str_list_append(str_list_t* self, const_str_t value);

void
str_list_prepends(str_list_t* self, str_t value);

void
str_list_prepend(str_list_t* self, const_str_t value);

str_t restrict
str_list_pop(str_list_t* self);

str_t restrict
str_list_prepop(str_list_t* self);

bool
str_startswith(const_str_t self, const_str_t key);

bool
str_endswith(const_str_t self, const_str_t key);

void
str_list_del(str_dict_t* self, const ssize_t pos);

void
str_dict_del(str_dict_t* self, const_str_t key);

str_t restrict
str_cut(const_str_t self, ssize_t a, ssize_t b);

str_t restrict
str_cut_end(const_str_t self, ssize_t a);

str_list_t* restrict
str_list_cut(const str_list_t* self, ssize_t a, ssize_t b);

str_list_t* restrict
str_list_cut_end(const str_list_t* self, ssize_t a);

str_t restrict
str_lstrip(const_str_t self);

str_t restrict
str_strip(const_str_t self);

str_t restrict
str_rstrip(const_str_t self);

str_list_t* restrict
str_split(const_str_t text, const char delim);

str_t
str_join2(const_str_t self, const_str_t from, const_str_t delim);

str_t restrict
str_list_join(const str_list_t* self, const_str_t delim);

str_t restrict
str_list3_join(str_t str1, str_t str2, str_t str3, const_str_t delim);

str_t restrict
str_replace(str_t self, str_t str1, str_t str2);

str_t
str_format(const char* format, ...);

str_t restrict
os_path_join(const_str_t path, const_str_t filename);

void
os_path_prepend(str_t* path, const_str_t prepath);

void
os_path_append(str_t* path, const_str_t subpath);

off_t
os_path_getsize(str_t path);

bool
os_path_isfile(str_t path);

bool
os_path_isdir(str_t path);

bool
os_path_islink(str_t path);

bool
os_path_issocket(str_t path);

bool
os_path_ispipe(str_t path);

double
os_path_getmtime(str_t path);

double
os_path_getctime(str_t path);

double
os_clock_gettime();

double
os_clock_localtime10(double timespec);

double
os_clock_localdate10(double timespec);

str_t restrict
os_path_readlink(str_t path);

bool
os_path_truncate(str_t path);

str_list_t* restrict
os_path_listdir(str_t path);

str_list_t* restrict
os_listdir(str_t path);

str_t restrict
os_path_dirname(str_t path);

str_t restrict
os_path_basename(str_t path);

str_t
os_path_basename_p(str_t path);

str_dict_t* restrict
os_environ_copy();

str_t restrict
str_escapes2(str_t value, char esc, str_t escapes);

str_t restrict
str_to_json(str_t self);

str_t
str_list_to_json(str_list_t* self);

str_t
str_list_list_to_json(str_list_list_t* self);

str_t
str_dict_to_json(str_dict_t* self);

str_t
str_list_dict_to_json(str_list_dict_t* self);

str_t
str_list_dict_dict_to_json(str_list_dict_dict_t* self);

#endif
