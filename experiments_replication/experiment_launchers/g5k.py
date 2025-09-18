
def configure_enoslib(en, cluster):
    conf = (
        en.G5kConf.from_settings(
            # job_type=[ "monitor=wattmetre_power_watt"],
            job_name="seektune"
        ).add_machine(
            roles=["server"], cluster=cluster, nodes=1
        )
        .finalize()
    )

    provider = en.G5k(conf)
    return (conf, provider)

def reserve_resources(provider):
    roles, networks = provider.init()

    addr_split = roles["server"][0].address.split('.')
    st_node = addr_split[0]
    st_server_adress = addr_split[0] + '.' + addr_split[1]
    proxy = f"https://{addr_split[0]}.{addr_split[1]}.http.proxy.grid5000.fr/"
    cors = f"https://{addr_split[0]}.{addr_split[1]}.http.proxy.grid5000.fr"

    site = provider.jobs[0].site
    env_line = f'REACT_APP_BACKEND_URL="{proxy}"'

    return (roles, st_server_adress, st_node, env_line, site, cors, proxy)



def deploy_st(seektune_version, roles, en, site, cors, env_line, prefork=False):
    with en.actions(roles=roles["server"]) as a:
        # Setup SSH
        a.copy(src="../g5kuserkey.pub", dest="~/.ssh/", mode="600")
        a.copy(src="../g5kuserkey", dest="~/.ssh/", mode="600")
        a.copy(src="../config", dest="~/.ssh/")

        # Copy spike trigger
        a.copy(src="../trigger_power_spike.sh", dest="/tmp/", mode="700")

        # Clone Git Repos
        a.shell(chdir="/tmp", cmd=f"git clone git@YOUR_GIT_{seektune_version}.git")
        a.shell(chdir="/tmp", cmd=f"git clone git@YOUR_GIT_SERVER.git")

        # Upload database
        a.copy(src=f"../seek-tune-server/db/db.sqlite3", dest=f"/tmp/seek-tune-server/db/db.sqlite3")

        # Configure seek-tune
        a.lineinfile(path=f"/tmp/seek-tune-{seektune_version}/.env", line=env_line, create=True)

        # Install Go
        a.shell(chdir="/tmp", cmd="wget https://go.dev/dl/go1.24.3.linux-amd64.tar.gz")
        a.shell(chdir="/tmp", cmd="rm -rf /usr/local/go && tar -C /usr/local -xzf go1.24.3.linux-amd64.tar.gz")
        a.lineinfile(path="$HOME/.profile", line="export PATH=$PATH:/usr/local/go/bin")
        a.lineinfile(path="$HOME/.bashrc", line="export PATH=$PATH:/usr/local/go/bin")
        
        # Install NVM and Node
        a.shell(cmd="curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | PROFILE=~/.profile bash")
        a.blockinfile(path="$HOME/.bashrc", block="""export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm""",prepend_newline=True,append_newline=True)
        a.shell("nvm install node", executable="/bin/bash")

        # Configure KWollector
        a.lineinfile(path="$HOME/.profile", line=f"export G5K_SITE={site}")
        a.lineinfile(path="$HOME/.bashrc", line=f"export G5K_SITE={site}")

        # Configure CORS_ALLOW_ORIGIN
        a.lineinfile(path="$HOME/.profile", line=f"export CORS_ALLOW_ORIGIN={cors}")
        a.lineinfile(path="$HOME/.bashrc", line=f"export CORS_ALLOW_ORIGIN={cors}")

        # Configure SEEK_TUNE_VERSION
        a.lineinfile(path="$HOME/.profile", line=f"export SEEK_TUNE_VERSION={seektune_version}")
        a.lineinfile(path="$HOME/.bashrc", line=f"export SEEK_TUNE_VERSION={seektune_version}")

        # Setup front end npm
        a.shell(chdir=f"/tmp/seek-tune-{seektune_version}", cmd="npm install")
        a.shell(chdir=f"/tmp/seek-tune-{seektune_version}", cmd="npm run build")

        # Start back end
        a.shell(cmd="tmux new-session -d -s server")
        # a.shell(cmd=f"tmux send-keys -t server.0 \"cd /tmp/seek-tune-server\" ENTER \"go run *.go serve -prefork={prefork} -p=80\" ENTER")
        a.shell(cmd=f"tmux send-keys -t server.0 \"cd /tmp/seek-tune-server\" ENTER \"go build *.go\" ENTER \"./cmdHandlers serve -prefork={prefork} -p=80\" ENTER")