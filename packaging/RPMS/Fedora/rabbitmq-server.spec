%define debug_package %{nil}

Name: rabbitmq-server
Version: %%VERSION%%
Release: 1%{?dist}
License: MPLv1.1 and MIT and ASL 2.0 and BSD
Group: %{group_tag}
Source: http://www.rabbitmq.com/releases/rabbitmq-server/v%{version}/%{name}-%{version}.tar.xz
Source1: rabbitmq-server.init
Source2: rabbitmq-server.logrotate
URL: http://www.rabbitmq.com/
BuildArch: noarch
BuildRequires: erlang >= R16B-03, python-simplejson, xmlto, libxslt, gzip, sed, zip, rsync
Requires: erlang >= R16B-03, logrotate
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-%{_arch}-root
Summary: The RabbitMQ server
Requires(post): %%REQUIRES%%
Requires(pre): %%REQUIRES%%

%description
RabbitMQ is an open source multi-protocol messaging broker.

# We want to install into /usr/lib, even on 64-bit platforms
%define _rabbit_libdir %{_exec_prefix}/lib/rabbitmq
%define _rabbit_erllibdir %{_rabbit_libdir}/lib/rabbitmq_server-%{version}
%define _rabbit_server_ocf scripts/rabbitmq-server.ocf
%define _plugins_state_dir %{_localstatedir}/lib/rabbitmq/plugins
%define _rabbit_server_ha_ocf scripts/rabbitmq-server-ha.ocf
%define _set_rabbitmq_policy_sh scripts/set_rabbitmq_policy.sh


%define _maindir %{buildroot}%{_rabbit_erllibdir}


%prep
%setup -q

%build
cp -a docs/README-for-packages %{_builddir}/rabbitmq-server-%{version}/README
make %{?_smp_mflags} dist manpages

%install
rm -rf %{buildroot}

make install install-bin install-man DESTDIR=%{buildroot} PREFIX=%{_exec_prefix} RMQ_ROOTDIR=%{_rabbit_libdir} MANDIR=%{_mandir}

mkdir -p %{buildroot}%{_localstatedir}/lib/rabbitmq/mnesia
mkdir -p %{buildroot}%{_localstatedir}/log/rabbitmq

#Copy all necessary lib files etc.
install -p -D -m 0755 %{S:1} %{buildroot}%{_initrddir}/rabbitmq-server
install -p -D -m 0755 %{_rabbit_server_ocf} %{buildroot}%{_exec_prefix}/lib/ocf/resource.d/rabbitmq/rabbitmq-server
install -p -D -m 0755 %{_rabbit_server_ha_ocf} %{buildroot}%{_exec_prefix}/lib/ocf/resource.d/rabbitmq/rabbitmq-server-ha
install -p -D -m 0644 %{_set_rabbitmq_policy_sh} %{buildroot}%{_exec_prefix}/lib/ocf/resource.d/rabbitmq/set_rabbitmq_policy.sh.example
install -p -D -m 0644 %{S:2} %{buildroot}%{_sysconfdir}/logrotate.d/rabbitmq-server

mkdir -p %{buildroot}%{_sysconfdir}/rabbitmq

mkdir -p %{buildroot}%{_sbindir}
sed -e 's|@SU_RABBITMQ_SH_C@|su rabbitmq -s /bin/sh -c|' \
	-e 's|@STDOUT_STDERR_REDIRECTION@||' \
	< scripts/rabbitmq-script-wrapper \
	> %{buildroot}%{_sbindir}/rabbitmqctl
chmod 0755 %{buildroot}%{_sbindir}/rabbitmqctl
for script in rabbitmq-server rabbitmq-plugins; do \
	cp -a %{buildroot}%{_sbindir}/rabbitmqctl \
	 %{buildroot}%{_sbindir}/$script; \
done

rm %{_maindir}/LICENSE* %{_maindir}/INSTALL

#Build the list of files
echo '%defattr(-,root,root, -)' >%{_builddir}/%{name}.files
find %{buildroot} -path %{buildroot}%{_sysconfdir} -prune -o '!' -type d -printf "/%%P\n" >>%{_builddir}/%{name}.files

%pre

if [ $1 -gt 1 ]; then
  # Upgrade - stop previous instance of rabbitmq-server init.d script
  /sbin/service rabbitmq-server stop
fi

# create rabbitmq group
if ! getent group rabbitmq >/dev/null; then
        groupadd -r rabbitmq
fi

# create rabbitmq user
if ! getent passwd rabbitmq >/dev/null; then
        useradd -r -g rabbitmq -d %{_localstatedir}/lib/rabbitmq rabbitmq \
            -c "RabbitMQ messaging server"
fi

