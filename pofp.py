"""
Complete POFP (Preference-Oriented Fixed-Priority) Scheduler Implementation
Based on: "Preference-oriented fixed-priority scheduling for periodic real-time tasks"
by R. Begam et al., Journal of Systems Architecture 69 (2016)

This single file contains:
- Core POFP algorithm (Algorithm 3 from paper)
- PORMS variant (POFP + RMS)
- POPPA variant (POFP + PPA)
- Example simulation from the paper
- All necessary classes and functions

Usage:
    python3 pofp.py                    # Run all examples
    python3 pofp.py --paper             # Paper example only
    python3 pofp.py --simple            # Simple 2-task example
    python3 pofp.py --custom            # Custom task set example
    python3 pofp.py --mixed             # Mixed preferences test
    python3 pofp.py --all-asap          # All ASAP tasks test
    python3 pofp.py --all-alap          # All ALAP tasks test
    python3 pofp.py --performance       # Performance test with many tasks
"""

import heapq
import sys
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

class TaskType(Enum):
    ASAP = "ASAP"  # As Soon As Possible
    ALAP = "ALAP"  # As Late As Possible

@dataclass
class Task:
    """Represents a periodic real-time task"""
    task_id: int
    execution_time: int  # ci - worst case execution time
    period: int          # pi - period
    task_type: TaskType  # execution preference (ASAP or ALAP)
    priority: int = 0    # ηi - priority (higher number = higher priority)
    response_time: int = 0  # Ri - response time
    promotion_time: int = 0  # γi - promotion time (for ALAP tasks)

class EventType(Enum):
    TASK_ARRIVAL = "arrival"
    TASK_COMPLETION = "completion"
    TASK_PROMOTION = "promotion"

@dataclass
class Event:
    time: int
    event_type: EventType
    task_id: int
    instance_id: int
    
    def __lt__(self, other):
        return self.time < other.time

# =============================================================================
# POFP SCHEDULER IMPLEMENTATION
# =============================================================================

