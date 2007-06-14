LIBS = -lm

#these are the debugging flags
#CFLAGS = -I. -g -DDEBUG
CFLAGS = -I.

WMFLIBOBJECTS =	\
	support.o	\
	version.o   \
	winresdump.o

TARGETS = winresdump

all: $(TARGETS)

winresdump: $(WMFLIBOBJECTS)
	$(CC) -o winresdump $(WMFLIBOBJECTS) $(LIBS)

%.o: %.c 
	$(CC) $(CFLAGS) -c $*.c 

clean: 
	rm -rf *.o $(TARGETS) a.out core *.a .pure

distclean: realclean 

realclean: clean
	rm -rf *.bmp *.xpm *.dlg

#  DO  NOT  DELETE THIS LINE -- make depend depends on it.
