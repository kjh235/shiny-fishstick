# shiny-fishstick
Markov Decision Process for Consolidated Parcel Container Priority

A Markov Decision Process and Simulation Framework for Optimizing Container Unloading Priority
Optimizing Unload Sequences for On-Time Shipment Delivery Across Single and Multiple Doors
Executive Summary

In high-velocity logistics operations, unloading containers efficiently and in the correct sequence is critical to ensuring shipments meet downstream departure and delivery deadlines. When each container holds hundreds or thousands of shipments—each with unique due times and processing requirements—the complexity increases dramatically.

This whitepaper presents a scalable analytical framework using:

A Markov Decision Process (MDP) for formal decision modeling
Shipment-level probability functions aggregated into container value curves
A design for N parallel unload servers (doors)
A priority-based simulation engine for evaluating policies
Implementable formulas and Python-style pseudocode

This approach provides operational insight and supports data-driven decision strategies for optimizing unload priority with the objective of maximizing on-time performance or minimizing lateness.

1. Problem Context

A facility receives inbound containers. Each container:

Requires unloading time (random or deterministic)
Contains a large number of shipments (e.g., 1,000 per container)
Each shipment has its own:
Due time (linehaul departure, service commitment)
Post-unload processing time

The operational goal is to determine which container(s) to unload next to maximize the probability all—or as many as possible—shipments depart on time.

The challenging constraints include:

Only N unload doors available in parallel
Time-dependent inter-arrival of outbound departures
Uncertain unload and processing times
Nonlinear penalty when high-priority freight is late
2. Markov Decision Process Formulation

We model unloading as an event-based MDP.

2.1 State Representation

For N unload doors, the system state at decision epoch t is:

s=(t,R,B)

Where:

t — current time
R — set of containers not yet started
B — set of active unload jobs, each with:
Door ID k
Container ID i
k
	​

Expected finish time F
i
k
	​

	​


Example busy-state element:

B={(k,i
k
	​

,F
i
k
	​

	​

)∣k∈{1,…,N}}
2.2 Decision Epochs

A decision epoch occurs whenever one or more doors complete unloading:

t
′
=
(k,i
k
	​

,F
i
k
	​

	​

)∈B
min
	​

F
i
k
	​

	​


All doors that finish at t=t
′
 become idle and must be assigned new containers.

2.3 Actions

At epoch t:

Let K
idle
	​

 be idle doors.
Action a assigns up to ∣K
idle
	​

∣ containers from R into those doors:
a={(k,i
k
	​

):k∈K
idle
	​

,i
k
	​

∈R}
2.4 Transitions

For each assigned container i:

Sample unload duration U
i
	​

Set finish time F
i
	​

=t+U
i
	​

Update state:
Remove i from R
Add (k,i,F
i
	​

) to busy set B
2.5 Rewards

Reward is earned when a container finishes unloading:

r
i
	​

=f
i
	​

(t
start,i
	​

)

Where f
i
	​

(⋅) is the container time–value curve derived in Section 3.

Total cumulative reward:

i=1
∑
M
	​

f
i
	​

(t
start,i
	​

)

This may represent:

Expected number of on-time shipments
Weighted on-time shipments
Negative lateness penalty
Probability all shipments are on time
3. Shipment-Level Time–Value Function

Each container is evaluated using shipment-level micro-models aggregated into a single curve f
i
	​

(t).

3.1 Shipment Completion Time Model

For shipment j in container i:

C
ij
	​

(t)=t+U
i
	​

+P
ij
	​


Where:

t — container start time
U
i
	​

 — unload time
P
ij
	​

 — post-unload processing time
3.2 Stochastic Modeling (Normal Approximation)

Assume:

U
i
	​

∼N(μ
U
i
	​

	​

,σ
U
i
	​

2
	​

)
P
ij
	​

∼N(μ
P
ij
	​

	​

,σ
P
ij
	​

2
	​

)

Then:

X
ij
	​

=U
i
	​

+P
ij
	​

∼N(μ
ij
	​

,σ
ij
2
	​

)

with:

μ
ij
	​

=μ
U
i
	​

	​

+μ
P
ij
	​

	​

,σ
ij
	​

=
σ
U
i
	​

2
	​

+σ
P
ij
	​

2
	​

	​


Probability shipment j makes its deadline D
ij
	​

:

p
ij
	​

(t)=Φ(
σ
ij
	​

D
ij
	​

−t−μ
ij
	​

	​

)

Where Φ(⋅) is the standard Normal CDF.

3.3 Container Time–Value Curve

If each shipment has weight w
ij
	​

