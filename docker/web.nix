{ pkgs ? import <nixpkgs> {} }:

let
  s4 = pkgs.callPackage ./s4.nix {
    pythonPackages = pkgs.python27Packages;
    pkgs = pkgs;
  };
  web = { python, s4, pkgs }:
    pkgs.dockerTools.buildImage {
      name = "leastauthority/web";
      runAsRoot = ''
        #!${pkgs.stdenv.shell}
        ${pkgs.dockerTools.shadowSetup}
        groupadd --system web
        useradd --system --gid web --home-dir /app/data web
      '';

      contents = python.buildEnv.override {
        extraLibs = [ s4 ];
	ignoreCollisions = true;
	postBuild = "\${out}/bin/twistd --help > /dev/null";
      };

      config = {
        Cmd =
          let
            port = "8443";
            cert = "/app/k8s_secrets/website-cert.pem";
            key = "/app/k8s_secrets/website-key.pem";
            chain = "/app/k8s_secrets/website-chain.pem";
          in
            [
              "/bin/python" "-u" "/${python.sitePackages}/lae_site/main.py"
              "--secure-port=ssl:${port}:${cert}:${key}:${chain}"
              "--insecure-port=tcp:8080"
              "--redirect-to-port=\${S4_SERVICE_PORT_HTTPS_SERVER}"
              "--signup-furl-path=/app/flapp-data/signup.furl"
              "--stripe-secret-api-key-path=/app/k8s_secrets/stripe-private.key"
              "--stripe-publishable-api-key-path=/app/k8s_secrets/stripe-publishable.key"
              "--site-logs-path /app/data/logs/sitelogs"
              "--interest-path /app/data/emails.csv"
              "--subscriptions-path /app/data/subscriptions.csv"
              "--service-confirmed-path /app/data/service_confirmed.csv"
            ];
        ExposedPorts = {
          "8443/tcp" = {};
        };
        WorkingDir = "/app/run";
        Volumes = {
          "/app/data" = {};
        };
      };
    };
in
  web {
    python = pkgs.python27;
    s4 = s4;
    pkgs = pkgs;
  }

# nix-channel --add https://nixos.org/channels/nixpkgs-unstable nixpkgs
# nix-channel --update
# nix-build -A pythonFull '<nixpkgs>'
