# scheduler.py — Core DVFS + Thermal-Aware Scheduling Logic
# Core scheduling logic implementation
class LoadPredictor:
    def __init__(self):
        self.history = []

    def update(self, load):
        self.history.append(load)
        if len(self.history) > 5:
            self.history.pop(0)

    def predict(self):
        if len(self.history) < 3:
            return self.history[-1] if self.history else 0
        return sum(self.history) / len(self.history)
class Process:
    def __init__(self, pid, name, burst_time, priority, base_power):
        self.pid = pid
        self.name = name
        self.burst_time = burst_time
        self.priority = priority        # 'high', 'med', 'low'
        self.base_power = base_power    # Watts at max frequency
        self.remaining = burst_time
        self.finish_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        

# Thermal model to control CPU temperature
class ThermalModel:
    def __init__(self, cores=4, ambient=35.0, limit=80.0):
        self.cores = cores
        self.temps = [ambient] * cores
        self.ambient = ambient
        self.limit = limit
        self.history = {i: [] for i in range(cores)}

    def update(self, core_id, power_watts, time_ms=4):
        R = 5.0
        C = 0.8
        delta = (power_watts * R - (self.temps[core_id] - self.ambient)) * (time_ms / 1000) / C
        self.temps[core_id] = round(self.temps[core_id] + delta, 1)
        self.history[core_id].append(self.temps[core_id])

    def is_throttling(self, core_id):
        return self.temps[core_id] >= self.limit

    def get_coolest_core(self):
        return min(range(self.cores), key=lambda c: self.temps[c])

    def report(self):
        return {f'core_{i}': self.temps[i] for i in range(self.cores)}
    

# Dynamic Voltage and Frequency Scaling based on CPU load
class DVFSScheduler:
    FREQ_LEVELS = {
        'high': (2.4, 1.00),
        'med':  (1.8, 0.80),
        'low':  (1.2, 0.65),
    }
    

    def __init__(self, thermal_limit=80):
        self.thermal = ThermalModel(limit=thermal_limit)
        self.time = 0
        self.log = []
        self.predictor = LoadPredictor()
        self.proactive_throttles = 0

    def schedule(self, processes, algorithm='dvfs'):
        results = []
        gantt = []
        queue = [Process(p['pid'], p['name'], p['burst'],
                         p['priority'], p['power']) for p in processes]

        quantum = 4
        current_time = 0

        while queue:
            current_load = sum(p.remaining for p in queue) if queue else 0
            self.predictor.update(current_load)
            predicted_load = self.predictor.predict()
            proc = queue.pop(0)
            if predicted_load > 20:
                freq, v_scale = self.FREQ_LEVELS['high']
            elif predicted_load > 10:
                freq, v_scale = self.FREQ_LEVELS['med']
            else:
                 freq, v_scale = self.FREQ_LEVELS['low']

            # Thermal-aware: pick core and check throttle
            core_id = current_time % 4
            if self.thermal.temps[core_id] > (self.thermal.limit - 5):
                freq, v_scale = self.FREQ_LEVELS['low']
                self.proactive_throttles += 1
                self.log.append(f"[AI] Proactive throttling on Core {core_id}")
            if algorithm in ('thermal', 'edf') and self.thermal.is_throttling(core_id):
                core_id = self.thermal.get_coolest_core()
                self.log.append(f"[THERMAL] {proc.name} migrated to Core {core_id}")

            # DVFS power: P ∝ C × V² × f  (simplified)
            if algorithm == 'rr':
                actual_power = proc.base_power
                freq = 2.4
            elif algorithm == 'edf':
                actual_power = proc.base_power * (v_scale ** 2) * (freq / 2.4) * 0.9
            else:
                actual_power = proc.base_power * (v_scale ** 2) * (freq / 2.4)

            exec_time = min(proc.remaining, quantum)
            proc.remaining -= exec_time
            current_time += exec_time

            self.thermal.update(core_id, actual_power, exec_time)

            energy = round(actual_power * exec_time, 2)
            gantt.append({
                'pid': proc.pid,
                'name': proc.name,
                'core': core_id,
                'start': current_time - exec_time,
                'end': current_time,
                'power': round(actual_power, 2),
                'freq': freq,
                'energy': energy,
                'priority': proc.priority,
            })

            if proc.remaining > 0:
                queue.append(proc)
            else:
                proc.finish_time = current_time
                self.log.append(f"[DONE] {proc.name} finished at t={current_time}ms, power={round(actual_power,2)}W")

        total_energy = sum(g['energy'] for g in gantt)
        makespan = max(g['end'] for g in gantt)
        avg_power = round(total_energy / makespan, 2) if makespan else 0

        # Baseline (standard RR) power for comparison
        baseline_power = sum(p['power'] for p in processes)
        savings = round(((baseline_power - avg_power) / baseline_power) * 100, 1) if baseline_power else 0

        return {
            'gantt': gantt,
            'thermal': self.thermal.report(),
            'thermal_history': self.thermal.history,
            'log': self.log,
            # Energy and performance metrics calculation
            'metrics': {
                'proactive_throttles': self.proactive_throttles,
                'predicted_load': round(predicted_load, 2),
                'total_energy': round(total_energy, 2),
                'avg_power': avg_power,
                'baseline_power': round(baseline_power, 2),
                'energy_savings': max(0, savings),
                'makespan': makespan,
                'avg_freq': round(sum(g['freq'] for g in gantt) / len(gantt), 2),
                'peak_temp': round(max(self.thermal.temps), 1),
            }
        }