#ifndef SYSTEMCTL_REGEX_H
#define SYSTEMCTL_REGEX_H 1
#include <regex.h>

int
regmatch(const char* regex, const char* text, size_t nmatch, regmatch_t pmatch[], char* flags);

#endif
