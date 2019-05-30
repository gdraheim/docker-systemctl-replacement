#include "systemctl-types.h"
#include "systemctl-shlex.h"
#include "systemctl-logging.h"
#include <stdlib.h>
#include <wchar.h>

#ifndef READNEXT
#define READNEXT 0
#endif

/*
 * compare with
 * https://github.com/python/cpython/blob/master/Lib/shlex.py
 */

typedef struct _shlex
{
    const_str_t input;
    int point;
    /* ... */
    bool posix;
    const char* commenters;
    const char* wordchars;
    const char* whitespace;
    bool whitespace_split;
    const char* quotes;
    const char* escape;
    const char* escapedquotes;
    char state;
    str_list_t* pushback;
    int lineno;
    int debug;
    str_t token;
} shlex_t;

void
shlex_init(shlex_t* self)
{
    self->input = NULL;
    self->point = 0;
    /* ... */
    self->posix = false;
    self->commenters = "#";
    self->wordchars = "abcdfeghijklmnopqrstuvwxyz"
                       "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_";
    self->whitespace = " \t\r\n";
    self->whitespace_split = false;
    self->quotes = "'\"";
    self->escape = "\\";
    self->escapedquotes = "\"";
    self->state = ' ';
    self->pushback = str_list_new();
    self->lineno = 1;
    self->debug = 0;
    self->token = NULL;
}

void
shlex_null(shlex_t* self) 
{
    str_list_free(self->pushback);
    str_null(&self->token);
}

void
shlex_begin(shlex_t* self, str_t value) 
{
    self->input = value;
    self->point = 0;
}

str_t 
shlex_readnext(shlex_t* self) 
{
    /* https://www.tldp.org/HOWTO/Unicode-HOWTO-6.html */
    if (self->input) {
        mbstate_t mb = {0};
        size_t len = mbrlen(self->input + self->point, MB_CUR_MAX, &mb);
        if (len > 0) {
            str_t value = str_cut(self->input, self->point, self->point + len);
            self->point += len;
            if (READNEXT)
                logg_debug("readnext '%s'", value);
            return value;
        }
        if (READNEXT)
            logg_debug("readnext EOF");
        return NULL; /* at end or error */
    }
    if (READNEXT)
        logg_debug("readnext NULL");
    return NULL; /* as if EOF */
}

str_t restrict
shlex_readline(shlex_t* self)
{
    str_t result = str_dup("");
    while (true) {
        str_t eol = shlex_readnext(self);
        if (! eol || *eol == '\n') {
            break;
        }
        str_adds(&result, eol);
    }
    return result;
}

str_t restrict
shlex_get_token(shlex_t* self)
{
    if (! str_list_empty(self->pushback)) {
        return str_list_pop(self->pushback);
    }
    return shlex_read_token(self);
}

