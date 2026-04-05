# GSoC 2026 Proposals — Shraavasti Bhat

> **Important:** OSRF explicitly discourages AI-generated applications. Rewrite every sentence in your own voice before submitting. Reference specific files/functions from the actual codebases.

---

# Proposal 1: Mission Control for ros2_control (OSRF)

**Title:** Mission Control for ros2_control: Declarative Orchestration of Controller and Hardware State

**Organization:** Open Robotics / ros2_control

**Mentors:** Bence Magyar (@bmagyar), Sai Kishor Kothakota (@saikishor)

**Duration:** 350 hours (Large)

---

## About Me

I'm Shraavasti Bhat, a student at Penn (CS + Management) with hands-on experience deploying autonomous robots on real hardware.

My most relevant project is **Trekker** — an autonomous construction inspection rover built on the Waveshare UGV Beast (Raspberry Pi 4B + ESP32), running ROS 2 Humble. Trekker executes multi-waypoint patrol routes using `nav2_simple_commander`, fuses GPS/IMU/encoder data through `robot_localization`'s EKF, and streams position-tagged anomaly detections to a live cloud dashboard. Coordinating the rover's operational states — patrol, inspection stop, alert, return home — is something I've had to handle manually in Python scripts. A proper mission-control layer is exactly what Trekker needs, and building it upstream in ros2_control is a direct solution to a problem I've already felt.

Prior to Trekker, I trained and deployed manipulation policies on a **LeRobot SO-101 arm**, where I worked directly with trajectory execution pipelines and real-time hardware feedback loops. I've also deployed edge inference on **NVIDIA Jetson Nano** (JetBot), giving me familiarity with constrained hardware timing requirements.

**Relevant skills:** ROS 2 (Humble), Python (primary), C++ (ramping up — reading ros2_control source actively), YAML configuration, state machines, Docker.

**GitHub:** https://github.com/shraavb

---

## Motivation

The `ros2_control` framework provides low-level building blocks for hardware and controller management, but as soon as a robot does more than one thing — switch tools, transition between operational modes, handle failure states — external orchestration logic proliferates. Projects like MoveIt2 implement their own `SimpleControllerManager` to fill this gap, and field robots like Trekker do it in ad-hoc Python scripts.

A native `mission_control` component inside ros2_control would let practitioners express these state transitions declaratively in YAML, rather than re-implementing a state machine from scratch in every project. This aligns directly with how ros2_control's controller lifecycle already works — the `controller_manager` already understands configured/inactive/active states; mission control extends that into a higher-level, user-configurable orchestration layer.

I read through the `controller_manager` source at `ros2_control/controller_manager/src/controller_manager.cpp` and traced the `load_controller`, `configure_controller`, and `switch_controller` service flows. The gap is clear: there's no component that groups these transitions into named presets or enforces sequencing between them.

---

## Technical Approach

### Architecture

```
mission_control_node
    ├── reads: mission_config.yaml (presets + transitions)
    ├── subscribes: /controller_manager/controller_state (status topics)
    ├── calls: /controller_manager/switch_controller (service)
    └── publishes: /mission_control/active_preset
```

A **preset** is a named set of active controllers. A **transition** is a triggered move from one preset to another, with optional preconditions and cleanup steps.

Example `mission_config.yaml`:

```yaml
presets:
  navigation:
    active_controllers: [diff_drive_controller]
    inactive_controllers: [arm_controller]
  inspection:
    active_controllers: [arm_controller, joint_trajectory_controller]
    inactive_controllers: [diff_drive_controller]

transitions:
  - from: navigation
    to: inspection
    trigger: /inspection/trigger
    precondition: velocity < 0.01
```

### Deliverables Breakdown

1. **Benchmark scenario** — define a multi-robot, multi-tool setup (e.g., mobile base + arm, two robots sharing a workspace) as the integration test reference
2. **Status publishers in controller_manager** — extend CM to publish controller lifecycle state on ROS 2 topics (not just via service calls)
3. **Status topics on standard controllers** — add `/controller_name/status` to `diff_drive_controller`, `joint_trajectory_controller`, `forward_command_controller`
4. **YAML preset format** — design and document the configuration schema
5. **mission_control node** — implement the orchestration component: parse config, watch status topics, call switch_controller on triggers

---

## Week-by-Week Timeline

