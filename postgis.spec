# build config
%global enable_sfcgal		1
%global enable_gui		0

%global pg_version_major	12

%global pkg_version		%version-%release
%global requires_main		Requires:	%name%{?_isa} = %pkg_version

%global cmd_update_alt		%_sbindir/update-alternatives
%global cmd_pg_config		%_bindir/pg_config-%pg_version_major
%global cmd_sfcgal_config	%_bindir/sfcgal-config
%global cmd_make		%__make -j4 DESTDIR="%buildroot"

%global pg_alternative_prio	%{pg_version_major}0
%global pg_prefix		/usr/postgresql-%pg_version_major

%global pkg_main		pg%pg_version_major-extension
%global pkg_client		pg%pg_version_major-client
%global pkg_docs		pg%pg_version_major-docs
%global pkg_gui			pg%pg_version_major-gui
%global pkg_utils		pg%pg_version_major-utils

Summary:	Geographic Information Systems Extensions to PostgreSQL
Name:		postgis
Version:	3.0.1
Release:	1%{?dist}
License:	GPLv2+
Source0:	postgis-%version.tar.gz
URL:		http://www.postgis.net/

BuildRequires:	gcc
BuildRequires:	postgresql%pg_version_major-devel
BuildRequires:	geos-devel >= 3.8.0
BuildRequires:	pcre-devel
BuildRequires:	libjson-c-devel
BuildRequires:	proj-devel
BuildRequires:	flex
BuildRequires:	libxml2-devel
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libtool
BuildRequires:	gdal-devel >= 3.0.2
BuildRequires:	xsltproc

%{?enable_sfcgal:BuildRequires:	sfcgal-devel}
%{?enable_sfcgal:Requires:	sfcgal}

Requires:	postgresql%pg_version_major
Requires:	geos >= 3.8.0
Requires:	postgresql%pg_version_major-contrib
Requires:	proj
Requires:	xerces-c

Requires:	pcre
Requires:	libjson-c2
Requires:	gdal-libs >= 3.0.2
Requires(post):	%cmd_update_alt

%description
PostGIS adds support for geographic objects to the PostgreSQL object-relational
database. In effect, PostGIS "spatially enables" the PostgreSQL server,
allowing it to be used as a backend spatial database for geographic information
systems (GIS), much like ESRI's SDE or Oracle's Spatial extension. PostGIS
follows the OpenGIS "Simple Features Specification for SQL" and has been
certified as compliant with the "Types and Functions" profile.

%package %pkg_main
Summary:	Geographic Information Systems Extensions to PostgreSQL
Requires:	postgresql%pg_version_major
Requires:	geos >= 3.8.0
Requires:	postgresql%pg_version_major-contrib
Requires:	proj
Requires:	xerces-c

Requires:	pcre
Requires:	libjson-c2
Requires:	gdal-libs >= 3.0.2
Requires(post):	%cmd_update_alt

%description %pkg_main
PostGIS adds support for geographic objects to the PostgreSQL object-relational
database. In effect, PostGIS "spatially enables" the PostgreSQL server,
allowing it to be used as a backend spatial database for geographic information
systems (GIS), much like ESRI's SDE or Oracle's Spatial extension. PostGIS
follows the OpenGIS "Simple Features Specification for SQL" and has been
certified as compliant with the "Types and Functions" profile.

%package %pkg_client
Summary:	Client tools and their libraries of PostGIS
%requires_main

%description %{pg_version_major}-client
The postgis-client package contains the client tools and their libraries
of PostGIS.

%package %pkg_docs
Summary:	Extra documentation for PostGIS

%description %pkg_docs
The postgis-docs package includes PDF documentation of PostGIS.

%if %enable_gui
%package	%pkg_gui
Summary:	GUI for PostGIS
Requires:	postgis%{?_isa} = %pkg_version

%description	%pkg_gui
The postgis-gui package provides a gui for PostGIS.

%files %pkg_gui -f rpmbuild/postgis-gui.files
%endif

%prep
%setup -q -n postgis-%version

