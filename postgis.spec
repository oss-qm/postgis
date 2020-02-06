%global enable_sfcgal		1
%global enable_gui		0

%global cmd_update_alt		%_sbindir/update-alternatives
%global cmd_pg_config		%_bindir/pg_config-%postgres_major
%global cmd_sfcgal_config	%_bindir/sfcgal-config
%global cmd_make		%__make %{?_smp_mflags} DESTDIR="%buildroot"

%global pg_alternative_prio	%{postgres_major}0

%global pkg_main	postgresql%{postgres_major}-postgis
%global pkg_client	%pkg_main-client
%global pkg_docs	%pkg_main-docs
%global pkg_gui		%pkg_main-gui
%global pkg_utils	%pkg_main-utils
%global pkg_devel	%pkg_main-devel

%global requires_main	Requires:	%pkg_main%{?_isa} = %version-%release

Summary:	Geographic Information Systems Extensions to PostgreSQL
Name:		postgis
Version:	2.5.3
Release:	mtx.12%{?dist}
License:	GPLv2+
Source0:	postgis-%version.tar.gz
URL:		http://www.postgis.net/

BuildRequires:	gcc
BuildRequires:	postgresql%postgres_major-devel
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

%description
PostGIS adds support for geographic objects to the PostgreSQL object-relational
database. In effect, PostGIS "spatially enables" the PostgreSQL server,
allowing it to be used as a backend spatial database for geographic information
systems (GIS), much like ESRI's SDE or Oracle's Spatial extension. PostGIS
follows the OpenGIS "Simple Features Specification for SQL" and has been
certified as compliant with the "Types and Functions" profile.

%prep
%setup -q -n postgis-%version

%if 0%{?postgres_major:1}
echo "Building against PostgreSQL %postgres_major"
%else
echo "postgres_major needs to be defined" >&2
exit 1
%endif

%build
./autogen.sh
%configure \
	--with-raster \
	%{?enable_sfcgal:--with-sfcgal=%cmd_sfcgal_config} \
	%{?enable_gui:--with-gui} \
	--with-pgconfig=%cmd_pg_config \
	--libdir=`%cmd_pg_config --pkglibdir`

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

touch rpmbuild/%pkg_utils.files
mkdir -p %buildroot/$SHAREDIR
for i in `cd utils && find -name "*.pl"` ; do
    %__install -m 644 utils/$i %buildroot/$SHAREDIR
    echo "$SHAREDIR/$i" >> rpmbuild/%pkg_utils.files
done

( cd %buildroot ; \
    find * -path "*/extension/*.sql"           -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    find * -path "*/extension/*.control"       -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    find * -path "*/contrib/*/*.sql"           -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    find * -path "*/contrib/*/*.pl"            -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    find * -path "*.so*"                       -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    find * -name "README.address_standardizer" -exec "echo" "%exclude "            "/{}" ";" ; \
) > rpmbuild/%pkg_main.files

( cd %buildroot ; \
    for f in pgsql2shp raster2pgsql shp2pgsql; do \
        find * -name $f -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    done \
) > rpmbuild/%pkg_client.files

( cd %buildroot ; \
    find * -name "*.h"  -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    find * -name "*.a"  -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    find * -name "*.la" -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
) > rpmbuild/%pkg_devel.files

%if %enable_gui
( cd %buildroot ; \
    for f in shp2pgsql-gui; do \
        find -name $f -exec "echo" "%attr(755,root,root)" "/{}" ";" ; \
    done \
    for f in shp2pgsql-gui.desktop shp2pgsql-gui.png; do \
        find -name $f -exec "echo" "%attr(644,root,root)" "/{}" ";" ; \
    done \
) > rpmbuild/%pkg_gui.files
%endif

%clean
%__rm -rf %buildroot

### main package

%package -n %pkg_main
Summary:	Geographic Information Systems Extensions to PostgreSQL
Requires:	postgresql%postgres_major
Requires:	postgresql%postgres_major-contrib
Requires(post):	%cmd_update_alt

%description -n %pkg_main
PostGIS adds support for geographic objects to the PostgreSQL object-relational
database. In effect, PostGIS "spatially enables" the PostgreSQL server,
allowing it to be used as a backend spatial database for geographic information
systems (GIS), much like ESRI's SDE or Oracle's Spatial extension. PostGIS
follows the OpenGIS "Simple Features Specification for SQL" and has been
certified as compliant with the "Types and Functions" profile.

%files -n %pkg_main -f rpmbuild/%pkg_main.files
%defattr(-,root,root)
%doc COPYING CREDITS NEWS TODO README.postgis
%license LICENSE.TXT

### docs package

%package -n %pkg_docs
Summary:	Extra documentation for PostGIS

%description -n %pkg_docs
The postgis-docs package includes PDF documentation of PostGIS.

%files -n %pkg_docs
%defattr(-,root,root)
%doc doc/html doc/postgis.xml doc/ZMSgeoms.txt loader/README.*
%doc extensions/address_standardizer/README.address_standardizer

### gui package

%if %enable_gui
%package -n %pkg_gui
Summary:	GUI for PostGIS
%requires_main

%description -n %pkg_gui
The postgis-gui package provides a gui for PostGIS.

%files -n %pkg_gui -f rpmbuild/%pkg_gui.files
%endif

### utils package

%package -n %pkg_utils
Summary:	The utils for PostGIS
Requires:	perl-DBD-Pg
%requires_main

%description -n %pkg_utils
The postgis-utils package provides the utilities for PostGIS.

%files -n %pkg_utils -f rpmbuild/%pkg_utils.files
%defattr(-,root,root)
%doc utils/README

%post -n %pkg_utils
%cmd_update_alt --install %_bindir/pgsql2shp postgis-pgsql2shp `%cmd_pg_config --bindir`/pgsql2shp %pg_alternative_prio
%cmd_update_alt --install %_bindir/shp2pgsql postgis-shp2pgsql `%cmd_pg_config --bindir`/shp2pgsql %pg_alternative_prio

%postun -n %pkg_utils
if [ "$1" -eq 0 ]; then
    # Only remove these links if the package is completely removed from the system (vs.just being upgraded)
    %cmd_update_alt --remove postgis-pgsql2shp `%cmd_pg_config --bindir`/pgsql2shp
    %cmd_update_alt --remove postgis-shp2pgsql `%cmd_pg_config --bindir`/shp2pgsql
fi

### client package

%package -n %pkg_client
Summary:	Client tools and their libraries of PostGIS
%requires_main

%description -n %pkg_client
The postgis-client package contains the client tools and their libraries
of PostGIS.

%files -n %pkg_client -f rpmbuild/%pkg_client.files

### devel package

%package -n %pkg_devel
Summary:	Development package PostGIS
%requires_main

%description -n %pkg_devel
The postgis-devel package provides development files for PostGIS.

%files -n %pkg_devel -f rpmbuild/%pkg_devel.files

### global changelog

%changelog
* Mon Feb 17 2020 Enrio Weigelt, metux IT consult <info@metux.net> - 2.5.3-8
- Packaged for SLES 12
