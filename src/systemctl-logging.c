#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "systemctl-logging.h"

static int loglevel = LOG_ERROR;

void logg_setlevel(int level) 
{
   loglevel = level;
}

void logg_error(const char* format, ...)
{
  if (loglevel > LOG_ERROR) return;
  char msg[] = "ERROR: ";
  va_list args;
  va_start(args, format);
  ssize_t size = vsnprintf(NULL, 0, format, args);
  va_end(args);
  if (size < 0) return;
  char* buf = malloc(size+2 + strlen(msg));  
  strcpy(buf, msg);
  char* msgbuf = buf + strlen(msg);
  va_start(args, format);
  ssize_t done = vsnprintf(msgbuf, size+1, format, args);
  va_end(args);
  if (done >= 0) {
    msgbuf[done] = '\n';
    fwrite(buf, 1, strlen(msg)+done+1, stderr);
  }
  free(buf);
}

void logg_warning(const char* format, ...)
{
  if (loglevel > LOG_WARNING) return;
  char msg[] = "WARNING: ";
  va_list args;
  va_start(args, format);
  ssize_t size = vsnprintf(NULL, 0, format, args);
  va_end(args);
  if (size < 0) return;
  char* buf = malloc(size+2 + strlen(msg));  
  strcpy(buf, msg);
  char* msgbuf = buf + strlen(msg);
  va_start(args, format);
  ssize_t done = vsnprintf(msgbuf, size+1, format, args);
  va_end(args);
  if (done >= 0) {
    msgbuf[done] = '\n';
    fwrite(buf, 1, strlen(msg)+done+1, stderr);
  }
  free(buf);
}

void logg_info(const char* format, ...)
{
  if (loglevel > LOG_INFO) return;
  char msg[] = "INFO: ";
  va_list args;
  va_start(args, format);
  ssize_t size = vsnprintf(NULL, 0, format, args);
  va_end(args);
  if (size < 0) return;
  char* buf = malloc(size+2 + strlen(msg));  
  strcpy(buf, msg);
  char* msgbuf = buf + strlen(msg);
  va_start(args, format);
  ssize_t done = vsnprintf(msgbuf, size+1, format, args);
  va_end(args);
  if (done >= 0) {
    msgbuf[done] = '\n';
    fwrite(buf, 1, strlen(msg)+done+1, stderr);
  }
  free(buf);
}

void logg_debug(const char* format, ...)
{
  if (loglevel > LOG_DEBUG) return;
  char msg[] = "DEBUG: ";
  va_list args;
  va_start(args, format);
  ssize_t size = vsnprintf(NULL, 0, format, args);
  va_end(args);
  if (size < 0) return;
  char* buf = malloc(size+2 + strlen(msg));  
  strcpy(buf, msg);
  char* msgbuf = buf + strlen(msg);
  va_start(args, format);
  ssize_t done = vsnprintf(msgbuf, size+1, format, args);
  va_end(args);
  if (done >= 0) {
    msgbuf[done] = '\n';
    fwrite(buf, 1, strlen(msg)+done+1, stderr);
  }
  free(buf);
}