str_t restrict
shlex_read_token(shlex_t* self)
{
    str_t next_token = NULL; /* from input */
    bool quoted = false;
    char escapedstate = ' ';
    while (true) {
        str_sets(&next_token, shlex_readnext(self));
        char nextchar = '\0';
        if (next_token)
            nextchar = next_token[0];
        if (nextchar == '\n')
            self->lineno += 1;
        if (! self->state) {
            str_sets(&self->token, str_dup(""));
            /* past end of file */
            break;
        } else if (self->state == ' ') {
            if (! nextchar) {
                self->state = nextchar; /* end of file */
                break;
            } else if (str_contains_chr(self->whitespace, nextchar)) {
                if (! str_empty(self->token) || (self->posix && quoted)) {
                    break; /* emit current token */
                } else {
                    continue;
                }
            } else if (str_contains_chr(self->commenters, nextchar)) {
                str_free(shlex_readline(self));
                self->lineno += 1;
            } else if (self->posix && str_contains_chr(self->escape, nextchar)) {
                escapedstate = 'a';
                self->state = nextchar;
            } else if (str_contains_chr(self->wordchars, nextchar)) {
                str_set(&self->token, next_token);
                self->state = 'a';
            } else if (str_contains_chr(self->quotes, nextchar)) {
                if (! self->posix)
                    str_set(&self->token, next_token);
                self->state = nextchar;
            } else if (self->whitespace_split) {
                str_set(&self->token, next_token);
                self->state = 'a';
            } else {
                str_set(&self->token, next_token);
                self->state = 'a';
                if (! str_empty(self->token) || (self->posix && quoted)) {
                    break; /* emit current token */
                } else {
                    continue;
                }
            }
        } else if (str_contains_chr(self->quotes, self->state)) {
            quoted = true;
            if (! nextchar) { /* end of file */
                self->state = nextchar;
                break;
            } else if (nextchar == self->state) {
                if (! self->posix) {
                    str_sets(&self->token, str_dup2(self->token, next_token));
                    self->state = ' ';
                } else {
                    self->state = 'a';
                }
            } else if (self->posix && str_contains_chr(self->escape, nextchar) 
                && str_contains_chr(self->escapedquotes, self->state)) {
                escapedstate = self->state;
                self->state = nextchar;
            } else {
                str_sets(&self->token, str_dup2(self->token, next_token));
            }
        } else if (str_contains_chr(self->escape, self->state)) {
            if (! nextchar) { /* end of file */
                break;
            }
            /* In posix shells, only the quote itself or the escape
            *  character may be escaped with quotes */
            if (str_contains_chr(self->quotes, escapedstate) &&
                nextchar != self->state && nextchar != escapedstate) {
                str_append_chr(&self->token, self->state);
            }
            str_sets(&self->token, str_dup2(self->token, next_token));
            self->state = escapedstate;
        } else if (self->state == 'a') {
            if (! nextchar) {
                self->state = nextchar; /* end of file */
                break;
            } else if (str_contains_chr(self->whitespace, nextchar)) {
                self->state = ' ';
                if (! str_empty(self->token) || (self->posix && quoted)) {
                    break; /* emit current token */
                } else {
                    continue;
                }
            } else if (str_contains_chr(self->commenters, nextchar)) {
                str_free(shlex_readline(self));
                self->lineno += 1;
                if (self->posix) {
                    self->state = ' ';
                    if (! str_empty(self->token) || (self->posix && quoted)) {
                        break; /* emit current token */
                    } else {
                        continue;
                    }
                }
            } else if (self->posix && str_contains_chr(self->quotes, nextchar)) {
                self->state = nextchar;
            } else if (self->posix && str_contains_chr(self->escape, nextchar)) {
                escapedstate = 'a';
                self->state = nextchar;
            } else if (str_contains_chr(self->wordchars, nextchar)
                || str_contains_chr(self->quotes, nextchar)
                || self->whitespace_split) {
                str_sets(&self->token, str_dup2(self->token, next_token));
            } else {
                str_list_add(self->pushback, next_token);
                self->state = ' ';
                if (! str_empty(self->token) || (self->posix && quoted)) {
                    break; /* emit current token */
                } else {
                    continue;
                }
            }
        }
    }
    str_t result = self->token;
    self->token = NULL;
    if (self->posix && ! quoted && str_empty(result)) {
        str_null(&result);
    }
    str_null(&next_token);
    if (READNEXT)
        logg_debug("TOKEN '%s'", result);
    return result;
}

/* returns zero on success and otherwise an error code */
str_list_t* restrict
shlex_splits(str_t value, const_str_t options) 
{
   str_list_t* result = str_list_new();
   if (! options) options = "xn";
   shlex_t shlex;
   shlex_init(&shlex);
   if (str_contains_chr(options, 'p'))
       shlex.posix = true;
   if (str_contains_chr(options, 'x'))
       shlex.posix = false;
   if (str_contains_chr(options, 'n'))
       shlex.commenters = "";
   if (str_contains_chr(options, 'w'))
       shlex.whitespace_split = true;
   shlex_begin(&shlex, value);
   while (true) {
      str_t token = shlex_get_token(&shlex);
      if (! token)
          break;
      if (! shlex.posix && str_empty(token)) {
          str_free(token);
          break;
      }
      str_list_adds(result, token);
   }
   shlex_null(&shlex);
   return result;
}

str_list_t* restrict
shlex_split(str_t value) 
{
    /* Python shlex.split operates in POSIX mode by default, 
       but uses non-POSIX mode if the posix argument is false. */
    return shlex_splits(value, "pnw");
}

str_list_t* restrict
shlex_parse(str_t value) 
{
    /* and this one is non-posix with comments */
    return shlex_splits(value, "xw");
}