%post
/sbin/chkconfig --add %{name}
if [ -f %{_sysconfdir}/rabbitmq/rabbitmq.conf ] && [ ! -f %{_sysconfdir}/rabbitmq/rabbitmq-env.conf ]; then
    mv %{_sysconfdir}/rabbitmq/rabbitmq.conf %{_sysconfdir}/rabbitmq/rabbitmq-env.conf
else 
    touch %{_sysconfdir}/rabbitmq/rabbitmq-env.conf
fi
chmod -R o-rwx,g-w %{_localstatedir}/lib/rabbitmq/mnesia

%preun
if [ $1 = 0 ]; then
  #Complete uninstall
  /sbin/service rabbitmq-server stop
  /sbin/chkconfig --del rabbitmq-server

  # We do not remove /var/log and /var/lib directories
  # Leave rabbitmq user and group
fi

# Clean out plugin activation state, both on uninstall and upgrade
rm -rf %{_plugins_state_dir}
for ext in rel script boot ; do
    rm -f %{_rabbit_erllibdir}/ebin/rabbit.$ext
done

%files -f ../%{name}.files
%defattr(-,root,root,-)
%attr(0755, rabbitmq, rabbitmq) %dir %{_localstatedir}/lib/rabbitmq
%attr(0750, rabbitmq, rabbitmq) %dir %{_localstatedir}/lib/rabbitmq/mnesia
%attr(0755, rabbitmq, rabbitmq) %dir %{_localstatedir}/log/rabbitmq
%dir %{_sysconfdir}/rabbitmq
%{_initrddir}/rabbitmq-server
%config(noreplace) %{_sysconfdir}/logrotate.d/rabbitmq-server
%doc LICENSE*
%doc README
%doc docs/rabbitmq.config.example

%clean
rm -rf %{buildroot}

%changelog
* Tue Dec 22 2015 michael@rabbitmq.com 3.6.0-1
- New Upstream Release

* Tue Dec 15 2015 michael@rabbitmq.com 3.5.7-1
- New Upstream Release

* Wed Oct 7 2015 michael@rabbitmq.com 3.5.6-1
- New Upstream Release

* Thu Sep 24 2015 jean-sebastien@rabbitmq.com 3.5.5-3
- Fix bashism in rabbitmq-script-wrapper

* Thu Sep 24 2015 jean-sebastien@rabbitmq.com 3.5.5-1
- New Upstream Release

* Tue Jul 21 2015 michael@rabbitmq.com 3.5.4-1
- New Upstream Release

* Fri May 22 2015 jean-sebastien@rabbitmq.com 3.5.3-1
- New Upstream Release

* Tue May 12 2015 jean-sebastien@rabbitmq.com 3.5.2-1
- New Upstream Release

* Thu Apr 2 2015 michael@rabbitmq.com 3.5.1-1
- New Upstream Release

* Wed Mar 11 2015 jean-sebastien@rabbitmq.com 3.5.0-1
- New Upstream Release

* Wed Feb 11 2015 michael@rabbitmq.com 3.4.4-1
- New Upstream Release

* Tue Jan 6 2015 jean-sebastien@rabbitmq.com 3.4.3-1
- New Upstream Release

* Wed Nov 26 2014 simon@rabbitmq.com 3.4.2-1
- New Upstream Release

* Wed Oct 29 2014 simon@rabbitmq.com 3.4.1-1
- New Upstream Release

* Tue Oct 21 2014 simon@rabbitmq.com 3.4.0-1
- New Upstream Release

* Mon Aug 11 2014 simon@rabbitmq.com 3.3.5-1
- New Upstream Release

* Tue Jun 24 2014 simon@rabbitmq.com 3.3.4-1
- New Upstream Release

* Mon Jun 16 2014 simon@rabbitmq.com 3.3.3-1
- New Upstream Release

* Mon Jun 9 2014 simon@rabbitmq.com 3.3.2-1
- New Upstream Release

* Tue Apr 29 2014 simon@rabbitmq.com 3.3.1-1
- New Upstream Release

* Wed Apr 2 2014 simon@rabbitmq.com 3.3.0-1
- New Upstream Release

* Mon Mar 3 2014 simon@rabbitmq.com 3.2.4-1
- New Upstream Release

* Thu Jan 23 2014 emile@rabbitmq.com 3.2.3-1
- New Upstream Release

* Tue Dec 10 2013 emile@rabbitmq.com 3.2.2-1
- New Upstream Release

* Wed Oct 23 2013 emile@rabbitmq.com 3.2.0-1
- New Upstream Release

* Thu Aug 15 2013 simon@rabbitmq.com 3.1.5-1
- New Upstream Release

