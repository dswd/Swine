rev=0.5

ALL: build

swine_$(rev).orig.tar.gz:
	cp -a ../../swine-$(rev)-src.tar.gz swine_$(rev).orig.tar.gz

unpack: swine_$(rev).orig.tar.gz
	tar -xzvf swine_$(rev).orig.tar.gz
	cp -a swine-$(rev) swine-$(rev).orig
	cp -a meta/* swine-$(rev)

build: unpack
	cd swine-$(rev); debuild; cd ..

rebuild: swine_$(rev).dsc
	dpkg-source -x swine_$(rev).dsc
	cd swine-$(rev); debuild binary; cd ..

clean:
	rm -r swine-$(rev)*
	rm -r swine_$(rev)*