**Community Bonding (May 1–24)**
- Read all of `controller_manager` source, controller lifecycle documentation, and MoveIt2's SimpleControllerManager implementation
- Set up development environment; run existing ros2_control demos
- Sync with mentors on benchmark scenario definition and YAML schema design

**Week 1–2 (May 25 – Jun 7): Benchmark + Status Publishers**
- Define multi-robot benchmark scenario with mentors; write test launch files
- Add status publisher to `controller_manager` — emit `ControllerState` messages on `/controller_manager/controller_state`

**Week 3–4 (Jun 8–21): Controller Status Topics**
- Add per-controller status topics to `diff_drive_controller`, `joint_trajectory_controller`, `forward_command_controller`
- Write unit tests for each

**Week 5–6 (Jun 22 – Jul 5): YAML Configuration Format**
- Design preset schema; write parser and validator
- Document format with annotated examples
- Submit PR; incorporate mentor review

**Week 7 (Jul 6–10): Midterm**
- Status publishers merged or in final review
- YAML parser complete with tests
- Midterm evaluation submitted

**Week 8–9 (Jul 11–24): mission_control Node Core**
- Implement node: load config, subscribe to status topics, expose `/mission_control/switch_preset` action
- Handle transition preconditions and failure cases

**Week 10–11 (Jul 25 – Aug 7): Integration + Testing**
- Run full benchmark scenario against mission_control
- Integration tests with Gazebo simulation
- Edge case handling: controller crash during transition, conflicting presets

**Week 12 (Aug 8–17): Documentation + Final Submission**
- Write tutorials with complete examples
- Record demo video against benchmark scenario
- Final PR cleanup and submission

---

## Why I'll Finish

I've deployed six-phase robotics projects on real hardware under time pressure — Trekker's full stack (EKF, SLAM, Nav2, YOLOv8 pipeline, cloud dashboard) was designed as a roadmap and executed phase by phase. I understand that shipping means handling the unsexy parts: testing edge cases, writing documentation, and iterating based on review. The C++ gap is real but tractable — the mission_control logic (config parsing, service calls, topic subscriptions) maps cleanly to patterns I already use in Python, and I'm actively reading the ros2_control C++ source to close that gap before coding begins.

---

---

# Proposal 2: Power Tower Inspection with Deep Learning (JdeRobot)

**Title:** Power Tower Inspection with Deep Learning: Dataset, Simulation Environment, and Exercise for RoboticsAcademy

**Organization:** JdeRobot

**Mentors:** David Pascual-Hernández, Md. Shariar Kabir, Luis Roberto Morales

**Duration:** 175 hours (Medium)

---

## About Me

I'm Shraavasti Bhat, a student at Penn (CS + Management) building autonomous inspection robots with deep learning perception pipelines on real hardware.

My primary project is **Trekker** — an autonomous construction site inspection rover running ROS 2 Humble. At every patrol waypoint, Trekker runs a two-stage detection pipeline: YOLOv8n on the Raspberry Pi 4B for fast first-pass filtering (~5–10 FPS edge inference), followed by a VLM on flagged frames for semantic hazard classification. Detections are tagged with the rover's EKF-fused pose and streamed to a cloud dashboard. This pipeline — object detection on infrastructure imagery for safety-critical inspection — is structurally identical to what this project asks for on power towers.

I've also trained and deployed manipulation policies with **LeRobot** (PyTorch, end-to-end learning, real hardware execution) and built edge inference systems on **NVIDIA Jetson Nano** with JetBot. I'm comfortable with the full loop: data collection → model training → deployment → evaluation.

**Skills:** Python, PyTorch, YOLOv8/Ultralytics, ROS 2, Gazebo, Jupyter Notebooks.

**GitHub:** https://github.com/shraavb

---

## Motivation

Power grid infrastructure inspection is a domain where autonomous systems can meaningfully reduce risk to human workers. RoboticsAcademy's existing power tower exercise teaches classical approaches, but deep learning-based defect detection — the method now used in real-world deployments — isn't covered.

