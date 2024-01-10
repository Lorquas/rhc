include Makefile

outdir ?= $(PWD)/outdir
spec ?= $(PWD)

SOURCEDIR := $(shell rpmbuild -E %_sourcedir)
SRCRPMDIR := $(shell rpmbuild -E %_srcrpmdir)

SHORTNAME = $(shell basename $(PWD))
LONGNAME = $(SHORTNAME)
BRANDNAME = $(SHORTNAME)
VERSION := $(shell echo $(VERSION) | awk -F. '{printf("%d.%d.%d", $$1, $$2, $$3+1)}')
RELEASE = $(shell printf "0.%s.git.%s" $(shell git rev-list $(shell git describe --tags --abbrev=0 --always | tr -d '\n')..HEAD --count | tr -d '\n') $(shell git rev-parse --short HEAD | tr -d '\n'))
PKGNAME = $(SHORTNAME)

.PHONY: srpm tarball
$(spec)/rhc.spec: $(spec)/.copr/rhc.spec.in
	sed \
	    -e 's,[@]SHORTNAME[@],$(SHORTNAME),g' \
		-e 's,[@]LONGNAME[@],$(LONGNAME),g' \
		-e 's,[@]BRANDNAME[@],$(BRANDNAME),g' \
		-e 's,[@]VERSION[@],$(VERSION),g' \
		-e 's,[@]RELEASE[@],$(RELEASE),g' \
		-e 's,[@]PKGNAME[@],$(PKGNAME),g' \
		-e 's,[@]TOPICPREFIX[@],$(TOPICPREFIX),g' \
		-e 's,[@]DATAHOST[@],$(DATAHOST),g' \
		-e 's,[@]PROVIDER[@],$(PROVIDER),g' \
		$< > $@

tarball: $(spec)/rhc.spec
	make PKGNAME=$(PKGNAME) VERSION=$(VERSION)-$(RELEASE) dist

srpm: $(spec)/rhc.spec tarball deps
	mkdir -p $(SOURCEDIR)
	mkdir -p $(SRCRPMDIR)
	mkdir -p $(outdir)
	install -D -m644 $(PKGNAME)-$(VERSION)-$(RELEASE).tar.gz $(SOURCEDIR)
	spectool --get-files --source 1 --sourcedir $(spec)/rhc.spec
	spectool --get-files --source 2 --sourcedir $(spec)/rhc.spec
	rpmbuild -bs $(spec)/rhc.spec
	install -D -m644 $(SRCRPMDIR)/*.rpm $(outdir)/

deps:
	dnf install -y golang git rpmdevtools
