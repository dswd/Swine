%.py : %.ui
	pyuic $< >$@

rev = 0.6
ui_files = MainWindow.ui AboutDialog.ui ProgramDialog.ui RunnerDialog.ui IconDialog.ui
ui_files_py = MainWindow.py AboutDialog.py ProgramDialog.py RunnerDialog.py IconDialog.py
images = images/*.png
py_files = swine.py swinecli.py swinerun.py swinelib.py shortcutlib.py
deb_dir = package-files/deb
buildfiles = Makefile
resources = resources/*
sources = $(py_files) $(ui_files) $(images) README LICENSE $(buildfiles) $(resources)
distfiles = $(py_files) $(ui_files_py) $(images) README LICENSE $(resources)

ALL: compile

deb-clean:
	cd $(deb_dir); export rev=$(rev); make clean

deb-build: swine-$(rev)-src.tar.gz
	cd $(deb_dir); export rev=$(rev); make build

deb-rebuild: swine-$(rev)-src.tar.gz
	cd $(deb_dir); export rev=$(rev); make rebuild

swine-$(rev).tar.gz: compile $(distfiles)
	mkdir swine-$(rev)
	rsync -R $(distfiles) swine-$(rev)
	tar -czvf swine-$(rev).tar.gz swine-$(rev)
	rm -r swine-$(rev)

swine-$(rev)-src.tar.gz: $(sources) $(buildfiles)
	mkdir swine-$(rev)
	rsync -R $(sources) swine-$(rev)
	tar -czvf swine-$(rev)-src.tar.gz swine-$(rev)
	rm -r swine-$(rev)

compile: $(ui_files_py)

dist: swine-$(rev).tar.gz swine-$(rev)-src.tar.gz

clean:
	rm -rf $(ui_files_py) *.pyc *.tar.gz *~

install: compile
	mkdir -p $(DESTDIR)/usr/lib/swine/
	cp $(py_files) $(ui_files_py) resources/wislib resources/wisrun $(DESTDIR)/usr/lib/swine
	mkdir -p $(DESTDIR)/usr/share/swine/images/
	cp -r $(images) $(DESTDIR)/usr/share/swine/images
	ln -s ../../share/swine/images $(DESTDIR)/usr/lib/swine
	ln -s ../lib/swine/swine.py $(DESTDIR)/usr/bin/swine
	ln -s ../lib/swine/swinecli.py $(DESTDIR)/usr/bin/swinecli
	ln -s ../lib/swine/swinerun.py $(DESTDIR)/usr/bin/swinerun
	mkdir -p $(DESTDIR)/usr/share/applications
	cp resources/swine.desktop $(DESTDIR)/usr/share/applications/swine.desktop
	cp resources/swine-extensions.desktop $(DESTDIR)/usr/share/applications/swine-extensions.desktop

deb: deb-clean deb-build
