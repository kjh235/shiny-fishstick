import math
import random
from typing import List, Dict, Tuple


# =========================
# Data Model
# =========================

class Shipment:
    """
    Represents a single shipment inside a container.
    """
    def __init__(self, due_time: float, proc_mean: float, proc_std: float, weight: float = 1.0):
        self.due_time = due_time      # deadline (same units as time, e.g., minutes)
        self.proc_mean = proc_mean    # mean of post-unload processing time
        self.proc_std = proc_std      # std dev of post-unload processing time
        self.weight = weight          # importance weight (default 1.0)


class Container:
    """
    Represents a container to be unloaded.

    Attributes:
    - id: unique container ID
    - unload_mean, unload_std: parameters for unload time distribution
    - shipments: list[Shipment]
    """
    def __init__(self, cid: int, unload_mean: float, unload_std: float, shipments: List[Shipment]):
        self.id = cid
        self.unload_mean = unload_mean
        self.unload_std = unload_std
        self.shipments = shipments


# =========================
# Core Math Helpers
# =========================

def normal_cdf(z: float) -> float:
    """
    Standard normal CDF Φ(z) using the error function.
    """
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def container_value(container: Container, t_now: float) -> float:
    """
    Compute the expected (weighted) number of on-time shipments in this container
    IF the container starts unloading at time t_now.

    Uses a Normal approximation for:
      X_ij = U_i + P_ij

    where:
      U_i  ~ N(unload_mean, unload_std^2)
      P_ij ~ N(proc_mean, proc_std^2)

    So:
      X_ij ~ N(mu_x, sig_x^2)
      p_on_time = P(X_ij <= D_ij - t_now) = Φ((D_ij - t_now - mu_x) / sig_x)
    """
    mu_u  = container.unload_mean
    sig_u = container.unload_std

    total = 0.0
    for s in container.shipments:
        mu_p  = s.proc_mean
        sig_p = s.proc_std
        w     = s.weight

        mu_x  = mu_u + mu_p
        sig_x = math.sqrt(sig_u ** 2 + sig_p ** 2)

        # Remaining time budget from start to due
        z = (s.due_time - t_now - mu_x) / sig_x
        p_on_time = normal_cdf(z)

        total += w * p_on_time

    return total


# =========================
# Simulation Components
# =========================

def draw_unload_time(container: Container) -> float:
    """
    Draw an unload time for a container.
    Default: Normal with truncation at a small positive number.
    """
    u = random.gauss(container.unload_mean, container.unload_std)
    return max(u, 0.01)


def assign_new_containers(
    t_now: float,
    idle_doors: List[int],
    unstarted: set,
    in_progress: List[Dict],
    container_by_id: Dict[int, Container]
) -> None:
    """
    Assign containers to idle doors at time t_now based on priority.

    Priority policy:
      - For each unstarted container i, compute value f_i(t_now) = container_value(...)
      - Sort descending by f_i(t_now)
      - Assign the highest-value containers to idle doors
    """
    if not idle_doors or not unstarted:
        return

    # Compute priority index for each unstarted container
    scores: List[Tuple[float, int]] = []
    for cid in unstarted:
        container = container_by_id[cid]
        score = container_value(container, t_now)
        scores.append((score, cid))

    # Sort descending by score
    scores.sort(key=lambda x: x[0], reverse=True)

    num_to_assign = min(len(idle_doors), len(scores))

    for k in range(num_to_assign):
        door_id = idle_doors[k]
        _, cid = scores[k]

        # Remove from unstarted set
        unstarted.remove(cid)

        container = container_by_id[cid]
        u = draw_unload_time(container)
        t_finish = t_now + u

        in_progress.append({
            "door_id": door_id,
            "cid": cid,
            "t_start": t_now,
            "t_finish": t_finish,
        })


