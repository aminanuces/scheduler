# POFP (Preference-Oriented Fixed-Priority) Scheduler

Complete implementation of the **Preference-Oriented Fixed-Priority (POFP)** scheduling algorithm from:

> **"Preference-oriented fixed-priority scheduling for periodic real-time tasks"**  
> by R. Begam et al., Journal of Systems Architecture 69 (2016)  
> Paper URL: https://cs.gmu.edu/~a##

````

**Everything consolidated in one place:**

- Core POFP algorithm implementation
- PORMS and POPPA scheduler variants
- Paper example simulation
- Additional test cases
- All necessary classes and functionsa16.pdf

## How to Run & Test

### **Terminal Commands - Run Each Section Separately**

```bash
# Show all available options
python3 pofp.py --help

# Run everything (default)
python3 pofp.py

# Run specific sections
python3 pofp.py --paper           # Paper example only
python3 pofp.py --simple          # Simple 2-task example
python3 pofp.py --custom          # Custom task set example

# Test specific scenarios
python3 pofp.py --mixed           # Mixed preferences test
python3 pofp.py --all-asap        # All ASAP tasks test
python3 pofp.py --all-alap        # All ALAP tasks test
python3 pofp.py --performance     # Performance test (10 tasks)
````

### **Get Started:**

```bash
python3 pofp.py --paper          # Research paper validation
python3 pofp.py --mixed          # See PORMS vs POPPA differences
```

**Verify paper results:**

```bash
python3 pofp.py --paper
# Should show: γ₃=2, γ₄=3 and both PORMS/POPPA schedules
```

**See key algorithm difference:**

```bash
python3 pofp.py --mixed
# Shows PORMS vs POPPA priority assignment difference
```

**Understand promotion times:**

```bash
python3 pofp.py --simple
# Simple case: T2 has promotion time = 4
```

**Test edge cases:**

```bash
python3 pofp.py --all-asap        # No delays (traditional RMS)
python3 pofp.py --all-alap        # Maximum delays via promotion times
```

**Performance testing:**

```bash
python3 pofp.py --performance     # 10 tasks, mixed preferences
```

### **1. Run the Built-in Examples**

```bash
python3 pofp.py
```

This runs everything automatically and shows:

- **Paper Example**: Original task set from the research paper
- **Simple 2-Task Case**: Easy verification example
- **Custom Task Set**: Different task combinations

### **2. Test with Your Own Tasks**

```python
# Create a test file (e.g., my_test.py)
from pofp import *

# Define your tasks
tasks = [
    Task(1, 1, 4, TaskType.ASAP),  # T1: exec=1, period=4, ASAP
    Task(2, 2, 6, TaskType.ALAP),  # T2: exec=2, period=6, ALAP
    Task(3, 1, 8, TaskType.ASAP),  # T3: exec=1, period=8, ASAP
]

# Test both schedulers
print("=== PORMS (RMS-based) ===")
porms = PORMSScheduler(tasks)
print_task_info(tasks, "PORMS")
schedule = porms.simulate(16)
print_schedule(schedule, "PORMS")

print("\n=== POPPA (Preference-aware) ===")
poppa_tasks = [Task(t.task_id, t.execution_time, t.period, t.task_type) for t in tasks]
poppa = POPPAScheduler(poppa_tasks)
print_task_info(poppa_tasks, "POPPA")
schedule = poppa.simulate(16)
print_schedule(schedule, "POPPA")
```

### **3. Interactive Testing in Python**

```python
# Start Python interpreter
python3

