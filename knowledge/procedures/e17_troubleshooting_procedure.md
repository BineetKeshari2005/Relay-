# [FICTIONAL DEMO DATA] Standard Operating Procedure: Fault E17 Troubleshooting
## Document ID: SOP-ACX420-E17
**Model Scope**: CoolCore ACX-420 Series  
**Target Subsystem**: Refrigeration Circuit & Condenser Air Management  
**Safety Classification**: High-Pressure Hazard (Mandatory PPE & LOTO)

> **NOTICE**: Completely fictional demo SOP for Relay testing.

---

### 1. Alarm Definition
Fault **E17** is triggered when discharge pressure sensor PT-1 senses pressure exceeding 210 PSI (demo value) continuously for 5 seconds, or if the electro-mechanical high-pressure safety switch trips at 220 PSI.

### 2. Common Root Causes
1. **Condenser Airflow Restriction**:
   - Debris, leaves, or cottonwood clogging condenser fins.
   - Condenser fan motor failure or loose fan belt.
   - Recirculation of hot discharge air due to architectural wind baffles.
2. **Refrigerant Overcharge**:
   - Recent unverified field service adding excess refrigerant.
3. **Sensor Drift / Transducer Fault**:
   - Pressure sensor PT-1 reporting artificial high voltage offset.
4. **Non-Condensables**:
   - Air or moisture trapped in refrigeration circuit.

### 3. Step-by-Step Action Plan

#### Step 1: Safe Shutdown Verification
- Prior to inspecting condenser fan deck, switch the unit disconnect switch to the OFF position.
- Confirm 0V across line terminals using a rated multimeter.

#### Step 2: Visual Inspection of Condenser
- Inspect outer and inner condenser coil surfaces for biological fouling, dust mats, or bent fins.
- Inspect condenser fan blades for cracking or mechanical binding.

#### Step 3: Mechanical vs Electrical Gauge Verification
- Connect calibrated external analog refrigerant manifold gauges to the discharge service port.
- Compare external gauge reading against the onboard digital telemetry reading.
- If onboard sensor reads 195+ PSI while manual gauge reads 165 PSI: **Transducer drift is diagnosed**.
- If external gauge confirms elevated pressure (>190 PSI): **Proceed to airflow and coil thermal delta testing**.

#### Step 4: Branching Decision Logic
- **If coil is dirty**: Clean coil using low-pressure alkaline detergent wash (Do not use pressure washer).
- **If fan motor is inoperative**: Test motor capacitor and 3-phase winding resistance.
- **If pressure remains high after airflow verification**: Evacuate circuit and recover refrigerant to verify charge weight.
