{ pkgs ? import <nixpkgs> {}
, pythonPackages ? pkgs.python27Packages
}:

rec {
  jsonpickle = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "jsonpickle";
    version = "0.9.4";

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/cc/5e/6ecbd1d27524fcafeed4f6156f47a2a79e31e4bfa383e329e9ba93c7f3ee/jsonpickle-0.9.4.tar.gz";
      sha256 = "0f7rs3v30xhwdmnqhqn9mnm8nxjq3yhp6gdzkg3z8m8lynhr968x";
    };
  };

  deepdiff = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "deepdiff";
    version = "3.1.2";

    propagatedBuildInputs = [ jsonpickle ];

    format = "wheel";

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/6f/56/9b61c4ecc6e16e1de85f474540c314434d7e2ec6f3c03fe4e0e3cc92a873/deepdiff-3.1.2-py2-none-any.whl";
      sha256 = "033hn1a3didw782fnknqbw118cangy1gf30icpv28p73qcd7dli8";
    };
  };

  filepath = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "filepath";
    version = "0.1";

    buildInputs = [ pythonPackages.twisted ];

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/eb/0f/3c5ebbfd6fa6904181ecece2b6737d797a033479a193984e7e84c1d84185/${name}.tar.gz";
      sha256 = "15wf9krsbjzsllw3h1wx3rwy9lzy8hr1jgjiisg0ipqqn7bgw3cb";
    };

    checkPhase = ''
      trial filepath
    '';
  };

  pem = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "pem";
    version = "16.1.0";

    buildInputs = [
      pkgs.libffi
      pkgs.openssl
      pythonPackages.pytest
      pythonPackages.pycparser
      pythonPackages.certifi
      pythonPackages.coverage
      pythonPackages.pretend
      pythonPackages.pytest
      pythonPackages.pyopenssl
      pythonPackages.incremental
      pythonPackages.twisted
    ];

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/4f/06/cf51103b48532565adb42f562389d364e2075947c5b1cba79fdc7eae4e8d/${name}.tar.gz";
      sha256 = "0w5i2ywcrjhdv7wjpm9519adcr87braskkbwxs9b6pbfrllvmx2b";
    };

    checkPhase = ''
      py.test
    '';
  };

  extras100 = pythonPackages.extras.override rec {
    name = "${pname}-${version}";
    pname = "extras";
    version = "1.0.0";
    src = pkgs.fetchurl {
      url = "mirror://pypi/e/extras/${name}.tar.gz";
      sha256 = "0khvm08rcwm62wc47j8niyl6h13f8w51c8669ifivjdr23g3cbhk";
    };
    checkPhase = ''
      python -m unittest extras.tests.test_suite
    '';
  };

  testtools220 = pythonPackages.testtools.override rec {
    name = "${pname}-${version}";
    pname = "testtools";
    version = "2.2.0";
    propagatedBuildInputs =
      with pythonPackages;
      [ pbr python_mimeparse extras100 fixtures300 lxml unittest2 ];

    src = pkgs.fetchurl {
      url = "mirror://pypi/t/testtools/${name}.tar.gz";
      sha256 = "042qlqymy9m40w30fg3gj20wahmac9jphnsfwb8f8k3fg9h0dxl0";
    };
    patches = [];

    # `python -m unittest testtools.tests.test_suite` fails because testtools
    # test suite requires testscenarios and testscenarios requires testtools
    # and I don't know how to resolve this circularity for Nix.
    doCheck = false;
  };

  pyrsistent0_12_0 = pythonPackages.pyrsistent.override rec {
    name = "pyrsistent-0.12.0";

    src = pkgs.fetchurl {
      url = "mirror://pypi/p/pyrsistent/${name}.tar.gz";
      sha256 = "1k7kjj1nyzyk1jfiawlg16s1nsmypwmfqsq9yc3iba1m6jq9rq9p";
    };

    # Test suite requires an old version of Hypothesis :(
    doCheck = false;
  };

  eliot = pythonPackages.buildPythonPackage rec {
    name = "eliot-${version}";
    version = "0.12.0";

    propagatedBuildInputs =
      with pythonPackages;
      [ six zope_interface pyrsistent0_12_0 ];

    src = pkgs.fetchurl {
      url = "mirror://pypi/e/eliot/${name}.tar.gz";
      sha256 = "07k9lbn3aym05h69rw1xiyjh4wp9swcvay3z2w0f1pqab5h0q8xs";
    };

    # Tests fail because eliot-prettyprint can't be found on the PATH
    doCheck = false;
  };

  tree-format = pythonPackages.buildPythonPackage rec {
    name = "tree-format-0.1.1";

    format = "wheel";

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/50/a4/ea87a1808a130ccd5b9a47b1cfe82d4f75bc630c094a62179a46da7209c4/tree_format-0.1.1-py2-none-any.whl";
      sha256 = "0y664nz2sg3mzn95fpq4nq08fyi14pyp7cm3jii783bvgfwpb1j9";
    };
  };

  eliot-tree = pythonPackages.buildPythonPackage rec {
    name = "eliot-tree-17.0.0";

    format = "wheel";

    propagatedBuildInputs =
      with pythonPackages;
      [ toolz jmespath six iso8601 termcolor tree-format eliot ];

    src = pkgs.fetchurl {
      # Wheels have underscores?  Argh or whatever.
      url = "https://pypi.python.org/packages/02/d9/585af501ee09d797f59ebe94369a0d2a20d3bf239795e663c7b8b055e228/eliot_tree-17.0.0-py2-none-any.whl";
      sha256 = "0fim44kqkx5hv5spx700jpc7xn8922b926vymz53v256j7jh3svy";
    };

    checkPhase = ''
    # foo
    '';
  };

  pyopenssl16_2_0 = pythonPackages.buildPythonPackage rec {
    name = "pyopenssl-${version}";
    version = "16.2.0";

    src = pkgs.fetchurl {
      url = "mirror://pypi/p/pyOpenSSL/pyOpenSSL-${version}.tar.gz";
      sha256 = "0vji4yrfshs15xpczbhzhasnjrwcarsqg87n98ixnyafnyxs6ybp";
    };

    preCheck = ''
      sed -i 's/test_set_default_verify_paths/noop/' tests/test_ssl.py
    '';

    checkPhase = ''
      runHook preCheck
      export LANG="en_US.UTF-8";
      py.test;
      runHook postCheck
    '';

    buildInputs =
    with pythonPackages;
    [ pkgs.openssl pytest pkgs.glibcLocales ];

    propagatedBuildInputs =
    with pythonPackages;
    [ cryptography pyasn1 idna ];
  };

  service-identity = pythonPackages.service-identity.override {
    propagatedBuildInputs = with pythonPackages; [
      characteristic pyasn1 pyasn1-modules pyopenssl16_2_0 idna attrs
    ];
  };

  foolscap = pythonPackages.foolscap.override {
    propagatedBuildInputs =
    with pythonPackages;
    [ mock twisted pyopenssl16_2_0 service-identity ];
  };

  tahoe_lafs = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "tahoe-lafs";
    version = "1.11.0";

    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/73/9e/53757536146aa197ff2310c90152487b3dc286d1dedd0c522eb51287d7e7/tahoe-lafs-1.11.0.tar.bz2";
      sha256 = "0hrp87rarbmmpnrxk91s83h6irkykds3pl263dagcddbdl5inqdi";
    };

    buildInputs = [ pythonPackages.tox ];

    propagatedBuildInputs =
      with pythonPackages; [
        pyasn1
        pyasn1-modules
        simplejson
        dateutil
        zfec
        pycrypto
        pyopenssl16_2_0
        pycryptopp
        service-identity
        foolscap
        twisted
        (nevow.override {
            postInstall = null;
          })
      ];

    # Lots of stuff fails. :(
    doCheck = false;
  };

  txaws021post5 = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "txAWS";
    version = "0.2.1.post5";

    propagatedBuildInputs =
      with pythonPackages;
      [ dateutil twisted ];

    src = pkgs.fetchurl {
      url = "https://tahoe-lafs.org/deps/txAWS-0.2.1.post5.tar.gz";
      sha256 = "1mwxpkr3ivsq35cp6s84f0yfmavyskqdf9drhvk5jvnmi6xfppq2";
    };

    # Test suite fails with some networking errors.
  };

  constantly = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "constantly";
    version = "15.1.0";

    src = pkgs.fetchurl {
      url = "mirror://pypi/c/constantly/${name}.tar.gz";
      sha256 = "0dgwdla5kfpqz83hfril716inm41hgn9skxskvi77605jbmp4qsq";
    };

    # Constantly doesn't ship with *any* tests!
    doCheck = false;
  };

  txaws030dev0 = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "txAWS";
    version = "0.3.0.dev0";

    src = pkgs.fetchFromGitHub {
      owner = "twisted";
      repo = "txaws";
      rev = "2c1a075caa24c9fa3c4e84dbe206196a4faa279c";
      sha256 = "1jdswmpkncvljsjlszl8968q5c2s0569k9hs3c5rqnf54czj2lq5";
    };

    buildInputs =
      with pythonPackages;
      [ treq ];

    propagatedBuildInputs =
      with pythonPackages;
      [ venusian attrs dateutil incremental pyrsistent0_12_0 constantly pyopenssl16_2_0 pem service-identity twisted lxml ];

    checkPhase = ''
      trial txaws
    '';
  };

  fixtures300 = pythonPackages.fixtures.override rec {
    name = "fixtures-3.0.0";
    src = pkgs.fetchurl {
      url = "mirror://pypi/f/fixtures/${name}.tar.gz";
      sha256 = "1vxj29bzz3rd4pcy51d05wng9q9dh4jq6wx92yklsm7i6h1ddw7w";
    };
  };

  stripe = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "stripe";
    version = "1.41.1";

    # Tests require network connectivity and there's no easy way to disable
    # them. ~ C.
    doCheck = false;

    src = pkgs.fetchurl {
      url = "mirror://pypi/s/${pname}/${name}.tar.gz";
      sha256 = "0zvffvq933ia5w5ll6xhx2zgvppgc6zc2mxhc6f0kypw5g2fxvz5";
    };

    buildInputs = with pythonPackages; [ unittest2 mock ];
    propagatedBuildInputs = with pythonPackages; [ requests2 ];

    meta = {
      homepage = "https://github.com/stripe/stripe-python";
      description = "Stripe Python bindings";
      license = pkgs.stdenv.lib.licenses.mit;
    };
  };

  oauth2client400 = pythonPackages.oauth2client.override rec {
    name = "oauth2client-4.0.0";

    src = pkgs.fetchurl {
      url = "mirror://pypi/o/oauth2client/${name}.tar.gz";
      sha256 = "1irqqap2zibysf8dba8sklfqikia579srd0phm5n754ni0h59gl0";
    };
  };

  pykube = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "pykube";
    version = "0.14.0";

    propagatedBuildInputs =
      with pythonPackages;
      [ six pyyaml tzlocal oauth2client400 requests2 requests_oauthlib ];

    src = pkgs.fetchurl {
      url = "mirror://pypi/p/${pname}/${name}.tar.gz";
      sha256 = "1vb51gzrm1ks2x0lgmwbqbr9gs7c0234lf0z9cjgyxl8cq43cfr7";
    };
  };

  txkube000 = pythonPackages.buildPythonPackage rec {
    name = "${pname}-${version}";
    pname = "txkube";
    version = "0.0.0";

    buildInputs =
      with pythonPackages;
      [ testtools220 hypothesis fixtures300 eliot-tree ];

    propagatedBuildInputs =
      with pythonPackages;
      [ zope_interface attrs pyrsistent0_12_0 incremental service-identity pyopenssl16_2_0 twisted pem eliot dateutil pykube eliot treq pem pyyaml klein ];


    src = pkgs.fetchFromGitHub {
      owner = "LeastAuthority";
      repo = "txkube";
      rev = "444fec5a1bfe66410ee56c867a022de9a19275c1";
      sha256 = "07rbckc2f171wspns0fr6fpck982si73p20cjkm1d3mw0ygxnlrk";
    };

    checkPhase = ''
    trial txkube
    '';
  };

  lae = pythonPackages.buildPythonPackage rec {
    name = "s4-${version}";
    version = "1.0.0";

    buildInputs =
      with pythonPackages;
      [ testtools220 hypothesis mock fixtures300 pelican klein treq eliot-tree ];

    propagatedBuildInputs =
      with pythonPackages; [
        pem
        deepdiff
        pyopenssl16_2_0
        filepath
        eliot
        stripe
        Fabric
        attrs
        jinja2
        twisted
        txaws021post5
        tahoe_lafs
        txkube000
      ];

    src =
    let
      excludedDirs = [ ".git" ".hypothesis" "_trial_temp" "dist" "docs" "docker" "k8s" ];
      excludedFiles = [ ".travis.yml" ".dockerignore" ".gitignore" "requirements.txt" ];
      goodSource = (path: type:
        ! (type == "directory" && (builtins.elem (baseNameOf path) excludedDirs)) &&
	! (type == "regular" && (builtins.elem (baseNameOf path) excludedFiles))
      );
    in
      builtins.filterSource goodSource ./..;

    checkPhase = ''
      trial lae_util lae_site lae_automation
    '';

    meta = {
      license = pkgs.stdenv.lib.licenses.gpl2;
    };
  };

  s4-common-image = pkgs.dockerTools.buildImage {
      name = "leastauthority/s4-common";
      runAsRoot = ''
        #!${pkgs.stdenv.shell}
        ${pkgs.dockerTools.shadowSetup}
        groupadd --system lae
        useradd --system --gid lae --home-dir /app/data lae
      '';
      contents = pkgs.python27.buildEnv.override {
        extraLibs = [ pkgs.dash pkgs.coreutils lae ];
        ignoreCollisions = true;
        postBuild = "\${out}/bin/twistd --help > /dev/null";
      };
    };
}