# Import and test interactively
>>> from pofp import *
>>>
>>> # Create a simple task
>>> t1 = Task(1, 1, 5, TaskType.ASAP)
>>> t2 = Task(2, 1, 6, TaskType.ALAP)
>>>
>>> # Test PORMS
>>> scheduler = PORMSScheduler([t1, t2])
>>> schedule = scheduler.simulate(10)
>>>
>>> # View results
>>> for entry in schedule:
...     print(f"T{entry['task']}.{entry['instance']}: {entry['start_time']}-{entry['end_time']}")
```

### **4. Verify Against Paper Results**

The implementation includes the exact example from the paper. You should see:

**Task Set**: T1(1,5,ASAP), T2(2,6,ASAP), T3(1,6,ALAP), T4(1,8,ALAP)

**Expected PORMS Results**:

- T1 gets highest priority (period=5)
- T2 gets medium priority (period=6)
- T3,T4 get delays due to ALAP preference
- Promotion times: γ₃=2, γ₄=3

**Expected POPPA Results**:

- T1,T2 (ASAP) get higher priorities than T3,T4 (ALAP)
- Within groups, shorter period = higher priority
- Same promotion times: γ₃=2, γ₄=3

### **5. Understanding the Output**

**Task Information Table**:

```
Task | Type | Period | Exec | Priority | Response | Promotion
------------------------------------------------------------
T1   | ASAP |      5 |    1 |        4 |        1 | N/A
T3   | ALAP |      6 |    1 |        2 |        4 | 2
```

- **Priority**: Higher number = executes first
- **Response**: Worst-case time from arrival to completion
- **Promotion**: How long ALAP tasks wait before becoming eligible

**Schedule Output**:

```
T1.1: 0-1 (ASAP)    # Task 1, instance 1, runs time 0→1, ASAP type
T3.1: 3-4 (ALAP)    # Task 3, instance 1, runs time 3→4, ALAP type
```

### **6. Test Different Scenarios**

**Scenario A: All ASAP tasks**

```python
tasks = [
    Task(1, 1, 4, TaskType.ASAP),
    Task(2, 2, 6, TaskType.ASAP)
]
# Should behave like traditional RMS
```

**Scenario B: All ALAP tasks**

```python
tasks = [
    Task(1, 1, 4, TaskType.ALAP),
    Task(2, 2, 6, TaskType.ALAP)
]
# Should show maximum delays via promotion times
```

**Scenario C: Mixed preferences**

```python
tasks = [
    Task(1, 2, 8, TaskType.ASAP),   # High period, but ASAP
    Task(2, 1, 4, TaskType.ALAP),   # Low period, but ALAP
]
# POPPA should prioritize T1 over T2 despite periods
```

### **7. Debugging and Validation**

**Check if tasks are schedulable**:

```python
# All tasks should have response_time ≤ period
for task in tasks:
    if task.response_time > task.period:
        print(f"Task T{task.task_id} not schedulable!")
```

**Verify promotion time calculation**:

```python
# For ALAP tasks: γᵢ = pᵢ - Rᵢ
for task in tasks:
    if task.task_type == TaskType.ALAP:
        expected_promotion = task.period - task.response_time
        print(f"T{task.task_id}: γ={task.promotion_time}, expected={expected_promotion}")
```

### **8. Performance Testing**

**Test with larger task sets**:

```python
# Generate many tasks
tasks = []
for i in range(1, 11):  # 10 tasks
    exec_time = 1
    period = 4 + i * 2  # Periods: 6,8,10,12...
    task_type = TaskType.ASAP if i % 2 == 1 else TaskType.ALAP
    tasks.append(Task(i, exec_time, period, task_type))

# Test schedulability and performance
porms = PORMSScheduler(tasks)
schedule = porms.simulate(50)
print(f"Scheduled {len(schedule)} task instances")
```

## Quick Start

**Single file contains everything:**

```bash
python3 pofp.py
```

**Create your own tasks:**

```python
from pofp import *

tasks = [
    Task(1, 1, 5, TaskType.ASAP),  # T1: exec=1, period=5, ASAP
    Task(2, 2, 6, TaskType.ALAP),  # T2: exec=2, period=6, ALAP
]

scheduler = PORMSScheduler(tasks)  # or POPPAScheduler(tasks)
schedule = scheduler.simulate(10)

for entry in schedule:
    print(f"T{entry['task']}.{entry['instance']}: {entry['start_time']}-{entry['end_time']}")
```

## Algorithm Overview

### Task Types

- **ASAP (As Soon As Possible)**: Execute as early as possible
- **ALAP (As Late As Possible)**: Can be delayed without missing deadlines

### Core Innovation: Dual Queue System

- **Ready Queue (QR)**: Tasks ready for immediate execution
- **Delay Queue (QD)**: ALAP tasks waiting for their promotion time
- **Non-work-conserving**: Processor can idle even when ALAP tasks are available

### Scheduler Variants

#### PORMS (POFP + RMS)

- **Priority Assignment**: Rate Monotonic Scheduling (shorter period = higher priority)
- **Example**: T1(period=5) > T2(period=6) > T3(period=8)

#### POPPA (POFP + PPA)

- **Priority Assignment**: Preference-aware (ASAP tasks > ALAP tasks, then by period)
- **Example**: T1(ASAP,period=5) > T2(ASAP,period=6) > T3(ALAP,period=8)

## Algorithm Details

### Core Algorithm (Algorithm 3 from Paper)

```
Input: {ci, pi, ηi} for ∀Ti ∈ T and γi for ∀Ti ∈ L

