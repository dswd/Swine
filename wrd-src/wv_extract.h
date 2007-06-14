#ifndef NERESDUMP
#define NERESDUMP

#ifndef U32
#define U32 unsigned int
#endif

#ifndef S32
#define S32 int
#endif

#ifndef U16
#define U16 unsigned short
#endif

#ifndef S16
#define S16 short
#endif

#ifndef U8
#define U8 unsigned char
#endif

#ifndef S8
#define S8 char
#endif

U32 read_32ubit(FILE *in);
U16 read_16ubit(FILE *in);

void write_32ubit(U32 chunk,FILE *in);
void write_16ubit(U16 chunk,FILE *in);

void wvFree(void *ptr);

char * wvFmtMsg(char * fmt, ...);

#ifdef DEBUG
#define wvTrace( args ) wvRealTrace(__FILE__,__LINE__, wvFmtMsg args )
#else
#define wvTrace( args )
#endif

void wvRealTrace(char *,int , char *);

#endif
