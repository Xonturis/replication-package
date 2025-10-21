# Local Computing vs. Cloud Computing: An Empirical Study of Energy Consumption -- Replication Package And Dataset

This repository contains all the elements necessary to reproduce the experiment for our paper.

> You will find mentions to "LoFi" in the code, this is due to early variable naming. We changed from "LoFi" (Local-First) to LP (Local Processing) later. To avoid random bug introduction, we didn't modify the variable names in the code (so treat any mention to LoFi as a mention to Local Processing (LP)). Also, the git repository for seektune-lofi, and the values in the `mode` column in table `GSPT_Test`, are not renamed.

## Project structure

The following sections present the project structure.

### Experiment replication

If you want to use the Grid5000 infrastructure, you will need access to it, you can ask for an access here:
https://www.grid5000.fr/w/Grid5000:Get_an_account#Access_for_a_conference_peer_review \
Then you will need to setup [Grid5000](https://www.grid5000.fr/w/Getting_Started) and [EnOSlib](https://discovery.gitlabpages.inria.fr/enoslib/jupyter/setup_for_use_in_g5k.html).

If you want to use the Greenspector (https://greenspector.com/en/home/) testbed, you will need access to it, you will have to ask them directly if that is possible. Otherwise, since the user scenario is simple and short, you can install an energy monitoring software and play the scenario by hand or with an automation software.

If you have a Greenspector access, for the script `collect_gspt.py`, you will need to connect to your Greenspector dashboard and get your bearer token from the network packets, there are no official Greenspector API for what we do in our script unfortunately.

In this repository, in folder `experiments_replication`, you will find the four folders corresponding to the four git repos needed for the scripts:
- `seek-tune-stress`: The stress test
- `seek-tune-server`: The seektune backend
- `seek-tune-lofi`: The LoFi front end version
- `seek-tune-saas`: The SaaS front end version

Then, you will need to upload them to a git repo with the correct name (the names above). Finally, in the different python files for reproducing our experiments, where the placeholder `YOUR_GIT_XXX` is written replace with the corresponding git url where `XXX` is `STRESS`, `SERVER`, `LOFI` or `SAAS`. This is important because the scripts will automatically download the code to the G5K node from the given git url. Don't forget to create your public and private key to give to the server so it can clone your private repo. Also change the config file to reflect the url of your gitlab server (if necessary). 

If you don't plan on modifying any of the code, you can use the repositories we used for our paper here:
- `seek-tune-stress`: https://gitlab.inria.fr/lsiffre/seek-tune-stress
- `seek-tune-server`: https://gitlab.inria.fr/lsiffre/seek-tune-server
- `seek-tune-lofi`: https://gitlab.inria.fr/lsiffre/seek-tune-lofi
- `seek-tune-saas`: https://gitlab.inria.fr/lsiffre/seek-tune-saas

### Figures and Tables reproduction
All the python code is available to reproduce the figures presented in the paper. For convenience, the given database already contains all the needed data.

For the figures:
| Figure | File                                                        |
|--------|-------------------------------------------------------------|
| 5      | gspt_analysis/metric_step/stats_listenstep_version_phone.py |
| 6      | gspt_analysis/data_conso/plot_cumul.py                      |
| 7      | g5k_analysis/impact_load_plot.py                            |
| 8      | gspt_analysis/impact_delay_load/compil_delay_srv.py         |

For the tables:
| Table  | File                                                        |
|--------|-------------------------------------------------------------|
| 2      | gspt_analysis/metric_step/stats_listenstep_version_phone.py |

### Raw dataset
All raw data are in the `raw_dataset` folder. There are more data in this file than in the database as we performed more tests that have been discarded because finally not used in our analysis. For example we tried to observe if the C-States were introducing a bias or not, we concluded not since the power and throughput measurment at high throughput are the same. But they are in the raw dataset if you want to take a look.

For two tests on the phones, the delay for the openingService task is longer since it was sometime taking slightly more time on the S22. This does not affect the other measurements.

## Contact
Feel free to contact us if you need any information!
Corresponding Author : Lylian Siffre ( lylian.siffre[at]imt-atlantique[dot]fr )