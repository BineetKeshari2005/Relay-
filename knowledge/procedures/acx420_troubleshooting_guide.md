# [FICTIONAL DEMO DATA] CoolCore ACX-420 Troubleshooting Guide

> **NOTICE**: This document is completely fictional and generated solely for the Relay demonstration sandbox. Do not apply these instructions to real-world equipment.

## Diagnostic Alarm Table

| Fault Code | Alarm Name | Description | Default Auto-Reset | Immediate Action |
|------------|------------|-------------|--------------------|------------------|
| **E01** | Phase Imbalance | Phase voltage disparity > 3% | No (Manual Lockout) | Check 3-phase line supply |
| **E08** | Low Suction Pressure | Suction drops below 45 PSI for >90s | Yes (Up to 3 times/hr) | Inspect evaporator filters and TXV |
| **E17** | High-Pressure Protection | Discharge pressure exceeds 210 PSI | No (Requires Manual Reset) | Inspect condenser fan & airflow |
| **E22** | Inverter Overheat | Variable speed drive heatsink > 85°C | Yes after cooldown | Inspect VFD cooling fan |
| **E35** | Communication Loss | DDC board loss of communication | Yes | Verify RS-485 bus termination |

## Preliminary Diagnostic Protocol
1. **Safety First**: Verify all disconnects before removing cabinet panels.
2. **Read Current Alarm State**: Record active error code and timestamp from the DDC controller.
3. **Verify Sensor Health**: Use an analog multimeter to verify DC voltage from transducers before assuming mechanical failure.
4. **Log Historical Events**: Cross-reference with equipment service records to see if intermittent faults preceded this lockout.
