%.py : %.ui
	pyuic $< >$@

rev = 0.41
ui_files = MainWindow.ui AboutDialog.ui ProgramDialog.ui
ui_files_py = MainWindow.py AboutDialog.py ProgramDialog.py
images = images/*.png
py_files = swine.py swinecli.py swinelib.py shortcutlib.py Registry.py
wrd_dir = wrd-src
wrd_sources = $(wrd_dir)/README $(wrd_dir)/Makefile $(wrd_dir)/CHANGELOG \
	$(wrd_dir)/newexe.h $(wrd_dir)/resfmt.h $(wrd_dir)/winresdump.h $(wrd_dir)/wv_extract.h \
	$(wrd_dir)/support.c $(wrd_dir)/version.c $(wrd_dir)/winresdump.c
wrd_bin = winresdump
sources = $(py_files) $(ui_files) $(images) README LICENSE $(wrd_sources)
distfiles = $(py_files) $(ui_files_py) $(images) README LICENSE $(wrd_bin)
buildfiles = Makefile

ALL: compile

winresdump-compile:
	cd $(wrd_dir); make; cd .. ; cp $(wrd_dir)/winresdump $(wrd_bin)

winresdump-clean:
	cd $(wrd_dir); make clean; cd ..

swine-$(rev).tar.gz: compile $(distfiles)
	mkdir swine-$(rev)
	rsync -R $(distfiles) swine-$(rev)
	tar -czvf swine-$(rev).tar.gz swine-$(rev)
	rm -r swine-$(rev)

swine-$(rev)-src.tar.gz: $(sources) $(buildfiles)
	mkdir swine-$(rev)-src
	rsync -R $(distfiles) swine-$(rev)-src
	tar -czvf swine-$(rev)-src.tar.gz swine-$(rev)-src
	rm -r swine-$(rev)-src

compile: $(ui_files_py) winresdump-compile

dist: swine-$(rev).tar.gz swine-$(rev)-src.tar.gz

clean: winresdump-clean
	rm -rf $(ui_files_py) *.pyc *.tar.gz *~ $(wrd_bin)

install: compile
	mkdir -p $(DESTDIR)/usr/share/swine/lib/
	cp $(py_files) $(ui_files_py) $(DESTDIR)/usr/share/swine/lib/
	mkdir -p $(DESTDIR)/usr/share/swine/lib/images/
	cp -r $(images) $(DESTDIR)/usr/share/swine/lib/images
	mkdir -p $(DESTDIR)/usr/share/swine/bin/
	cp $(wrd_bin) $(DESTDIR)/usr/share/swine/bin/
	ln -s ../share/swine/lib/swine.py $(DESTDIR)/usr/bin/swine
