# Hardware Wiring Guide

This document describes the connection between the Raspberry Pi and the 8-channel relay board used in the UltraFiltration Control System.

## Component List
- **Raspberry Pi** (3B+ or 4 recommended)
- **8-Channel Relay Board** (Active LOW)
- **Power Supply** (5V DC for Pi and Relays)

## Wiring Diagram

### Raspberry Pi to Relay Board Connection
The following table shows the GPIO pin mapping (BCM numbering) and the corresponding relay channel.

| Device | Type | BCM Pin | Relay Channel |
| :--- | :--- | :--- | :--- |
| **Valve 1** | Digital Out | GPIO 27 | IN 1 |
| **Valve 2** | Digital Out | GPIO 3 | IN 2 |
| **Valve 3** | Digital Out | GPIO 22 | IN 3 |
| **Valve 4** | Digital Out | GPIO 18 | IN 4 |
| **Valve 5** | Digital Out | GPIO 23 | IN 5 |
| **Pump 1**  | Digital Out | GPIO 24 | IN 6 |
| **Pump 2**  | Digital Out | GPIO 25 | IN 7 |
| **Common GND** | Power | Ground | GND |
| **Relay VCC** | Power | 5V | VCC |

### Logical Flow Diagram

```mermaid
graph TD
    subgraph Raspberry Pi
        G27[GPIO 27]
        G3[GPIO 3]
        G22[GPIO 22]
        G18[GPIO 18]
        G23[GPIO 23]
        G24[GPIO 24]
        G25[GPIO 25]
    end

    subgraph 8-Channel Relay Board
        R1[Relay 1: Valve 1]
        R2[Relay 2: Valve 2]
        R3[Relay 3: Valve 3]
        R4[Relay 4: Valve 4]
        R5[Relay 5: Valve 5]
        R6[Relay 6: Pump 1]
        R7[Relay 7: Pump 2]
    end

    G27 --> R1
    G3 --> R2
    G22 --> R3
    G18 --> R4
    G23 --> R5
    G24 --> R6
    G25 --> R7
```

## Power Considerations
- The 8-channel relay board typically requires a separate 5V supply if many relays are active simultaneously.
- Ensure the JD-VCC jumper is correctly configured for your power setup.
- **DANGER:** High voltage (110V/220V) should only be handled by qualified personnel. Ensure all connections are insulated.