:

f
i
	​

(t)=
j=1
∑
n
i
	​

	​

w
ij
	​

p
ij
	​

(t)

Properties:

f
i
	​

(t) is monotonically decreasing in t
Encodes full shipment-level urgency
Is computationally cheap to evaluate
4. Extension to N Parallel Unload Doors

With multiple doors:

States track all active unloads
Decision epoch triggers on earliest finishing unload
Multiple doors may finish simultaneously
Priority-based assignment applied to each idle door

The MDP structure remains identical, with the only expansion being:

Larger busy set B
Multi-container action selection

This makes the framework scalable to large operations (e.g., 20–50 doors).

5. Priority-Based Scheduling Policy

Exact dynamic programming over this MDP is intractable due to:

Large state space (2
20
 subsets × continuous time × N doors)
Shipment-level interactions

Instead, we deploy a myopic value-based policy, which is a practical form of approximate dynamic programming:

Policy:

Whenever a door becomes idle at time t:

Compute f
i
	​

(t) for each unstarted container i.
Rank containers by f
i
	​

(t).
Assign the top ranked container(s) to all idle doors.

This exploits:

Shipment-level urgency
Parallelism
Time-sensitivity of freight

and performs well in practice.

6. Pseudo-Code Implementation

Below is implementable Python-style pseudo-code for the end-to-end simulator.

6.1 Container Value Function
import math

def normal_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))

def container_value(container, t_now):
    mu_u  = container.unload_mean
    sig_u = container.unload_std

    total = 0.0
    for s in container.shipments:
        mu_p  = s.proc_mean
        sig_p = s.proc_std
        w     = getattr(s, "weight", 1.0)

        mu_x  = mu_u + mu_p
        sig_x = math.sqrt(sig_u**2 + sig_p**2)

        z = (s.due_time - t_now - mu_x) / sig_x
        p_on_time = normal_cdf(z)
        total += w * p_on_time

    return total
6.2 Event-Driven Simulation Framework
def simulate_unload_schedule(containers, N_doors, t_start=0):
    t = t_start
    unstarted = {c.id for c in containers}
    container_by_id = {c.id: c for c in containers}
    in_progress = []
    completed = {}
    total_value = 0.0

    doors = list(range(N_doors))
    assign_new_containers(t, doors, unstarted, in_progress, container_by_id)

    while in_progress or unstarted:
        if in_progress:
            t_event = min(job["t_finish"] for job in in_progress)
        else:
            t_event = t  # Assign immediately if idle but containers remain

        t = t_event

        finished = [job for job in in_progress if job["t_finish"] <= t]
        in_progress = [job for job in in_progress if job["t_finish"] > t]

        freed_doors = []
        for job in finished:
            cid = job["cid"]
            door_id = job["door_id"]
            t_start_c = job["t_start"]

            container = container_by_id[cid]
            v = container_value(container, t_start_c)
            total_value += v

            completed[cid] = {
                "door_id": door_id,
                "t_start": t_start_c,
                "t_finish": job["t_finish"],
                "value": v,
            }

            freed_doors.append(door_id)

        assign_new_containers(t, freed_doors, unstarted, in_progress, container_by_id)

    return total_value, completed
6.3 Assign Containers to Idle Doors via Priority Index
import random

def draw_unload_time(container):
    u = random.gauss(container.unload_mean, container.unload_std)
    return max(u, 0.01)

def assign_new_containers(t_now, idle_doors, unstarted, in_progress, container_by_id):
    if not idle_doors or not unstarted:
        return

    scores = []
    for cid in unstarted:
        c = container_by_id[cid]
        s = container_value(c, t_now)
        scores.append((s, cid))

    scores.sort(reverse=True)

    num_assign = min(len(idle_doors), len(scores))
    for k in range(num_assign):
        door_id = idle_doors[k]
        _, cid = scores[k]

        unstarted.remove(cid)

        u = draw_unload_time(container_by_id[cid])
        t_finish = t_now + u

        in_progress.append({
            "door_id": door_id,
            "cid": cid,
            "t_start": t_now,
            "t_finish": t_finish,
        })
7. Operational Interpretation
What This Framework Enables
Prioritization that reflects shipment urgency, not just container attributes
Ability to simulate dozens of policies (EDD, minimum slack, probabilistic, hybrid)
Quantification of expected on-time performance under different scenarios
Ability to scale to tens of doors and thousands of shipments
Where This Is Useful
Hub unload sequencing
Crossdock optimization
Containerized import unload planning
Sort planning & departure protection
Workforce allocation for unloading
