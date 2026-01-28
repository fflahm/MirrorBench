# MirrorBench: Evaluating Self-centric Intelligence in MLLMs by Introducing a Mirror

<p align="center">
   <a href="https://fflahm.github.io/mirror-bench-page/" target="_blank">🌐 Project Page</a> | <a href="https://huggingface.co/datasets/flahm/MirrorBenchAssets" target="_blank">🤗 Data</a> | <a href="#" target="_blank">📃 Paper(TBD) </a>
</p>

<div style="width: 100%; text-align: center; margin:auto;">
    <img style="width:100%" src="teasers/fig2.png">
</div>

## Tested Environments

This repository has been tested and verified to work correctly on the following configurations:

### Windows
- OS: Windows 11
- GPU: NVIDIA GeForce RTX 3080 Laptop
- CUDA: 12.4

### Linux
- OS: Ubuntu 20.04
- GPU: NVIDIA GeForce RTX 5090
- CUDA: 12.8

## Installation

### Setup Simulation
Download and unzip NVIDIA Isaac Sim 4.5.0 (Standalone) from the official download page, choosing the link corresponding to your operating system:
https://docs.isaacsim.omniverse.nvidia.com/4.5.0/installation/download.html.

Then set the environment variable `ISAACSIM_ROOT`, for example: `set ISAACSIM_ROOT= "D:\isaac-sim-4.5.0"` (Windows) or `export ISAACSIM_ROOT=/home/user/isaac-sim-4.5.0` (Linux).

### Install Dependencies
Run:
```shell
# Windows
%ISAACSIM_ROOT%\python.bat -m pip install openai==1.79.0

# Linux
$ISAACSIM_ROOT/python.sh -m pip install openai==1.79.0
```

### Download Assets
Run:
```shell
pip install huggingface_hub
python download.py
```
The necessary assets will be downloaded to the `assets` directory.

## Evaluation

TODOs: Args; Results

### Model Type

- **Proprietary**: To evaluate proprietary MLLMs with `OpenAI` client, you need to edit your own `api_key` and `base_url` in `agent.py`.
- Open-source(TBD)
- Your own model(TBD)
- Human baseline(TBD)
- Random baseline(TBD)

### Single Scenario
You may familiarize yourself with a single inference scenario in **MirrorBench** by running commands like:
```shell
# Windows
%ISAACSIM_ROOT%\python.bat  inference.py --body male_0 --hand mano_white --mark splash --level 1 --model gpt-4o

# Linux
$ISAACSIM_ROOT/python.sh  inference.py --body male_0 --hand mano_white --mark splash --level 1 --model gpt-4o
```
For each evaluation run, the framework automatically generates logs, observations, and result summaries in `logs` and `results` directories.

### Full Evaluation
We also provide scripts for full evaluation with over 5,000 inference steps per MLLM. To use them, run:
```shell
# Windows
evaluate.bat MODEL_NAME

# Linux
./evaluate.sh MODEL_NAME
```

## Citation

If you find our work interesting, please feel free to cite our paper:

```bibtex

```