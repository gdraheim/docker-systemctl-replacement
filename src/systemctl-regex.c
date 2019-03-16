#include <string.h>
#include "systemctl-regex.h"
#include "systemctl-logging.h"

/* returns zero on success and otherwise an error code */
int
regmatch(const char* regex, const char* text, size_t nmatch, regmatch_t pmatch[], char* flags) 
{
  int res; /* 0 = success */
  int cflags = REG_EXTENDED;
  if (flags && strchr(flags, 'i'))
      cflags |= REG_ICASE;
  if (flags && strchr(flags, 'm'))
      cflags |= REG_NEWLINE;
  regex_t preg;
  res = regcomp(&preg, regex, cflags);
  if (res) logg_info("bad regex '%s'", regex);
  res = regexec(&preg, text, nmatch, pmatch, 0);
  regfree(&preg);
  return res;
}
