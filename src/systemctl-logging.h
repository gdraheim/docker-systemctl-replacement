#ifndef SYSTEMCTL_LOGGING_H
#define SYSTEMCTL_LOGGING_H 1

#define LOG_DEBUG 0
#define LOG_INFO 10
#define LOG_WARNING 20
#define LOG_ERROR 30
#define LOG_SEVERE 40
#define LOG_FATAL 50

void logg_setlevel(int level);
int logg_getlevel();

void logg_error(const char* format, ...);
void logg_warning(const char* format, ...);
void logg_info(const char* format, ...);
void logg_debug(const char* format, ...);

#endif
