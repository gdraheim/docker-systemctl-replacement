#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "systemctl-logging.h"

static int loglevel = LOG_ERROR;

static int loglevel_stderr = LOG_ERROR;
static int loglevel_logfile[8] = { LOG_ERROR, LOG_ERROR, LOG_ERROR, LOG_ERROR, LOG_ERROR, LOG_ERROR, LOG_ERROR, LOG_ERROR };
static FILE* stream_logfile[8] = { NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, };

int 
logg_getlevel()
{
   return loglevel;
}

void 
logg_setlevel(int level)
{
   loglevel_stderr = level;
   /* loglevel = max(loglevel_logfile,... loglevel_stderr */
   int maxlevel = loglevel_stderr;
   for (int i=0; i < 8; ++i) {
       maxlevel = (maxlevel > loglevel_logfile[i]) ? (loglevel_logfile[i]) : maxlevel;
   }
   /* fprintf(stderr, "OOPS: level %i -> maxlevel %i\n", level, maxlevel); */
   loglevel = maxlevel;
}

int
logg_getlevel_logfile(int logfile)
{
   return loglevel_logfile[logfile];
}

void 
logg_setlevel_logfile(int logfile, int level)
{
   loglevel_logfile[logfile] = level;
   /* loglevel = max(loglevel_logfile,... loglevel_stderr */
   int maxlevel = loglevel_stderr;
   for (int i=0; i < 8; ++i) {
       maxlevel = (maxlevel > loglevel_logfile[i]) ? (loglevel_logfile[i]) : maxlevel;
   }
   loglevel = maxlevel;
}

void 
logg_open_logfile(int logfile, char* filename)
{
    stream_logfile[logfile] = fopen(filename, "a");
    /* fprintf(stderr, "logg_stream %i %s\n", logfile, filename); */
}

void 
logg_stop()
{
    for (int i = 0; i < 8; ++i) {
        if (stream_logfile[i]) {
            fflush(stream_logfile[i]);
            fclose(stream_logfile[i]);
            stream_logfile[i] = NULL;
            loglevel_logfile[i] = LOG_ERROR;
        }
    }
    loglevel = LOG_ERROR;
}

void
logg_write(int level, char* buf, size_t len)
{
    if (loglevel_stderr <= level) {
        fwrite(buf, 1, len, stderr);
    }
    for (int i = 0; i < 8; ++i) {
        if (loglevel_logfile[i] <= level && stream_logfile[i]) {
            fwrite(buf, 1, len, stream_logfile[i]);
        }
    }
}

void 
logg_error(const char* format, ...)
{
  if (loglevel > LOG_ERROR) return;
  char msg[] = "^ ERROR ";
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
    logg_write(LOG_ERROR, buf, strlen(msg)+done+1);
  }
  free(buf);
}

void 
logg_warning(const char* format, ...)
{
  if (loglevel > LOG_WARNING) return;
  char msg[] = "^ WARNING ";
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
    logg_write(LOG_WARNING, buf, strlen(msg)+done+1);
  }
  free(buf);
}

void 
logg_info(const char* format, ...)
{
  if (loglevel > LOG_INFO) return;
  char msg[] = "^ INFO ";
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
    logg_write(LOG_INFO, buf, strlen(msg)+done+1);
  }
  free(buf);
}

void 
logg_debug(const char* format, ...)
{
  if (loglevel > LOG_DEBUG) return;
  char msg[] = "^ DEBUG ";
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
    logg_write(LOG_DEBUG, buf, strlen(msg)+done+1);
  }
  free(buf);
}
