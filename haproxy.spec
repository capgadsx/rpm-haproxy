%define haproxy_user    haproxy
%define haproxy_group   %{haproxy_user}
%define haproxy_home    %{_localstatedir}/lib/haproxy
%define major_version 2.0
%define version 2.0.1
%define release 2

Summary: HA-Proxy is a TCP/HTTP reverse proxy for high availability environments
Name: haproxy
Version: %{version}
Release: %{release}.el7
License: GPL
Group: System Environment/Daemons
URL: http://www.haproxy.org/
Source0: https://www.haproxy.org/download/%{major_version}/src/%{name}-%{version}.tar.gz
Source1: %{name}.cfg
Source2: %{name}.service
Source3: %{name}.logrotate
Source4: %{name}.syslog.el7
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: pcre-devel make gcc openssl-devel
Requires(pre):      shadow-utils
Requires:           rsyslog
BuildRequires:      systemd-units systemd-devel
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd

%description
HA-Proxy is a TCP/HTTP reverse proxy which is particularly suited for high
availability environments. Indeed, it can:
- route HTTP requests depending on statically assigned cookies
- spread the load among several servers while assuring server persistence
  through the use of HTTP cookies
- switch to backup servers in the event a main one fails
- accept connections to special ports dedicated to service monitoring
- stop accepting connections without breaking existing ones
- add/modify/delete HTTP headers both ways
- block requests matching a particular pattern

It needs very little resource. Its event-driven architecture allows it to easily
handle thousands of simultaneous connections on hundreds of instances without
risking the system's stability.

%prep
%setup -q

# We don't want any perl dependecies in this RPM:
%define __perl_requires /bin/true

%build
regparm_opts=
%ifarch %ix86 x86_64
regparm_opts="USE_REGPARM=1"
%endif

RPM_BUILD_NCPUS="`/usr/bin/nproc 2>/dev/null || /usr/bin/getconf _NPROCESSORS_ONLN`";

# Default opts
systemd_opts=
pcre_opts="USE_PCRE=1"
USE_TFO=
USE_NS=
systemd_opts="USE_SYSTEMD=1"
pcre_opts="USE_PCRE=1 USE_PCRE_JIT=1"
USE_TFO=1
USE_NS=1

%{__make} -j$RPM_BUILD_NCPUS %{?_smp_mflags} CPU="generic" TARGET="linux-glibc" ${systemd_opts} ${pcre_opts} USE_OPENSSL=1 USE_ZLIB=1 ${regparm_opts} ADDINC="%{optflags}" USE_LINUX_TPROXY=1 USE_THREAD=1 USE_TFO=${USE_TFO} USE_NS=${USE_NS} ADDLIB="%{__global_ldflags}" EXTRA_OBJS="contrib/prometheus-exporter/service-prometheus.o"

%install
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

%{__install} -d %{buildroot}%{_sbindir}
%{__install} -d %{buildroot}%{_sysconfdir}/%{name}
%{__install} -d %{buildroot}%{_sysconfdir}/%{name}/errors
%{__install} -d %{buildroot}%{_mandir}/man1/
%{__install} -d %{buildroot}%{_sysconfdir}/logrotate.d
%{__install} -d %{buildroot}%{_sysconfdir}/rsyslog.d
%{__install} -d %{buildroot}%{_localstatedir}/log/%{name}

%{__install} -s %{name} %{buildroot}%{_sbindir}/

%{__install} -c -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{name}/haproxy.cfg
%{__install} -c -m 755 examples/errorfiles/*.http %{buildroot}%{_sysconfdir}/%{name}/errors/
%{__install} -c -m 755 doc/%{name}.1 %{buildroot}%{_mandir}/man1/
%{__install} -c -m 755 %{SOURCE4} %{buildroot}%{_sysconfdir}/rsyslog.d/49-%{name}.conf
%{__install} -c -m 755 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

%{__install} -s %{name} %{buildroot}%{_sbindir}/
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}.service

%clean
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

%pre
getent group %{haproxy_group} >/dev/null || \
       groupadd -g 188 -r %{haproxy_group}
getent passwd %{haproxy_user} >/dev/null || \
       useradd -u 188 -r -g %{haproxy_group} -d %{haproxy_home} \
       -s /sbin/nologin -c "%{name}" %{haproxy_user}
exit 0

%post
%systemd_post %{name}.service
systemctl restart rsyslog.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service
systemctl restart rsyslog.service

%files
%defattr(-,root,root)
%doc CHANGELOG README examples/*.cfg doc/architecture.txt doc/configuration.txt doc/intro.txt doc/management.txt doc/proxy-protocol.txt
%doc %{_mandir}/man1/%{name}.1*
%dir %{_sysconfdir}/%{name}
%{_sysconfdir}/%{name}/errors
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/%{name}/%{name}.cfg
%attr(0755,root,root) %{_sbindir}/%{name}
%dir %{_localstatedir}/log/%{name}
%attr(0644,root,root) %config %{_sysconfdir}/logrotate.d/%{name}
%attr(0644,root,root) %config %{_sysconfdir}/rsyslog.d/49-%{name}.conf

%if 0%{?el6} || 0%{?amzn1}
%attr(0755,root,root) %config %_sysconfdir/rc.d/init.d/%{name}
%endif

%if 0%{?el7} || 0%{?amzn2}
%attr(-,root,root) %{_unitdir}/%{name}.service
%endif

%changelog
* Sat Jul 06 2019 Carlos Ponce <cponce@alumnos.inf.utfsm.cl>
- Remove support for Amazon Linux and EL6
- Add support for Prometheus metrics exporter

* Tue Jun 18 2019 David Bezemer <info@davidbezemer.nl>
- First build of HAproxy 2.0.0

* Tue Jun 18 2019 David Bezemer <info@davidbezemer.nl>
- Update to HAproxy 1.9.8

* Wed Sep 26 2018 J. Casalino <casalino@adobe.com>
- Update to HAproxy 1.8.14

* Fri Jun 29 2018 Topher Cullen <topher@shawlite.com>
- Update to HAproxy 1.8.12
- Add support for Amazon Linux 2

* Fri May 18 2018 David Bezemer <info@davidbezemer.nl>
- Update to HAproxy 1.8.8

* Fri Feb 23 2018 J. Casalino <casalino@adobe.com>
- Add support for Amazon Linux (Fedora-based)

* Mon Feb 12 2018 David Bezemer <info@davidbezemer.nl>
- Update to HAproxy 1.8.4

* Fri Jan 26 2018 Kamil Herbik <kamil.herbik@rst.com.pl>
- Update for HAproxy 1.8

* Mon Jul 31 2017 David Bezemer <info@davidbezemer.nl>
- Update for HAproxy 1.7.8

* Thu Jun 08 2017 David Bezemer <info@davidbezemer.nl>
- Update for HAproxy 1.7.5
- Remove duplicate pcre-devel requirement

* Sun Jan 15 2017 David Bezemer <info@davidbezemer.nl>
- Update for HAproxy 1.7.2

* Sun Oct 23 2016 David Bezemer <info@davidbezemer.nl>
- Add systemd compatibility

* Sat Oct 22 2016 David Bezemer <info@davidbezemer.nl>
- reworked installation structure
- included rsylog config for logging
- copy default error files
- updated to 1.6.9