%build
./autogen.sh
%configure \
	--without-raster \
	%{?enable_sfcgal:--with-sfcgal=%cmd_sfcgal_config} \
	%{?enable_gui:--with-gui} \
	--with-pgconfig=%cmd_pg_config \
	--enable-rpath \
	--libdir=`%cmd_pg_config --pkglibdir` \
	--without-llvm

%cmd_make -C extensions
%cmd_make -C utils

%install
%__rm -rf %buildroot
rm -Rf rpmbuild
mkdir -p rpmbuild

SHAREDIR=`%cmd_pg_config --sharedir`

%cmd_make install
%cmd_make -C extensions install
%cmd_make -C utils install

touch rpmbuild/postgis-utils.files
mkdir -p %buildroot/$SHAREDIR
( cd utils && find -name "*.pl" )
for i in `cd utils && find -name "*.pl"` ; do
    %__install -m 644 utils/$i %buildroot/$SHAREDIR
    echo "$SHAREDIR/$i" >> rpmbuild/postgis-utils.files
done

( cd %buildroot ; \
    find * -path "*/extension/*.sql"           -exec "echo" "%attr(-,root,root)"   "/{}" ";" ; \
    find * -path "*/extension/*.control"       -exec "echo" "%attr(-,root,root)"   "/{}" ";" ; \
    find * -path "*/contrib/*/*.sql"           -exec "echo" "%attr(-,root,root)"   "/{}" ";" ; \
    find * -path "*/contrib/*/*.pl"            -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    find * -path "*.so"                        -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    find * -name "README.address_standardizer" -exec "echo" "%exclude "            "/{}" ";" ; \
) > rpmbuild/postgis.files

( cd %buildroot ; \
    for f in pgsql2shp raster2pgsql shp2pgsql; do \
        find * -name $f -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    done \
) > rpmbuild/postgis-client.files

%if %enable_gui
( cd %buildroot ; \
    for f in shp2pgsql-gui; do \
        find -name $f -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    done \
    for f in shp2pgsql-gui.desktop shp2pgsql-gui.png; do \
        find -name $f -exec "echo" "%attr(-,root,root)" "/{}" ";" ; \
    done \
) > rpmbuild/postgis-gui.files
%endif

%package %pkg_utils
Summary:	The utils for PostGIS
Requires:	perl-DBD-Pg
%requires_main

%description %pkg_utils
The postgis-utils package provides the utilities for PostGIS.

%post %pkg_utils
%cmd_update_alt --install %_bindir/pgsql2shp postgis-pgsql2shp `%cmd_pg_config --bindir`/pgsql2shp %pg_alternative_prio
%cmd_update_alt --install %_bindir/shp2pgsql postgis-shp2pgsql `%cmd_pg_config --bindir`/shp2pgsql %pg_alternative_prio

%postun %pkg_utils
if [ "$1" -eq 0 ]; then
    # Only remove these links if the package is completely removed from the system (vs.just being upgraded)
    %cmd_update_alt --remove postgis-pgsql2shp `%cmd_pg_config --bindir`/pgsql2shp
    %cmd_update_alt --remove postgis-shp2pgsql `%cmd_pg_config --bindir`/shp2pgsql
fi

%clean
%__rm -rf %buildroot

%files -f rpmbuild/postgis.files
%defattr(-,root,root)
%doc COPYING CREDITS NEWS TODO README.postgis
%license LICENSE.TXT

%files %{pg_version_major}-client -f rpmbuild/postgis-client.files

%files %pkg_docs
%defattr(-,root,root)
%doc doc/html doc/postgis.xml doc/ZMSgeoms.txt loader/README.*
%doc extensions/address_standardizer/README.address_standardizer

%files %pkg_utils -f rpmbuild/postgis-utils.files
%defattr(-,root,root)
%doc utils/README

%changelog
* Mon Feb 17 2020 Enrio Weigelt, metux IT consult <info@metux.net> - 3.0.1-1
- Packaged version 3.0.1 for SLES
