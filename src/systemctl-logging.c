#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

void systemctl_error(const char* format, ...)
{
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

void systemctl_warning(const char* format, ...)
{
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

void systemctl_info(const char* format, ...)
{
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

void systemctl_debug(const char* format, ...)
{
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