* Tue Jun 25 2013 tim@rabbitmq.com 3.1.3-1
- New Upstream Release

* Mon Jun 24 2013 tim@rabbitmq.com 3.1.2-1
- New Upstream Release

* Mon May 20 2013 tim@rabbitmq.com 3.1.1-1
- Test release

* Wed May 1 2013 simon@rabbitmq.com 3.1.0-1
- New Upstream Release

* Tue Dec 11 2012 simon@rabbitmq.com 3.0.1-1
- New Upstream Release

* Fri Nov 16 2012 simon@rabbitmq.com 3.0.0-1
- New Upstream Release

* Fri Dec 16 2011 steve@rabbitmq.com 2.7.1-1
- New Upstream Release

* Tue Nov 8 2011 steve@rabbitmq.com 2.7.0-1
- New Upstream Release

* Fri Sep 9 2011 tim@rabbitmq.com 2.6.1-1
- New Upstream Release

* Fri Aug 26 2011 tim@rabbitmq.com 2.6.0-1
- New Upstream Release

* Mon Jun 27 2011 simon@rabbitmq.com 2.5.1-1
- New Upstream Release

* Thu Jun 9 2011 jerryk@vmware.com 2.5.0-1
- New Upstream Release

* Thu Apr 7 2011 Alexandru Scvortov <alexandru@rabbitmq.com> 2.4.1-1
- New Upstream Release

* Tue Mar 22 2011 Alexandru Scvortov <alexandru@rabbitmq.com> 2.4.0-1
- New Upstream Release

* Thu Feb 3 2011 simon@rabbitmq.com 2.3.1-1
- New Upstream Release

* Tue Feb 1 2011 simon@rabbitmq.com 2.3.0-1
- New Upstream Release

* Mon Nov 29 2010 rob@rabbitmq.com 2.2.0-1
- New Upstream Release

* Tue Oct 19 2010 vlad@rabbitmq.com 2.1.1-1
- New Upstream Release

* Tue Sep 14 2010 marek@rabbitmq.com 2.1.0-1
- New Upstream Release

* Mon Aug 23 2010 mikeb@rabbitmq.com 2.0.0-1
- New Upstream Release

* Wed Jul 14 2010 Emile Joubert <emile@rabbitmq.com> 1.8.1-1
- New Upstream Release

* Tue Jun 15 2010 Matthew Sackman <matthew@rabbitmq.com> 1.8.0-1
- New Upstream Release

* Mon Feb 15 2010 Matthew Sackman <matthew@lshift.net> 1.7.2-1
- New Upstream Release

* Fri Jan 22 2010 Matthew Sackman <matthew@lshift.net> 1.7.1-1
- New Upstream Release

* Mon Oct 5 2009 David Wragg <dpw@lshift.net> 1.7.0-1
- New upstream release

* Wed Jun 17 2009 Matthias Radestock <matthias@lshift.net> 1.6.0-1
- New upstream release

* Tue May 19 2009 Matthias Radestock <matthias@lshift.net> 1.5.5-1
- Maintenance release for the 1.5.x series

* Mon Apr 6 2009 Matthias Radestock <matthias@lshift.net> 1.5.4-1
- Maintenance release for the 1.5.x series

* Tue Feb 24 2009 Tony Garnock-Jones <tonyg@lshift.net> 1.5.3-1
- Maintenance release for the 1.5.x series

* Mon Feb 23 2009 Tony Garnock-Jones <tonyg@lshift.net> 1.5.2-1
- Maintenance release for the 1.5.x series

* Mon Jan 19 2009 Ben Hood <0x6e6562@gmail.com> 1.5.1-1
- Maintenance release for the 1.5.x series

* Wed Dec 17 2008 Matthias Radestock <matthias@lshift.net> 1.5.0-1
- New upstream release

* Thu Jul 24 2008 Tony Garnock-Jones <tonyg@lshift.net> 1.4.0-1
- New upstream release

* Mon Mar 3 2008 Adrien Pierard <adrian@lshift.net> 1.3.0-1
- New upstream release

* Wed Sep 26 2007 Simon MacMullen <simon@lshift.net> 1.2.0-1
- New upstream release

* Wed Aug 29 2007 Simon MacMullen <simon@lshift.net> 1.1.1-1
- New upstream release

* Mon Jul 30 2007 Simon MacMullen <simon@lshift.net> 1.1.0-1.alpha
- New upstream release

* Tue Jun 12 2007 Hubert Plociniczak <hubert@lshift.net> 1.0.0-1.20070607
- Building from source tarball, added starting script, stopping

* Mon May 21 2007 Hubert Plociniczak <hubert@lshift.net> 1.0.0-1.alpha
- Initial build of server library of RabbitMQ package
