# Can Vision Foundation Models Navigate?
### Zero-Shot Real-World Evaluation and Lessons Learned

**[Maeva Guerrier](https://scholar.google.com/citations?hl=fr&user=4-GRCBsAAAAJ), [Karthik Soma](https://scholar.google.com/citations?hl=fr&user=eJ5jLXoAAAAJ), [Jana Pavlasek](https://scholar.google.com/citations?hl=fr&user=yJS-u7IAAAAJ), [Giovanni Beltrame](https://scholar.google.com/citations?hl=fr&user=TVHJJ9wAAAAJ)**  
*Polytechnique Montréal*

[![arXiv](https://img.shields.io/badge/arXiv-2603.25937-b31b1b.svg)](https://arxiv.org/abs/2603.25937)
[![website](https://img.shields.io/badge/website-link-blue)](https://maevaguerrier.github.io/papers-pages/zero-shot-eval.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview 🔎

Visual Navigation Models (VNMs) promise generalizable robot navigation by learning from large-scale visual demonstrations. Yet existing evaluations rely almost exclusively on **success rate** — whether the robot reaches its goal — which conceals trajectory quality, collision behavior, and robustness to environmental change.

This work provides a **comprehensive real-world evaluation** of five state-of-the-art VNMs across two robot platforms and five environments. We go beyond success rate by combining path-based metrics with vision-based goal-recognition scores and controlled robustness testing.

<p align="center">
  <img src="medias/vnm_pitch_fig.svg" alt="Evaluation overview" width="100%"/>
</p>

---

## TODOs 📝

### ONNX models

- [ ] provde google drive link

### Documentations

- [x] Initial draft of readme
- [x] Provide arXiv link and website
- [ ] Explain how to deploy + Docker structure *(ETA release during the week of 8 June)*
- [ ] Explain the onnx models *(ETA release during the week of 8 June)*


---

## Key Findings 🔑

Three systematic limitations are identified across all evaluated architectures:

1. **Limited geometric understanding** — Even diffusion- and transformer-based models exhibit frequent collisions. Architectural sophistication does not guarantee safe navigation.
2. **Goal confusion in repetitive environments** — Models fail to discriminate between perceptually similar locations, causing premature or incorrect goal predictions.
3. **Fragility under distribution shift** — Performance degrades noticeably under motion blur, sunflare, and out-of-distribution environments (e.g., snow).

A surprising result: **simpler architectures (GNM/MobileNetV2) match complex transformer and diffusion models** across several metrics, suggesting data insufficiency limits the newer models more than architectural capacity.

---

## Models Evaluated

| Model | Backbone | Key Feature | Output |
|---|---|---|---|
| [GNM](https://arxiv.org/abs/2210.03370) | Fully Connected | Shared action space | Waypoints + distance |
| [ViNT](https://arxiv.org/abs/2306.14846) | Transformer | Goal fusion token | Waypoint + distance |
| [NoMaD](https://arxiv.org/abs/2310.07896) | Diffusion | Goal masking for exploration | Trajectory |
| [NaviBridger](https://arxiv.org/abs/2504.10041) | Diffusion | Learned action prior | Trajectory |
| [CrossFormer](https://arxiv.org/abs/2408.11812) | Transformer | Embodiment-specific heads | Waypoint |

---

## Environments 🌍

Five real-world environments of increasing difficulty, deployed on two robot platforms (**Bunker** tracked robot, **Spot** quadruped):

| Environment | Platform | Length | Description |
|---|---|---|---|
| **Corridor** | Bunker | 3.75 m | Short-horizon straight-line, goal = cardboard box |
| **Stairs** | Spot | 6.25 m | Ascending staircase; two visually identical staircases |
| **Office Loop** | Bunker | 27.96 m | Full office loop; cluttered long-horizon setting |
| **Arena** | Spot | 20.05 m | Doorway navigation; three similar doors, one target |
| **Snow** | Bunker | 18.96 m | Outdoor snowy parking lot; significant OOD shift |

&nbsp;

<p align="center">
  <img src="medias/meet_the_envs.svg" alt="Evaluation overview" width="70%"/>
</p>

---

## Metrics 🎯

We evaluate across three complementary domains:

**Path quality** 📊📉
- Path length
- Distance to goal (checkpoint-based)
- Collision occurrence
- Topological node error

**Visual perception** 👀
- Goal prediction accuracy
- LPIPS, PSNR, DSSIM (perceptual similarity at goal)

**Robustness** 💪
- Motion blur perturbation on topological map
- Sunflare perturbation on topological map

---

## WIP - Getting Started

### Prerequisites


### Installation


### WIP - Download Pretrained Weights

Download model weights (ONNX format) for GNM, ViNT, NoMaD, NaviBridger, and CrossFormer:



### WIP - Running Deployment

**Real-world deployment (ROS/ROS2):**


---

## WIP - Dataset

> **Dataset release coming soon.**

The evaluation dataset includes ROS/ROS2 bag files for all environments and all model deployments. (*We will provide a conversion tool to go from ROS to ROS2 and vice versa.*)
Each trial logs: odometry, node predictions, goal detection events, CPU/GPU/memory usage, and inference time.

---

## WIP - Repository Structure


---

## Citation 🖊️

If you use this work, please cite:

```bibtex
@article{guerrier2026vnm,
  title   = {Can Vision Foundation Models Navigate? Zero-Shot Real-World Evaluation and Lessons Learned},
  author  = {Guerrier, Maeva and Soma, Karthik and Pavlasek, Jana and Beltrame, Giovanni},
  journal = {arXiv preprint arXiv:2603.25937},
  year    = {2026}
}
```

---

## Contact ✉️

For questions, open an issue or reach out to `maeva.guerrier@polymtl.ca`.

## Acknowledgements 🤗

* [jetson-containers](https://github.com/dusty-nv/jetson-containers?tab=readme-ov-file) - For providing the amazing dockerfiles that helped us build our dockers for each of the models. 
* [visualnav-transformer](https://github.com/robodhruv/visualnav-transformer) - For open sourcing their code which served as a foundation for all the baselines. 