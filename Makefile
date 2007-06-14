%.py : %.ui
	pyuic $< >$@

ui_files = MainWindow.ui RunDialog.ui AboutDialog.ui ShortcutDialog.ui
ui_files_py = MainWindow.py RunDialog.py AboutDialog.py ShortcutDialog.py
images = images/*.png images/16x16/*.png
py_files = swine.py swinecli.py swinelib.py
sources = $(py_files) $(ui_files) $(images) README LICENSE
distfiles = $(py_files) $(ui_files_py) $(images) README LICENSE
buildfiles = Makefile

ALL: compile

swine.tar.gz: $(distfiles)
	tar -czvf swine.tar.gz $(distfiles)

swine-src.tar.gz: $(sources) $(buildfiles)
	tar -czvf swine-src.tar.gz $(sources) $(buildfiles)

compile: $(ui_files_py)

dist: swine.tar.gz swine-src.tar.gz

clean:
	rm $(ui_files_py) *.pyc *.tar.gz *~