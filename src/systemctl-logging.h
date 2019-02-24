#ifndef SYSTEMCTL_LOGGING_H
#define SYSTEMCTL_LOGGING_H 1

void systemctl_error(const char* format, ...);
void systemctl_warning(const char* format, ...);
void systemctl_info(const char* format, ...);
void systemctl_debug(const char* format, ...);

#endif