On event at time t involving task instance Tk:

if (Tk ∈ L arrives at time t) then
    Enqueue(Tk, QD); SetTimer(γk);        // ALAP task to delay queue
else if (Tk completes at time t) then
    if (Ready queue QR is not empty) then
        Tk = Dequeue(QR); Execute(Tk);     // Execute next ready task
    else
        Let processor idle;                 // Key: idle even if tasks in QD
    end if
else
    // Tk ∈ L is promoted OR Tk ∈ S arrives at time t
    if (ηk > ηc) then
        Enqueue(Tc, QR); Execute(Tk);      // Preempt current task
    else
        Enqueue(Tk, QR);                   // Add to ready queue
    end if
end if
```

### Promotion Time Calculation

**Formula**: γᵢ = pᵢ - Rᵢ (period - response time)

Determines how long ALAP tasks can safely wait in delay queue.

### Response Time Analysis

For task Tᵢ with priority ηᵢ:

```
Rᵢ = cᵢ + Σ(⌈Rᵢ/pⱼ⌉ × cⱼ) for all Tⱼ with ηⱼ > ηᵢ
```

## Example Results

**Task Set**: T1(1,5,ASAP), T2(2,6,ASAP), T3(1,6,ALAP), T4(1,8,ALAP)

### PORMS Schedule:

```
T1.1: 0-1 (ASAP)     # T1 executes immediately
T2.1: 1-3 (ASAP)     # T2 executes after T1
T3.1: 3-4 (ALAP)     # T3 promoted after delay
T4.1: 5-6 (ALAP)     # T4 promoted after delay
T3.2: 8-9 (ALAP)     # T3 second instance
```

### POPPA Schedule:

```
T1.1: 0-1 (ASAP)     # Same - T1 highest priority
T2.1: 1-3 (ASAP)     # Same - T2 second highest
T3.1: 3-4 (ALAP)     # T3 gets better priority than PORMS
T4.1: 5-6 (ALAP)     # T4 similar timing
T3.2: 8-9 (ALAP)     # T3 second instance
```

**Key Difference**: In POPPA, ASAP tasks always get higher priority than ALAP tasks.

## Key Design Principles

1. **ASAP Principle**: If ready ASAP tasks exist, processor should not idle
2. **ALAP Principle**: If only ALAP tasks ready, processor can idle to delay their execution
3. **Non-Work-Conserving**: Unlike traditional schedulers, can idle with available tasks
4. **Preference Awareness**: Different handling based on execution preferences

## File Structure

```
Project/
├── pofp.py    # Complete implementation (everything in one file)
└── README.md           # This documentation
```

**No multiple files needed** - everything is consolidated in `pofp.py`:

- Core POFP algorithm implementation
- PORMS and POPPA scheduler variants
- Paper example simulation
- Additional test cases
- All necessary classes and functions

## What You Get When You Run It

```bash
python3 pofp.py
```

1. **Paper Example**: Exact case study from the research paper
2. **Task Information**: Priorities, response times, promotion times
3. **Schedule Output**: When each task instance executes
4. **Additional Examples**: Simple 2-task case, custom task sets

## Understanding the Output

**Task Information Table:**

```
Task | Type | Period | Exec | Priority | Response | Promotion
------------------------------------------------------------
T1   | ASAP |      5 |    1 |        4 |        1 | N/A
T3   | ALAP |      6 |    1 |        2 |        4 | 2
```

- **Priority**: Higher number = higher priority
- **Response**: Worst-case response time
- **Promotion**: How long ALAP tasks wait (γᵢ = pᵢ - Rᵢ)

**Schedule Output:**

```
T1.1: 0-1 (ASAP)    # Task 1, instance 1, time 0-1, ASAP type
T3.1: 3-4 (ALAP)    # Task 3, instance 1, time 3-4, ALAP type
```

## Educational Value

This implementation helps understand:

- **Fixed-priority scheduling** beyond basic RMS/DMS
- **Non-work-conserving schedulers** and when idling can be beneficial
- **Preference-aware scheduling** for mixed-criticality systems
- **Response time analysis** with task dependencies
- **Queue management** in real-time systems

## Paper Reference

Begam, R., Prasad, R. V., Rao, S., & Jantsch, A. (2016). Preference-oriented fixed-priority scheduling for periodic real-time tasks. Journal of Systems Architecture, 69, 1-14.

## Requirements

- Python 3.7+
- No external dependencies