I studied the [end-to-end visual control exercise](https://github.com/JdeRobot/RoboticsAcademy) as the structural template for this project. It shows the pattern: a Gazebo environment, a Simple API wrapping sensor/actuator access, and a Jupyter Notebook scaffold that guides students from raw perception to a working solution. The power tower project follows the same structure but targets detection/classification rather than control — a clean extension.

My Trekker experience is directly applicable: I've already solved the "run a detection model against an inspection image stream and extract structured outputs" problem. Building this into a teachable exercise with a proper dataset and simulation environment is a contribution I can make concretely.

---

## Technical Approach

### 1. Gazebo Environment

Extend or create a Gazebo world containing power tower models with simulated defect variants:
- Damaged insulators
- Corroded hardware / missing bolts
- Vegetation encroachment
- Bird nests / foreign object debris

Use existing open-source tower models and extend with defect mesh variants. Camera drone or ground robot provides the inspection viewpoint.

### 2. Dataset Creation

- **Simulated:** Render labeled images from Gazebo at varied angles, lighting, and distances using Gazebo's camera sensor + automated annotation from model metadata
- **Augmentation:** Apply standard augmentations (blur, brightness, rotation) to improve generalization
- **Format:** YOLO-compatible label format; host on a public repository (HuggingFace Datasets or Zenodo) for student access

Target: ~2,000–5,000 labeled images across defect classes.

### 3. Simple API Extension

Extend RoboticsAcademy's Simple API to expose:

```python
HAL.getImage()           # existing
HAL.getDetections()      # NEW: returns list of {label, bbox, confidence, logits}
HAL.classifyDefect(img)  # NEW: runs model inference, returns structured output
```

### 4. Exercise Framework

Following the end-to-end visual control template:
- `exercise.py` — ROS 2 node wrapping Gazebo + API
- `student_solution.py` — scaffold with TODO blocks guiding the student
- Evaluation script scoring detection mAP against held-out test images

### 5. Jupyter Notebooks

Three progressive notebooks:
1. **Dataset exploration** — visualize samples, class distribution, bounding boxes
2. **Model training** — fine-tune YOLOv8 on the power tower dataset, plot metrics
3. **Full pipeline** — run inference in the Gazebo environment, evaluate mAP

---

## Week-by-Week Timeline

**Community Bonding (May 1–24)**
- Study RoboticsAcademy codebase structure; run end-to-end visual control exercise locally
- Review existing classical power tower exercise; identify reusable components
- Sync with mentors on scope, target defect classes, and API design

**Week 1–2 (May 25 – Jun 7): Gazebo Environment**
- Source/create power tower Gazebo models
- Build world file with multiple towers and defect variants
- Verify camera sensor output streams correctly in ROS 2

**Week 3 (Jun 8–14): Dataset Collection**
- Write automated data collection script (spawn robot, move to viewpoints, save labeled images)
- Collect initial dataset (~2,000 images); verify label quality

**Week 4 (Jun 15–21): Model Training**
- Fine-tune YOLOv8 on dataset; run ablations on model size (n/s/m)
- Document training curves, mAP per class; select best checkpoint

**Midterm (Jul 10)**
- Gazebo environment complete and reviewed
- Dataset public and documented
- Trained model checkpoint available

**Week 5 (Jun 22 – Jul 5): Simple API Extension**
- Implement `getDetections()` and `classifyDefect()` in RoboticsAcademy API
- Write unit tests against static test images

**Week 6 (Jul 6–21): Exercise Framework + Notebooks**
- Implement `exercise.py` + `student_solution.py` scaffold
- Write all three Jupyter Notebooks with prose explanations
- Draft documentation

**Week 7 (Jul 22 – Aug 17): Testing, Polish, Submission**
- End-to-end test: student completes exercise from scratch using notebooks
- Fix integration issues; get mentor review
- Final PR submission with full documentation

---

## Why I'll Finish

The Trekker inspection pipeline is a deployed version of this project — I've already built the dataset labeling workflow (YOLOv8 training on inspection imagery), the Gazebo integration (ROS 2 camera topics → model inference), and the structured output logging. The 175-hour scope is realistic given that foundation. I've shipped multi-phase hardware projects before and know how to cut scope intelligently when integration takes longer than expected — prioritizing the core exercise over polish, then iterating.

---

## Submission Checklist

- [ ] Rewrite both proposals in your own voice
- [ ] Reference specific files/functions from ros2_control and RoboticsAcademy source
- [ ] Post to OSRF Discourse thread and JdeRobot community channel for mentor feedback by March 27
- [ ] Submit drafts on GSoC portal (orgs can comment on drafts)
- [ ] Final submit by March 30 (not 31 — timezone risk)
