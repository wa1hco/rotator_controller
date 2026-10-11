# ADR 0006: Headless, with a minimal front panel

- Status: Accepted
- Date: 2026-10-11

## Context

The system overview treats the display as a module that can grow, and
lists a numeric display as a possible default. For this controller the
choice is narrower: the box is operated from a PC or over Ethernet.

## Decision

The controller is headless. There is no LCD, OLED, or knob. The front
panel has STOP, CW, and CCW, plus status LEDs. Heading, calibration, and
setup are done from the host.

## Consequences

Protocol handling and a host UI matter more than a menu system. The
front-panel buttons are direct motion inputs, with STOP highest priority.
A display can be added later as a front end. It is not in the baseline
enclosure.