class POFPScheduler:
    """
    Base POFP Scheduler implementing Algorithm 3 from the paper
    
    Key Features:
    - Dual queue system: Ready Queue (QR) and Delay Queue (QD)
    - Non-work-conserving: can idle even with ALAP tasks available
    - Promotion time calculation: γi = pi - Ri
    """
    
    def __init__(self, tasks: List[Task]):
        self.tasks = tasks
        self.ready_queue = []  # QR - priority queue: (-priority, time, task_id, instance_id)
        self.delay_queue = []  # QD - list of (task_id, instance_id, promotion_time)
        self.event_queue = []  # Event queue for simulation
        self.current_time = 0
        self.current_task = None  # (task_id, instance_id)
        self.schedule = []
        self.task_dict = {task.task_id: task for task in tasks}
        
        # Calculate response times and promotion times
        self._calculate_response_times()
        self._calculate_promotion_times()
    
    def _calculate_response_times(self):
        """Calculate response times using fixed-point iteration"""
        for task in self.tasks:
            # Iterative calculation considering higher priority interference
            task.response_time = task.execution_time
            changed = True
            max_iterations = 10
            iteration = 0
            
            while changed and iteration < max_iterations:
                old_response_time = task.response_time
                interference = 0
                
                # Calculate interference from higher priority tasks
                for other_task in self.tasks:
                    if other_task.priority > task.priority:
                        interference += ((task.response_time - 1) // other_task.period + 1) * other_task.execution_time
                
                new_response_time = task.execution_time + interference
                
                if new_response_time <= task.period:
                    task.response_time = new_response_time
                else:
                    task.response_time = task.period
                    break
                
                changed = (new_response_time != old_response_time)
                iteration += 1
    
    def _calculate_promotion_times(self):
        """Calculate promotion times γi = pi - Ri for ALAP tasks"""
        for task in self.tasks:
            if task.task_type == TaskType.ALAP:
                task.promotion_time = max(0, task.period - task.response_time)
    
    # =========================================================================
    # ALGORITHM 3 IMPLEMENTATION
    # =========================================================================
    
    def process_event(self, event: Event):
        """Process a scheduling event following Algorithm 3"""
        self.current_time = event.time
        
        if event.event_type == EventType.TASK_ARRIVAL:
            self._handle_task_arrival(event.task_id, event.instance_id)
        elif event.event_type == EventType.TASK_COMPLETION:
            self._handle_task_completion(event.task_id, event.instance_id)
        elif event.event_type == EventType.TASK_PROMOTION:
            self._handle_task_promotion(event.task_id, event.instance_id)
    
    def _handle_task_arrival(self, task_id: int, instance_id: int):
        """Handle task arrival - Algorithm 3 lines 2-3"""
        task = self.task_dict[task_id]
        
        if task.task_type == TaskType.ALAP:
            # Enqueue(Tk, QD); SetTimer(γk)
            promotion_time = self.current_time + task.promotion_time
            self.delay_queue.append((task_id, instance_id, promotion_time))
            
            if task.promotion_time > 0:
                # Schedule promotion event
                promotion_event = Event(
                    time=promotion_time,
                    event_type=EventType.TASK_PROMOTION,
                    task_id=task_id,
                    instance_id=instance_id
                )
                heapq.heappush(self.event_queue, promotion_event)
            else:
                # Immediate promotion (γ = 0)
                self._handle_task_ready(task_id, instance_id)
        else:
            # ASAP task - handle as ready
            self._handle_task_ready(task_id, instance_id)
    
    def _handle_task_completion(self, task_id: int, instance_id: int):
        """Handle task completion - Algorithm 3 lines 4-9"""
        if self.current_task and self.current_task[0] == task_id and self.current_task[1] == instance_id:
            # Record completion
            task = self.task_dict[task_id]
            self.schedule.append({
                'task': task_id,
                'instance': instance_id,
                'start_time': self.current_time - task.execution_time,
                'end_time': self.current_time,
                'type': task.task_type.value
            })
            self.current_task = None
        
        # if (Ready queue QR is not empty) then
        if self.ready_queue:
            # Tk = Dequeue(QR); Execute(Tk)
            _, _, next_task_id, next_instance_id = heapq.heappop(self.ready_queue)
            self._execute_task(next_task_id, next_instance_id)
        else:
            # Let processor idle; // regardless of tasks in QD
            self.current_task = None
    
    def _handle_task_promotion(self, task_id: int, instance_id: int):
        """Handle ALAP task promotion from delay queue"""
        # Remove from delay queue
        self.delay_queue = [(tid, iid, pt) for tid, iid, pt in self.delay_queue 
                           if not (tid == task_id and iid == instance_id)]
        
        # Tk ∈ L is promoted - handle as ready task
        self._handle_task_ready(task_id, instance_id)
    
    def _handle_task_ready(self, task_id: int, instance_id: int):
        """Handle task becoming ready - Algorithm 3 lines 11-17"""
        task = self.task_dict[task_id]
        
        if self.current_task is None:
            # No task running, execute immediately
            self._execute_task(task_id, instance_id)
        elif task.priority > self.task_dict[self.current_task[0]].priority:
            # if (ηk > ηc) then
            # Enqueue(Tc, QR); Execute(Tk); // Tk preempts Tc
            current_task_id, current_instance_id = self.current_task
            current_task = self.task_dict[current_task_id]
            heapq.heappush(self.ready_queue, (-current_task.priority, self.current_time, current_task_id, current_instance_id))
            self._execute_task(task_id, instance_id)
        else:
            # Enqueue(Tk, QR); // Insert Tk to ready queue QR
            heapq.heappush(self.ready_queue, (-task.priority, self.current_time, task_id, instance_id))
    
    def _execute_task(self, task_id: int, instance_id: int):
        """Start executing a task"""
        task = self.task_dict[task_id]
        self.current_task = (task_id, instance_id)
        
        # Schedule completion event
        completion_event = Event(
            time=self.current_time + task.execution_time,
            event_type=EventType.TASK_COMPLETION,
            task_id=task_id,
            instance_id=instance_id
        )
        heapq.heappush(self.event_queue, completion_event)
    
    # =========================================================================
    # SIMULATION
    # =========================================================================
    
    def simulate(self, simulation_time: int):
        """Run the POFP simulation"""
        # Generate arrival events
        for task in self.tasks:
            instance_id = 1
            arrival_time = 0
            
            while arrival_time < simulation_time:
                arrival_event = Event(
                    time=arrival_time,
                    event_type=EventType.TASK_ARRIVAL,
                    task_id=task.task_id,
                    instance_id=instance_id
                )
                heapq.heappush(self.event_queue, arrival_event)
                
                instance_id += 1
                arrival_time += task.period
        
        # Process events
        while self.event_queue and self.current_time < simulation_time:
            event = heapq.heappop(self.event_queue)
            if event.time <= simulation_time:
                self.process_event(event)
        
        return sorted(self.schedule, key=lambda x: x['start_time'])

# =============================================================================
# SCHEDULER VARIANTS
# =============================================================================

class PORMSScheduler(POFPScheduler):
    """PORMS: POFP with Rate Monotonic Scheduling (RMS) priority assignment"""
    
    def __init__(self, tasks: List[Task]):
        # Apply RMS priority assignment: shorter period = higher priority
        sorted_tasks = sorted(tasks, key=lambda t: t.period)
        for i, task in enumerate(sorted_tasks):
            task.priority = len(tasks) - i
        
        super().__init__(tasks)

class POPPAScheduler(POFPScheduler):
    """POPPA: POFP with Preference-aware Priority Assignment (PPA)"""
    
    def __init__(self, tasks: List[Task]):
        # Apply PPA priority assignment
        self._apply_ppa_priorities(tasks)
        super().__init__(tasks)
    
    def _apply_ppa_priorities(self, tasks: List[Task]):
        """Apply Preference-aware Priority Assignment"""
        asap_tasks = [t for t in tasks if t.task_type == TaskType.ASAP]
        alap_tasks = [t for t in tasks if t.task_type == TaskType.ALAP]
        
        # Sort by period (RMS within preference groups)
        asap_tasks.sort(key=lambda t: t.period)
        alap_tasks.sort(key=lambda t: t.period)
        
        # Assign priorities: ASAP tasks get higher priorities
        priority = len(tasks)
        
        # ASAP tasks first (highest priorities)
        for task in asap_tasks:
            task.priority = priority
            priority -= 1
        
        # Then ALAP tasks (lower priorities)
        for task in alap_tasks:
            task.priority = priority
            priority -= 1

# =============================================================================
# EXAMPLE AND TESTING
# =============================================================================

def create_paper_example_tasks():
    """Create the task set from the paper: T1(1,5,ASAP), T2(2,6,ASAP), T3(1,6,ALAP), T4(1,8,ALAP)"""
    return [
        Task(task_id=1, execution_time=1, period=5, task_type=TaskType.ASAP),
        Task(task_id=2, execution_time=2, period=6, task_type=TaskType.ASAP),
        Task(task_id=3, execution_time=1, period=6, task_type=TaskType.ALAP),
        Task(task_id=4, execution_time=1, period=8, task_type=TaskType.ALAP)
    ]

def print_task_info(tasks, scheduler_name):
    """Print task information including priorities and promotion times"""
    print(f"\n{scheduler_name} Task Information:")
    print("Task | Type | Period | Exec | Priority | Response | Promotion")
    print("-" * 60)
    for task in tasks:
        promotion = task.promotion_time if task.task_type == TaskType.ALAP else "N/A"
        print(f"T{task.task_id}   | {task.task_type.value:4} | {task.period:6} | {task.execution_time:4} | "
              f"{task.priority:8} | {task.response_time:8} | {promotion}")

def print_schedule(schedule, scheduler_name):
    """Print the execution schedule"""
    print(f"\n{scheduler_name} Schedule:")
    if not schedule:
        print("No tasks scheduled")
        return
        
    for entry in schedule:
        print(f"T{entry['task']}.{entry['instance']}: {entry['start_time']}-{entry['end_time']} ({entry['type']})")

def run_paper_example():
    """Run the complete example from the paper"""
    print("=" * 80)
    print("POFP Scheduler - Paper Example Implementation")
    print("Tasks: T1(1,5,ASAP), T2(2,6,ASAP), T3(1,6,ALAP), T4(1,8,ALAP)")
    print("=" * 80)
    
    simulation_time = 10
    
    # Create separate task sets for each scheduler
    porms_tasks = create_paper_example_tasks()
    poppa_tasks = create_paper_example_tasks()
    
    # Run PORMS
    print("\n" + "="*40)
    print("PORMS (POFP + RMS)")
    print("="*40)
    porms = PORMSScheduler(porms_tasks)
    print_task_info(porms_tasks, "PORMS")
    porms_schedule = porms.simulate(simulation_time)
    print_schedule(porms_schedule, "PORMS")
    
    # Run POPPA
    print("\n" + "="*40)
    print("POPPA (POFP + PPA)")
    print("="*40)
    poppa = POPPAScheduler(poppa_tasks)
    print_task_info(poppa_tasks, "POPPA")
    poppa_schedule = poppa.simulate(simulation_time)
    print_schedule(poppa_schedule, "POPPA")
    
    # Analysis
    print("\n" + "="*40)
    print("KEY DIFFERENCES")
    print("="*40)
    print("PORMS: Uses RMS priority assignment (period-based)")
    print("POPPA: Uses PPA priority assignment (preference-aware)")
    print("Both: Use POFP's delay queue for ALAP tasks")
    print("Both: Non-work-conserving (can idle with ALAP tasks available)")

def run_custom_examples():
    """Additional test examples with different task sets"""
    print("\n" + "=" * 80)
    print("ADDITIONAL TEST EXAMPLES")
    print("=" * 80)
    
    # Example 1: Simple 2-task case
    print("\n" + "="*50)
    print("SIMPLE 2-TASK EXAMPLE")
    print("="*50)
    
    simple_tasks = [
        Task(task_id=1, execution_time=1, period=4, task_type=TaskType.ASAP),
        Task(task_id=2, execution_time=1, period=6, task_type=TaskType.ALAP)
    ]
    
    print("Tasks: T1(1,4,ASAP), T2(1,6,ALAP)")
    porms = PORMSScheduler(simple_tasks)
    print_task_info(simple_tasks, "PORMS")
    schedule = porms.simulate(12)
    print_schedule(schedule, "PORMS")
    
    print(f"\nObservation: T2 (ALAP) has promotion time = {simple_tasks[1].promotion_time}")
    print("This means T2 waits in delay queue before becoming ready")
    
    # Example 2: Custom task set
    print("\n" + "="*50)
    print("CUSTOM TASK SET EXAMPLE")
    print("="*50)
    
    custom_tasks = [
        Task(task_id=1, execution_time=2, period=8, task_type=TaskType.ASAP),
        Task(task_id=2, execution_time=1, period=4, task_type=TaskType.ASAP),
        Task(task_id=3, execution_time=3, period=12, task_type=TaskType.ALAP),
        Task(task_id=4, execution_time=1, period=6, task_type=TaskType.ALAP)
    ]
    
    print("Tasks: T1(2,8,ASAP), T2(1,4,ASAP), T3(3,12,ALAP), T4(1,6,ALAP)")
    
    porms_custom = PORMSScheduler([Task(t.task_id, t.execution_time, t.period, t.task_type) for t in custom_tasks])
    poppa_custom = POPPAScheduler([Task(t.task_id, t.execution_time, t.period, t.task_type) for t in custom_tasks])
    
    print_task_info(porms_custom.tasks, "PORMS")
    porms_schedule = porms_custom.simulate(16)
    print_schedule(porms_schedule, "PORMS")
    
    print_task_info(poppa_custom.tasks, "POPPA")
    poppa_schedule = poppa_custom.simulate(16)
    print_schedule(poppa_schedule, "POPPA")

def run_mixed_preferences_test():
    """Test mixed preferences scenario"""
    print("=" * 80)
    print("MIXED PREFERENCES TEST")
    print("=" * 80)
    print("T1: High period (8) but ASAP")
    print("T2: Low period (4) but ALAP") 
    print("POPPA should prioritize T1 over T2 despite periods")
    print()

    tasks = [
        Task(1, 2, 8, TaskType.ASAP),   # High period, but ASAP
        Task(2, 1, 4, TaskType.ALAP),   # Low period, but ALAP
    ]

    print("=== PORMS (Period-based) ===")
    porms_tasks = [Task(t.task_id, t.execution_time, t.period, t.task_type) for t in tasks]
    porms = PORMSScheduler(porms_tasks)
    print_task_info(porms_tasks, "PORMS")
    schedule = porms.simulate(12)
    print_schedule(schedule, "PORMS")

    print("\n=== POPPA (Preference-aware) ===")
    poppa_tasks = [Task(t.task_id, t.execution_time, t.period, t.task_type) for t in tasks]
    poppa = POPPAScheduler(poppa_tasks)
    print_task_info(poppa_tasks, "POPPA")
    schedule = poppa.simulate(12)
    print_schedule(schedule, "POPPA")

    print("\n=== KEY DIFFERENCE ===")
    print("PORMS: T2 (period=4) gets higher priority than T1 (period=8)")
    print("POPPA: T1 (ASAP) gets higher priority than T2 (ALAP)")

def run_all_asap_test():
    """Test with all ASAP tasks - should behave like traditional RMS"""
    print("=" * 80)
    print("ALL ASAP TASKS TEST")
    print("=" * 80)
    print("All tasks are ASAP - should behave like traditional RMS")
    print()

    tasks = [
        Task(1, 1, 4, TaskType.ASAP),
        Task(2, 2, 6, TaskType.ASAP),
        Task(3, 1, 8, TaskType.ASAP)
    ]

    print("Tasks: T1(1,4,ASAP), T2(2,6,ASAP), T3(1,8,ASAP)")
    porms = PORMSScheduler(tasks)
    print_task_info(tasks, "PORMS")
    schedule = porms.simulate(16)
    print_schedule(schedule, "PORMS")
    
    print("\nObservation: All promotion times are N/A since no ALAP tasks")

def run_all_alap_test():
    """Test with all ALAP tasks - should show maximum delays"""
    print("=" * 80)
    print("ALL ALAP TASKS TEST") 
    print("=" * 80)
    print("All tasks are ALAP - should show maximum delays via promotion times")
    print()

    tasks = [
        Task(1, 1, 4, TaskType.ALAP),
        Task(2, 2, 6, TaskType.ALAP),
        Task(3, 1, 8, TaskType.ALAP)
    ]

    print("Tasks: T1(1,4,ALAP), T2(2,6,ALAP), T3(1,8,ALAP)")
    porms = PORMSScheduler(tasks)
    print_task_info(tasks, "PORMS")
    schedule = porms.simulate(16)
    print_schedule(schedule, "PORMS")
    
    print(f"\nObservation: All tasks have promotion times")
    for task in tasks:
        print(f"  T{task.task_id}: γ={task.promotion_time} (can wait {task.promotion_time} units)")

def run_performance_test():
    """Test with larger task set"""
    print("=" * 80)
    print("PERFORMANCE TEST - 10 TASKS")
    print("=" * 80)
    
    # Generate 10 tasks
    tasks = []
    for i in range(1, 11):
        exec_time = 1
        period = 4 + i * 2  # Periods: 6,8,10,12,14,16,18,20,22,24
        task_type = TaskType.ASAP if i % 2 == 1 else TaskType.ALAP
        tasks.append(Task(i, exec_time, period, task_type))

    print("10 tasks: T1,T3,T5,T7,T9 are ASAP; T2,T4,T6,T8,T10 are ALAP")
    print("Periods from 6 to 24")
    
    porms = PORMSScheduler(tasks)
    print_task_info(tasks, "PORMS")
    schedule = porms.simulate(30)
    
    print(f"\nScheduled {len(schedule)} task instances in 30 time units")
    print("First 10 instances:")
    for i, entry in enumerate(schedule[:10]):
        print(f"  T{entry['task']}.{entry['instance']}: {entry['start_time']}-{entry['end_time']} ({entry['type']})")
    
    if len(schedule) > 10:
        print(f"  ... and {len(schedule)-10} more instances")

def main():
    """Main function with command line argument handling"""
    if len(sys.argv) == 1:
        # No arguments - run all examples (default behavior)
        run_paper_example()
        run_custom_examples()
    elif len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h']:
            print(__doc__)
            return
            
        elif arg == '--paper':
            run_paper_example()
            
        elif arg == '--simple':
            # Run just the simple 2-task example
            print("=" * 50)
            print("SIMPLE 2-TASK EXAMPLE")
            print("=" * 50)
            
            simple_tasks = [
                Task(task_id=1, execution_time=1, period=4, task_type=TaskType.ASAP),
                Task(task_id=2, execution_time=1, period=6, task_type=TaskType.ALAP)
            ]
            
            print("Tasks: T1(1,4,ASAP), T2(1,6,ALAP)")
            porms = PORMSScheduler(simple_tasks)
            print_task_info(simple_tasks, "PORMS")
            schedule = porms.simulate(12)
            print_schedule(schedule, "PORMS")
            
            print(f"\nObservation: T2 (ALAP) has promotion time = {simple_tasks[1].promotion_time}")
            print("This means T2 waits in delay queue before becoming ready")
            
        elif arg == '--custom':
            # Run just the custom task set
            print("=" * 50)
            print("CUSTOM TASK SET EXAMPLE")
            print("=" * 50)
            
            custom_tasks = [
                Task(task_id=1, execution_time=2, period=8, task_type=TaskType.ASAP),
                Task(task_id=2, execution_time=1, period=4, task_type=TaskType.ASAP),
                Task(task_id=3, execution_time=3, period=12, task_type=TaskType.ALAP),
                Task(task_id=4, execution_time=1, period=6, task_type=TaskType.ALAP)
            ]
            
            print("Tasks: T1(2,8,ASAP), T2(1,4,ASAP), T3(3,12,ALAP), T4(1,6,ALAP)")
            
            porms_custom = PORMSScheduler([Task(t.task_id, t.execution_time, t.period, t.task_type) for t in custom_tasks])
            poppa_custom = POPPAScheduler([Task(t.task_id, t.execution_time, t.period, t.task_type) for t in custom_tasks])
            
            print_task_info(porms_custom.tasks, "PORMS")
            porms_schedule = porms_custom.simulate(16)
            print_schedule(porms_schedule, "PORMS")
            
            print_task_info(poppa_custom.tasks, "POPPA")
            poppa_schedule = poppa_custom.simulate(16)
            print_schedule(poppa_schedule, "POPPA")
            
        elif arg == '--mixed':
            run_mixed_preferences_test()
            
        elif arg == '--all-asap':
            run_all_asap_test()
            
        elif arg == '--all-alap':
            run_all_alap_test()
            
        elif arg == '--performance':
            run_performance_test()
            
if __name__ == "__main__":
    main()