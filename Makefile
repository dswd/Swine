CPP = cpp -undef -x c -nostdinc -P -traditional-cpp -Wundef -imacros layout/definitions.html -Ilayout

LAYOUT = layout/*.html
PAGES_IN = $(shell find . -name '*.html.in')
PAGES_OUT = ${PAGES_IN:.html.in=.html}

%.html : %.html.in
	$(CPP) $< $@

.PHONY: all

all: pages

$(PAGES_OUT) : $(LAYOUT)

pages: $(PAGES_OUT)

clean:
	rm $(PAGES_OUT)
