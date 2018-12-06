# If any of the following macros should be set otherwise,
# you can wrap any of them with the following conditions:
# - %%if 0%%{centos} == 7
# - %%if 0%%{?rhel} == 7
# - %%if 0%%{?fedora} == 23
# Or just test for particular distribution:
# - %%if 0%%{centos}
# - %%if 0%%{?rhel}
# - %%if 0%%{?fedora}
#
# Be aware, on centos, both %%rhel and %%centos are set. If you want to test
# rhel specific macros, you can use %%if 0%%{?rhel} && 0%%{?centos} == 0 condition.
# (Don't forget to replace double percentage symbol with single one in order to apply a condition)

# Generate devel rpm
%global with_devel 1
# Build project from bundled dependencies
%global with_bundled 0
# Build with debug info rpm
%global with_debug 0
# Run tests in check section
%global with_check 1
# Generate unit-test rpm
%global with_unit_test 1

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         vishvananda
%global repo            netlink
# https://github.com/vishvananda/netlink
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          f5a6f697a596c788d474984a38a0ac4ba0719e93
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           golang-%{provider}-%{project}-%{repo}
Version:        0
Release:        0.17.git%{shortcommit}%{?dist}
Summary:        Simple netlink library for go
License:        ASL 2.0
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} aarch64 x86_64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%description
The netlink package provides a simple netlink library for go.
Netlink is the interface a user-space program in linux uses to communicate
with the kernel. It can be used to add and remove interfaces, set ip addresses
and routes, and configure ipsec. Netlink communication requires elevated
privileges, so in most cases this code needs to be run as root. Since low-level
netlink messages are inscrutable at best, the library attempts to provide
an api that is loosely modeled on the CLI provied by iproute2.
Actions like ip link add will be accomplished via a similarly named function
like AddLink(). This library began its life as a fork of the netlink
functionality in docker/libcontainer but was heavily rewritten to improve
testability,performance, and to add new functionality like ipsec xfrm handling.

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check} && ! 0%{?with_bundled}
BuildRequires: golang(github.com/vishvananda/netns)
%endif

Requires:      golang(github.com/vishvananda/netns)

Provides:      golang(%{import_path}) = %{version}-%{release}
Provides:      golang(%{import_path}/nl) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test}
%package unit-test
Summary:         Unit tests for %{name} package

%if 0%{?with_check}
#Here comes all BuildRequires: PACKAGE the unit tests
#in %%check section need for running
%endif

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test
%{summary}

This package contains unit tests for project
providing packages with %{import_path} prefix.
%endif

%prep
%setup -q -n %{repo}-%{commit}

%build

%install
# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%dir %%{gopath}/src/%%{import_path}/." >> devel.file-list
# find all *.go but no *_test.go files and generate devel.file-list
for file in $(find . \( -iname "*.go" -or -iname "*.s" \) \! -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test-devel.file-list
for file in $(find . -iname "*_test.go") ; do
    dirprefix=$(dirname $file)
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$dirprefix
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test-devel.file-list

    while [ "$dirprefix" != "." ]; do
        echo "%%dir %%{gopath}/src/%%{import_path}/$dirprefix" >> devel.file-list
        dirprefix=$(dirname $dirprefix)
    done
done
%endif

%if 0%{?with_devel}
sort -u -o devel.file-list devel.file-list
%endif

%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%else
# No dependency directories so far

export GOPATH=%{buildroot}/%{gopath}:%{gopath}
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

#%%gotest %%{import_path}
%gotest %{import_path}/nl
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%if 0%{?with_devel}
%files devel -f devel.file-list
%license LICENSE
%doc README.md
%dir %{gopath}/src/%{provider}.%{provider_tld}/%{project}
%endif

%if 0%{?with_unit_test}
%files unit-test -f unit-test-devel.file-list
%license LICENSE
%doc README.md
%endif

%changelog
* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.17.gitf5a6f69
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.16.gitf5a6f69
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 24 2017 Jan Chaloupka <jchaloup@redhat.com> - 0-0.15.gitf5a6f69
- Bump to upstream f5a6f697a596c788d474984a38a0ac4ba0719e93
  related: #1398575

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.14.gite73bad4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.13.gite73bad4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.12.gite73bad4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Dec 14 2016 Jan Chaloupka <jchaloup@redhat.com> - 0-0.11.gite73bad4
- Polish the spec file
  related: #1398575

* Tue Dec 13 2016 Jan Chaloupka <jchaloup@redhat.com> - 0-0.10.gite73bad4
- Bump to upstream e73bad418fd727ed3a02830b1af1ad0283a1de6c
  related: #1398575

* Tue Dec 13 2016 Jan Chaloupka <jchaloup@redhat.com> - 0-0.9.git1e2e08e
- Fix tests for ppc64le architecture (upstream patch)
  resolves: #1398575

* Thu Jul 21 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0-0.8.git1e2e08e
- https://fedoraproject.org/wiki/Changes/golang1.7

* Mon Feb 22 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0-0.7.git1e2e08e
- https://fedoraproject.org/wiki/Changes/golang1.6

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0-0.6.git1e2e08e
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Nov 26 2015 jchaloup <jchaloup@redhat.com> - 0-0.5.git1e2e08e
- Bump to upstream 1e2e08e8a2dcdacaae3f14ac44c5cfa31361f270
  related: #1248155

* Wed Jul 29 2015 jchaloup <jchaloup@redhat.com> - 0-0.4.git991a7a2
- Update of spec file to spec-2.0
  resolves: #1248155

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0-0.3.git991a7a2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed May 20 2015 jchaloup <jchaloup@redhat.com> - 0-0.2.git991a7a2
- Bump to upstream 991a7a2fa7c073968fb27f36669df199b1fdf412
- Remove runtime dependency on golang
- Add license macro
  related: #1164176

* Fri Nov 14 2014 jchaloup <jchaloup@redhat.com> - 0-0.1.git2187ba6
- First package for Fedora
  resolves: #1164176