def simulate_unload_schedule(
    containers: List[Container],
    N_doors: int,
    t_start: float = 0.0,
    verbose: bool = False
) -> Tuple[float, Dict[int, Dict]]:
    """
    Event-based simulation of unloading schedule with N doors.

    Returns:
      total_value: sum of container_value(container, t_start_container) over all containers
      completed:   dict[cid] -> info about completion times and value
    """
    t = t_start

    # Set of unstarted containers (by id)
    unstarted = {c.id for c in containers}

    # Quick lookup
    container_by_id: Dict[int, Container] = {c.id: c for c in containers}

    # Jobs currently being unloaded
    in_progress: List[Dict] = []

    # Completed info
    completed: Dict[int, Dict] = {}
    total_value: float = 0.0

    # Doors 0..N_doors-1
    doors = list(range(N_doors))

    # Initial assignment
    assign_new_containers(t, doors, unstarted, in_progress, container_by_id)

    # Event loop
    while in_progress or unstarted:
        if in_progress:
            # Next completion time
            t_event = min(job["t_finish"] for job in in_progress)
        else:
            # No active jobs but unstarted containers remain; start immediately
            t_event = t

        # Advance time
        t = t_event

        # Jobs that finished at t
        finished = [job for job in in_progress if job["t_finish"] <= t + 1e-9]
        # Jobs still in progress
        in_progress = [job for job in in_progress if job["t_finish"] > t + 1e-9]

        freed_doors: List[int] = []

        for job in finished:
            cid = job["cid"]
            door_id = job["door_id"]
            t_start_c = job["t_start"]
            t_finish_c = job["t_finish"]

            container = container_by_id[cid]
            v = container_value(container, t_start_c)
            total_value += v

            completed[cid] = {
                "door_id": door_id,
                "t_start": t_start_c,
                "t_finish": t_finish_c,
                "value": v,
            }

            freed_doors.append(door_id)

            if verbose:
                print(
                    f"Time {t:6.2f}: Container {cid} finished on door {door_id} "
                    f"(start {t_start_c:.2f}, finish {t_finish_c:.2f}, value {v:.2f})"
                )

        # Assign new containers to freed doors
        assign_new_containers(t, freed_doors, unstarted, in_progress, container_by_id)

    return total_value, completed


# =========================
# Example Scenario / Main
# =========================

def build_example_containers(
    num_containers: int = 10,
    shipments_per_container: int = 200
) -> List[Container]:
    """
    Build a synthetic test scenario with num_containers.
    Each container has 'shipments_per_container' shipments with:
      - due times spread over a horizon
      - random processing means/variances
    """
    containers: List[Container] = []

    # global horizon for due times (e.g., minutes)
    # we assume unload + processing is on the order of 60-120 minutes
    base_due = 300.0  # base around which shipment due times are distributed

    for cid in range(1, num_containers + 1):
        shipments: List[Shipment] = []

        for j in range(shipments_per_container):
            # Spread due times a bit: some tighter, some looser
            due_time = base_due + random.randint(-60, 60)

            # Processing time parameters (post-unload)
            proc_mean = random.uniform(15, 30)  # minutes
            proc_std = random.uniform(3, 8)

            s = Shipment(
                due_time=due_time,
                proc_mean=proc_mean,
                proc_std=proc_std,
                weight=1.0
            )
            shipments.append(s)

        # Unload time parameters for this container
        unload_mean = random.uniform(40, 70)   # mean unload time
        unload_std  = random.uniform(5, 15)    # std dev

        c = Container(
            cid=cid,
            unload_mean=unload_mean,
            unload_std=unload_std,
            shipments=shipments
        )
        containers.append(c)

    return containers


if __name__ == "__main__":
    random.seed(42)  # for reproducibility

    # Build synthetic containers
    containers = build_example_containers(
        num_containers=10,
        shipments_per_container=200
    )

    # Number of unload doors
    N_DOORS = 3

    print(f"Simulating {len(containers)} containers, {N_DOORS} doors...")

    total_value, completed = simulate_unload_schedule(
        containers,
        N_doors=N_DOORS,
        t_start=0.0,
        verbose=True
    )

    print("\n========== SUMMARY ==========")
    print(f"Total value (sum of expected on-time shipments across containers): {total_value:.2f}")
    print(f"Containers completed: {len(completed)}")

    # Optionally show a few container stats
    for cid in sorted(completed.keys())[:5]:
        info = completed[cid]
        print(
            f"Container {cid}: door {info['door_id']}, "
            f"start {info['t_start']:.2f}, finish {info['t_finish']:.2f}, "
            f"value {info['value']:.2f}"
        )
